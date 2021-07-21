from functools import singledispatch
from typing import Any, Iterable, Text, get_type_hints

from json_data import JsonFormat


@singledispatch
def to_json_from(instance: Any) -> JsonFormat:
    try:
        variables_names: Iterable[Text] = _get_variables_names(instance)
    except AttributeError as e:
        raise SerializingFailError(instance).with_traceback(e.__traceback__) from e

    return {name: to_json_from(getattr(instance, name)) for name in variables_names}


def _get_variables_names(instance: Any) -> Iterable[Text]:
    if isinstance(instance, tuple):
        return get_type_hints(type(instance)).keys()

    return instance.__dict__.keys() if '__dict__' in dir(instance) else instance.__slots__


class SerializingFailError(Exception):
    def __init__(self, instance: Any):
        self.message: Text = f"Fail to deserialize '{instance}: {type(instance).__name__}'."

    def __str__(self) -> Text:
        return self.message
