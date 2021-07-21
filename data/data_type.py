import cgitb
from dataclasses import dataclass
from functools import lru_cache
from traceback import TracebackException
from types import TracebackType
from typing import Any, Dict, KeysView, Text, Tuple, Type, get_type_hints

from json_data import JsonFormat
from slotdataclass import slotdataclass


DEFAULT_KEY: Text = "Default"


@slotdataclass
@dataclass
class ErrorData:
    exception: Text
    message: Text


def create_error_data(error: Exception) -> ErrorData:
    traceback: TracebackException = TracebackException.from_exception(error)
    return ErrorData(exception=traceback.exc_type.__name__, message=''.join(traceback.format_exception_only()).strip())


def get_error_full_context(error: Exception) -> Text:
    exc_info: Tuple[Type[Exception], Exception, TracebackType] = (type(error), error, error.__traceback__)
    return cgitb.text(exc_info)


def is_error_data(data: JsonFormat) -> bool:
    if not isinstance(data, dict):
        return False

    annotations: Dict[Text, Any] = _get_cached_type_hints(ErrorData)
    if len(data) != len(annotations.keys()):
        return False

    return all(name in data and isinstance(data[name], annotation) for name, annotation in annotations.items())


@lru_cache(1)
def _get_cached_type_hints(cls: Type) -> Dict[Text, Any]:
    return get_type_hints(cls)


class ResponseError(Exception):
    exception: Text

    def __init__(self, error: ErrorData):
        self.message: Text = f"An error occurred on the server: {error.message}"
        self._set_error(error)

    def _set_error(self, error: ErrorData):
        properties: KeysView[Text] = _get_cached_type_hints(ErrorData).keys()
        for property_ in properties:
            attr: Any = getattr(self, property_, None)
            if attr is not None:
                continue

            error_attr: Any = getattr(error, property_, None)
            setattr(self, property_, error_attr)

    def __str__(self) -> Text:
        return self.message
