from functools import singledispatch, wraps
from inspect import Parameter, signature
from types import FunctionType
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Text, Tuple


class Case(NamedTuple):
    value: Any
    func: Callable
    separate_comparator: Optional[Callable[[Any], bool]]


@singledispatch
def switch_dispatch(allow_overwrite: bool = False, comparator: Callable[[Any, Any], bool] = None) -> Callable:
    return lambda func: _(func, allow_overwrite, comparator)


@switch_dispatch.register(FunctionType)
def _(func: Callable, allow_overwrite: bool = False, comparator: Callable[[Any, Any], bool] = None) -> Callable:
    cases: List[Case] = []
    valid_comparator: Callable[[Any, Any], bool] = comparator if comparator is not None else lambda x, y: x == y

    @singledispatch
    def register(*comparison_values: Any) -> Callable[[Callable], Callable]:
        return register_default(*comparison_values)

    @register.register(FunctionType)
    def register_default(*comparison_values: Any) -> Callable[[Callable], Callable]:
        def register_wrapper(case_func: Callable) -> Callable:
            for value in comparison_values:
                legacy: Optional[Case] = _find_legacy_case(value, cases, valid_comparator)
                if legacy is not None:
                    if not allow_overwrite:
                        raise OverwriteCaseError(func, value)
                    else:
                        cases.remove(legacy)

                cases.append(Case(value, case_func, None))
            return case_func
        return register_wrapper

    @register.register(FunctionType)
    def _(separate_comparator: Callable[[Any], bool], *args) -> Callable[[Callable], Callable]:
        if not callable(separate_comparator) or 0 < len(args):
            return register_default(separate_comparator, *args)

        def register_wrapper(case_func: Callable) -> Callable:
            cases.append(Case(None, case_func, separate_comparator))
            return case_func
        return register_wrapper

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        first_argument: Any = _get_first_argument(func, args, kwargs)
        case: Optional[Case] = _find_execute_case(first_argument, cases, valid_comparator)
        return case.func(*args, **kwargs) if case is not None else func(*args, **kwargs)

    wrapper.register = register
    return wrapper


def _find_legacy_case(value: Any, cases: List[Case], comparator: Callable[[Any, Any], bool]) -> Optional[Case]:
    return _find_case(lambda case: _check_by_common_comparator(value, case, comparator), cases)


def _find_execute_case(value: Any, cases: List[Case],
                       comparator: Callable[[Any, Any], bool]) -> Optional[Case]:
    return _find_case(lambda case: (_check_by_common_comparator(value, case, comparator)) or
                                   (_check_by_separate_comparator(value, case)), cases)


def _find_case(condition: Callable[[Case], bool], cases: List[Case]) -> Optional[Case]:
    try:
        return next(case for case in cases if condition(case))
    except StopIteration:
        return None


def _check_by_common_comparator(value: Any, case: Case, comparator: Callable[[Any, Any], bool]) -> bool:
    return case.separate_comparator is None and comparator(value, case.value)


def _check_by_separate_comparator(value: Any, case: Case) -> bool:
    return callable(case.separate_comparator) and case.separate_comparator(value)


def _get_first_argument(func: Callable, args: Tuple[Any, ...], kwargs: Dict[Text, Any]) -> Any:
    if 0 < len(args):
        return args[0]

    parameter: Mapping[Text, Parameter] = signature(func).parameters
    if len(parameter) <= 0:
        return None

    first_parameter_name: Text = next(iter(parameter))
    first_argument: Any = kwargs.get(first_parameter_name, None)
    return first_argument


class OverwriteCaseError(Exception):
    def __init__(self, target_func: Callable, tried_value: Any):
        self.message: Text = f"'{target_func.__name__}' already has the comparison value '{tried_value}'"

    def __str__(self) -> Text:
        return self.message
