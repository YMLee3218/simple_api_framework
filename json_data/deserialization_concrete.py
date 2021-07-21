from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import (Any, Callable, Dict, Iterable, KeysView, List, NamedTuple, Text, Tuple, Type, Union,
                    get_args, get_origin, get_type_hints)

from json_data import JsonObject
from json_data.deserialization import from_data_to, _compare_annotation
from switch_dispatch import switch_dispatch


@from_data_to.register(int, float)
def deserialize_number(annotation: Type, data: Union[int, float, Decimal], **kwargs) -> Any:
    return annotation(data)


@from_data_to.register(Text, bool, type(None), Any)
def deserialize_value(annotation: Type, data: Union[Text, bool, None, Any], **kwargs) -> Any:
    return data


@from_data_to.register(List)
def deserialize_list(annotation: Any, data_list: List, **kwargs) -> Any:
    return deserialize_generic(lambda args: [from_data_to(args[0], value, **kwargs) for value in data_list],
                               annotation, data_list)


@from_data_to.register(Dict)
def deserialize_dict(annotation: Any, data_dict: Dict, **kwargs) -> Any:
    return deserialize_generic(lambda args: {key: from_data_to(args[1], value, **kwargs)
                                             for key, value in data_dict.items()}, annotation, data_dict)


def deserialize_generic(deserialize: Callable[[Tuple[Any, ...]], Any], annotation: Any, values: Any) -> Any:
    args: Tuple[Any, ...] = get_args(annotation)
    if len(args) <= 0:
        return values

    return deserialize(args)


class Predict(NamedTuple):
    annotation: Any
    probability: float


@from_data_to.register(Union)
def deserialize_union(annotation: Any, data: Any, **kwargs) -> Any:
    args: Tuple[Any, ...] = get_args(annotation)
    predict, probability = find_predict_annotation_from(args, data)
    return from_data_to(predict, data, **kwargs)


def find_predict_annotation_from(candidates: Iterable, data: Any) -> Predict:
    return max((find_predict_annotation(candidate, data) for candidate in candidates),
               key=lambda candidate: candidate.probability)


@switch_dispatch(False, _compare_annotation)
def find_predict_annotation(annotation: Type, data: JsonObject) -> Predict:
    if not isinstance(annotation, type) or not isinstance(data, dict):
        return Predict(annotation, 0.0)

    data_argument_names: KeysView[Text] = data.keys()
    annotations: KeysView[Text] = get_type_hints(annotation).keys()
    matched_names_count: int = len(list(filter(lambda names: names[0] == names[1],
                                               zip(sorted(data_argument_names), sorted(annotations)))))
    return Predict(annotation, matched_names_count / max(len(data_argument_names), len(annotations)))


@find_predict_annotation.register(Any)
def _(annotation: Any, data: Any) -> Predict:
    return Predict(annotation, 0.5)


@find_predict_annotation.register(int, float, str, bool, type(None), List, Dict)
def _(annotation: Any, data: Any) -> Predict:
    annotation_origin: Any = get_origin(annotation) or annotation
    return Predict(annotation, 1.0 if isinstance(data, annotation_origin) else 0.0)


@find_predict_annotation.register(Union)
def _(annotation: Any, data: Any) -> Predict:
    args: Tuple[Any, ...] = get_args(annotation)
    return find_predict_annotation_from(args, data)


@from_data_to.register(lambda annotation: isinstance(annotation, type) and issubclass(annotation, Enum))
def deserialize_enum(annotation: Any, data: Any, **kwargs) -> Any:
    return annotation(data)


@from_data_to.register(datetime)
def deserialize_datetime(annotation: Any, data: Any, **kwargs) -> Any:
    return data
