from dataclasses import dataclass
from functools import lru_cache, singledispatch
from inspect import Parameter, signature
from types import FunctionType
from typing import Any, Callable, Coroutine, List, Text, Tuple, ValuesView, overload

from async_util import await_or_not
from concrete import AbstractMeta
from data import DEFAULT_KEY, ErrorData, create_error_data, get_error_full_context
from json_data import JsonFormat, from_data_to, to_json_from
from logger import get_logger
from slotdataclass import slotdataclass

_logger = get_logger(__name__)

RECEIVER_KEY: Text = "Receiver"


@slotdataclass
@dataclass
class Receiver:
    call: Callable[[Any], Any]
    key: Text = DEFAULT_KEY
    

class DataReceiver(metaclass=AbstractMeta):
    def __init__(self, *receivers: Receiver, **kwargs):
        self.initialize(**kwargs)

        def receive(data: JsonFormat, key: Text = DEFAULT_KEY) -> Coroutine[Any, Any, JsonFormat]:
            return _receive_to_receivers(data, receivers, key)

        self.route(receive, **kwargs)

    def initialize(self, **kwargs):
        """Function that can be used by overriding when initial setting is required."""
        pass

    def route(self, receive: Callable[[JsonFormat, Text], Coroutine[Any, Any, JsonFormat]], **kwargs):
        pass


async def _receive_to_receivers(data: JsonFormat, receivers: Tuple[Receiver, ...], key: Text) -> JsonFormat:
    selected_receivers: List[Receiver] = [receiver for receiver in receivers if receiver.key == key]
    if len(selected_receivers) <= 0:
        error: NoReceiverError = NoReceiverError(key)
        return _handle_error(error)

    responses: List[JsonFormat] = [await _receive_to_receiver(data, receiver) for receiver in selected_receivers]
    return responses[0] if len(responses) == 1 else responses


async def _receive_to_receiver(data: JsonFormat, receiver: Receiver) -> JsonFormat:
    try:
        data_type: Any = _get_first_parameter_type(receiver.call)
        data_instance: Any = from_data_to(data_type, data)
        response_instance: Any = await await_or_not(receiver.call(data_instance))
        return to_json_from(response_instance)
    except Exception as e:
        return _handle_error(e)


def _handle_error(error: Exception) -> JsonFormat:
    _logger.error(get_error_full_context(error))
    error_data: ErrorData = create_error_data(error)
    return to_json_from(error_data)


@lru_cache
def _get_first_parameter_type(func: Callable) -> Any:
    parameters: ValuesView[Parameter] = signature(func).parameters.values()
    try:
        first_parameter: Parameter = next(parameter for parameter in parameters
                                          if parameter.kind == Parameter.POSITIONAL_ONLY
                                          or parameter.kind == Parameter.POSITIONAL_OR_KEYWORD)
    except StopIteration:
        return Any

    annotation: Any = first_parameter.annotation
    return annotation if annotation is not Parameter.empty else Any


_registered_receivers: List[Receiver] = []


@overload
def register_as_receiver(key: Text = DEFAULT_KEY) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
    ...


@overload
def register_as_receiver(func: Callable[[Any], Any], key: Text = DEFAULT_KEY) -> Callable[[Any], Any]:
    ...


def register_as_receiver(*args, **kwargs) -> Callable[[Any], Any]:
    return _register_as_receiver_implementation(*args, **kwargs)


@singledispatch
def _register_as_receiver_implementation(key: Text = DEFAULT_KEY) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
    return lambda func: _(func, key)


@_register_as_receiver_implementation.register(FunctionType)
def _(func: Callable[[Any], Any], key: Text = DEFAULT_KEY) -> Callable[[Any], Any]:
    receiver = Receiver(func, key)
    _registered_receivers.append(receiver)
    return func


def get_registered_receivers() -> List[Receiver]:
    return _registered_receivers


class NoReceiverError(Exception):
    def __init__(self, key: Text):
        self.message: Text = f"There is no receiver registered for the key '{key}'."

    def __str__(self) -> Text:
        return self.message
