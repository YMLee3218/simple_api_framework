from contextlib import contextmanager
from functools import lru_cache, wraps
from inspect import Parameter, signature
from itertools import groupby, islice
from typing import (Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Set, Text, Tuple, Type,
                    get_origin, get_type_hints)

from json_data.json_format import JsonFormat, JsonObject
from logger import get_logger
from switch_dispatch import switch_dispatch

_logger = get_logger(__name__)

_serializing_option_property_name: Text = '__serializing_option__'


class _SerializingOption(NamedTuple):
    checks_validation: bool = True
    includes_none: bool = True


def _check_valid(original: Any) -> Callable:
    @wraps(original)
    def wrapper(annotation: Any, data: Any, *args, **kwargs) -> Any:
        try:
            deserialized: Any = original(annotation, data, *args, **kwargs)
        except (DeserializingFailError, InvalidAnnotationError) as e:
            raise e
        except Exception as e:
            raise DeserializingFailError(annotation, data).with_traceback(e.__traceback__) from e

        if isinstance(annotation, type) and not _is_matched_annotation(deserialized, annotation):
            raise InvalidAnnotationError(annotation, deserialized)

        return deserialized
    wrapper.register = original.register
    return wrapper


def _is_matched_annotation(data: Any, annotation: Any) -> bool:
    if isinstance(data, annotation):
        return True

    if isinstance(data, list):
        return len(data) <= 0 or isinstance(data[0], annotation)

    return False


def _compare_annotation(x: Any, y: Any) -> bool:
    x_origin: Any = get_origin(x) or x
    y_origin: Any = get_origin(y) or y
    return x_origin == y_origin


@_check_valid
@switch_dispatch(False, _compare_annotation)
def from_data_to(annotation: Any, data: JsonFormat, *,
                 checks_validation: bool = True, includes_none: bool = True) -> Any:
    cls_option: _SerializingOption = getattr(annotation, _serializing_option_property_name, _SerializingOption())
    checks_validation = checks_validation and cls_option.checks_validation
    includes_none = includes_none and cls_option.includes_none
    local_variables: Dict[Text, Any] = locals()
    options: Dict[Text, bool] = {name: local_variables[name] for name in _get_kwargs_names(from_data_to)}
    if isinstance(data, List):
        return from_data_to(List[annotation], data, **options)

    annotations: Dict[Text, Any] = _get_cached_type_hints(annotation)
    deserialized_data: JsonObject = {name: from_data_to(annotations[name], value, **options)
                                     for name, value in data.items() if name in annotations}

    grouped_arguments = groupby(deserialized_data.items(), key=(lambda item: _is_in_init(annotation, item[0])))
    arguments: Dict[bool, JsonObject] = {is_in_init: dict(arguments) for is_in_init, arguments in grouped_arguments}

    init_arguments: JsonObject = arguments.get(True, {})
    supplemented_init_arguments: JsonObject = _get_supplemented_init_arguments(init_arguments, annotation)

    left_arguments: JsonObject = arguments.get(False, {})
    curtailed_left_arguments: JsonObject = _get_curtailed_left_arguments(left_arguments, annotation)

    def swap_for_named_tuple():
        nonlocal supplemented_init_arguments, curtailed_left_arguments
        supplemented_init_arguments, curtailed_left_arguments = curtailed_left_arguments, supplemented_init_arguments

    with _process_back_and_forth(annotation, swap_for_named_tuple, swap_for_named_tuple):
        instance: annotation = annotation(**supplemented_init_arguments)
        for name, value in curtailed_left_arguments.items():
            setattr(instance, name, value)

    missed_arguments_names: Optional[List[Text]] = (_get_missed_arguments_names(instance, annotation)
                                                    if includes_none else None)
    for name in missed_arguments_names or []:
        setattr(instance, name, None)

    if checks_validation:
        missed_arguments_names = missed_arguments_names or _get_missed_arguments_names(instance, annotation)
        added_init_arguments_names: List[Text] = list(supplemented_init_arguments.keys() - init_arguments.keys())
        dumped_arguments_names: List[Text] = list(left_arguments.keys() - curtailed_left_arguments.keys())
        _print_validation_warning(missed_arguments_names + added_init_arguments_names, dumped_arguments_names)

    return instance


