from functools import singledispatch, wraps
from types import FunctionType
from typing import Callable, Union, overload


@overload
def methoddispatcher(checked_argument_index: int = 1) -> Callable[[Callable], Callable]:
    ...


@overload
def methoddispatcher(func: Callable, checked_argument_index: int = 1) -> Callable:
    ...


def methoddispatcher(*args, **kwargs) -> Union[Callable[[Callable], Callable], Callable]:
    return _methoddispatcher_implementation(*args, **kwargs)


@singledispatch
def _methoddispatcher_implementation(checked_argument_index: int = 1) -> Callable[[Callable], Callable]:
    return lambda func: _(func, checked_argument_index)


@_methoddispatcher_implementation.register(FunctionType)
def _(func: Callable, checked_argument_index: int = 1) -> Callable:
    dispatcher = singledispatch(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return dispatcher.dispatch(type(args[checked_argument_index]))(*args, **kwargs)

    wrapper.register = dispatcher.register
    return wrapper
