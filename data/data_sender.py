from functools import singledispatch
from itertools import groupby
from typing import Any, Dict, List, NamedTuple, Optional, Text, Tuple, Type, Union, overload

from async_util import await_or_not
from concrete import AbstractMeta
from data import (DEFAULT_KEY, ErrorData, JsonFormat, ResponseError, from_data_to, is_error_data, to_json_from)

SENDER_KEY: Text = "Sender"


class DataSender(metaclass=AbstractMeta):
    def __init__(self, **kwargs):
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        """Function that can be used by overriding when initial setting is required."""
        pass

    async def send(self, data: JsonFormat, key: Text = DEFAULT_KEY, **kwargs) -> JsonFormat:
        pass


class _MainSender:
    _sender: Optional[DataSender] = None

    @staticmethod
    def get() -> DataSender:
        if _MainSender._sender is None:
            _MainSender.set(DataSender())

        return _MainSender._sender

    @staticmethod
    def set(sender: DataSender):
        _MainSender._sender = sender


def pass_sender_arguments(**kwargs):
    _MainSender.set(DataSender(**kwargs))


class Response(NamedTuple):
    instance: Union[Any, List]
    error: Union[Exception, List[Exception]]


@overload
async def send(data: Any, response_type: Type, key: Text = DEFAULT_KEY, **kwargs) -> Response:
    ...


@overload
async def send(sender: DataSender, data: Any, response_type: Type, key: Text = DEFAULT_KEY, **kwargs) -> Response:
    ...


async def send(*args, **kwargs) -> Response:
    return await _send_implementation(*args, **kwargs)


@singledispatch
async def _send_implementation(data: Any, response_type: Type, key: Text = DEFAULT_KEY, **kwargs) -> Response:
    return await _(_MainSender.get(), data, response_type, key, **kwargs)


@_send_implementation.register(DataSender)
async def _(sender: DataSender, data: Any, response_type: Type, key: Text = DEFAULT_KEY,
            **kwargs) -> Response:
    response_data: Union[JsonFormat, Exception] = await _get_response_data(sender, data, key, **kwargs)
    response_data_list: List[Union[JsonFormat, Exception]] = (response_data if isinstance(response_data, list)
                                                              else [response_data])
    instance_list: List[Union[response_type, Exception]]\
        = [_try_get_instance_from(response_type, response_data) for response_data in response_data_list]
    instance_groups: Dict[bool, List[Union[response_type, Exception]]]\
        = {not is_exception: list(instances) for is_exception, instances
           in groupby(instance_list, key=lambda instance_: isinstance(instance_, Exception))}

    instance, error = _get_single_or_lists(instance_groups.get(True, None), instance_groups.get(False, None))
    return Response(instance, error)


async def _get_response_data(sender: DataSender, data: Any, key: Text, **kwargs) -> Union[JsonFormat, Exception]:
    json_data: JsonFormat = to_json_from(data)
    try:
        return await await_or_not(sender.send(json_data, key, **kwargs))
    except Exception as e:
        return e


def _try_get_instance_from(data_type: Type, data: Union[JsonFormat, Exception]) -> Union[JsonFormat, Exception]:
    try:
        return _get_instance_from(data_type, data)
    except Exception as e:
        return e


def _get_instance_from(data_type: Type, data: Union[JsonFormat, Exception]) -> Union[JsonFormat, Exception]:
    if isinstance(data, Exception):
        return data

    if is_error_data(data):
        error: ErrorData = from_data_to(ErrorData, data)
        return ResponseError(error)

    return from_data_to(data_type, data)


def _get_single_or_lists(*single_or_lists: Optional[List]) -> Union[Any, List, None, Tuple]:
    if len(single_or_lists) <= 1:
        return _get_single_or_list(single_or_lists[0])

    return tuple(_get_single_or_list(single_of_list) for single_of_list in single_or_lists)


def _get_single_or_list(single_or_list: Optional[List]) -> Union[Any, List, None]:
    if single_or_list is None or len(single_or_list) == 0:
        return None

    return single_or_list[0] if len(single_or_list) == 1 else single_or_list