@lru_cache(1)
def _get_kwargs_names(func: Callable) -> List[Text]:
    return [name for name, parameter in signature(func).parameters.items() if parameter.kind is Parameter.KEYWORD_ONLY]


@lru_cache
def _get_cached_type_hints(cls: Type) -> Dict[Text, Any]:
    return get_type_hints(cls)


def _is_in_init(cls: Type, parameter_name: Text) -> bool:
    valid_init_parameters: Dict[Text, Parameter] = _get_valid_init_parameters(cls)
    return parameter_name in valid_init_parameters


_ignore_parameter_kind: Set = {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}


@lru_cache
def _get_valid_init_parameters(cls: Type) -> Dict[Text, Parameter]:
    sliced_parameters: List[Tuple[Text, Parameter]] = list(islice(signature(cls.__init__).parameters.items(), 1, None))
    return {name: parameter for name, parameter in sliced_parameters
            if parameter.kind not in _ignore_parameter_kind}


def _get_supplemented_init_arguments(init_arguments: JsonObject, cls: Type) -> JsonObject:
    init_parameters: Mapping[Text, Parameter] = _get_valid_init_parameters(cls)
    return {name: init_arguments[name] if name in init_arguments else None
            for name, parameter in init_parameters.items()
            if name in init_arguments or parameter.default == Parameter.empty}


def _get_curtailed_left_arguments(left_arguments: JsonObject, cls: Type) -> JsonObject:
    annotations: Dict[Text, Any] = _get_cached_type_hints(cls)
    return {name: value for name, value in left_arguments.items() if name in annotations}


def _get_missed_arguments_names(created_object: Any, cls: Type) -> List[Text]:
    annotations: Dict[Text, Any] = _get_cached_type_hints(cls)
    missed_arguments_names: List[Text] = []
    for name in annotations:
        try:
            getattr(created_object, name)
        except AttributeError:
            missed_arguments_names.append(name)

    return missed_arguments_names


@contextmanager
def _process_back_and_forth(cls: Type, prev_process: Callable[[], Any], next_process: Callable[[], Any]):
    is_named_tuple: bool = issubclass(cls, tuple)
    if is_named_tuple:
        prev_process()
    yield
    if is_named_tuple:
        next_process()


def _print_validation_warning(missed_arguments_name: List[Text], dumped_arguments_name: List[Text]):
    if 0 < len(missed_arguments_name):
        _print_warning("Missed variables in data", missed_arguments_name)

    if 0 < len(dumped_arguments_name):
        _print_warning("Unused variables in data", dumped_arguments_name)


def _print_warning(message: Text, variables: Iterable[Text]):
    _logger.warning(f"{message}: {', '.join(variables)}")


def serializing_option(*, checks_validation: bool = True, includes_none: bool = True) -> Callable[[Type], Type]:
    def wrapper(cls: Type) -> Type:
        setattr(cls, _serializing_option_property_name, _SerializingOption(checks_validation=checks_validation,
                                                                           includes_none=includes_none))
        return cls
    return wrapper


class DeserializingFailError(Exception):
    def __init__(self, annotation: Any, data: Any):
        self.message: Text = f"Fail to deserialize '{data}: {type(data).__name__}' to '{annotation}'."

    def __str__(self) -> Text:
        return self.message


class InvalidAnnotationError(TypeError):
    def __init__(self, annotation: Any, data: Any):
        self.message: Text = f"'{annotation}' and '{data}: {type(data).__name__}' do not match."

    def __str__(self) -> Text:
        return self.message
