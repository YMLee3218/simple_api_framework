from collections import defaultdict
from functools import singledispatch
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Text, overload

from concrete import AbstractMeta


class Argument(NamedTuple):
    from_name: Text
    to_name: Text
    const_value: Optional[Any]
    default: Optional[Any]
    type_converter: Callable[[Any], Any]
    description: Optional[Text]


class ArgumentGetter(metaclass=AbstractMeta):
    def __init__(self, **kwargs):
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        """Function that can be used by overriding when initial setting is required."""
        pass

    def add(self, argument: Argument):
        pass

    def get(self, name: Text) -> Any:
        pass


class _ArgumentStore(ArgumentGetter):
    arguments: List[Argument] = []

    def add(self, argument: Argument):
        self.arguments.append(argument)


class _MainGetter:
    _store: _ArgumentStore = _ArgumentStore()
    _getter: Optional[ArgumentGetter] = None

    @staticmethod
    def get_to_add() -> ArgumentGetter:
        return _MainGetter._getter if _MainGetter._getter is not None else _MainGetter._store

    @staticmethod
    def get() -> ArgumentGetter:
        if _MainGetter._getter is None:
            _MainGetter.set(ArgumentGetter())

        return _MainGetter._getter

    @staticmethod
    def set(getter: ArgumentGetter):
        _MainGetter._getter = getter
        for argument in _MainGetter._store.arguments:
            _MainGetter.get().add(argument)


def pass_getter_arguments(**kwargs):
    _MainGetter.set(ArgumentGetter(**kwargs))


_to_names: Dict[Text, List[Text]] = defaultdict(list)


@overload
def add_argument(key: Text, from_name: Text, *, const_value: Optional[Any] = None,
                 default: Optional[Any] = None, type_converter: Callable[[Any], Any] = str,
                 description: Optional[Text] = None, to_name: Optional[Text] = None):
    ...


@overload
def add_argument(argument_getter: ArgumentGetter, key: Text, from_name: Text, *, const_value: Optional[Any] = None,
                 default: Optional[Any] = None, type_converter: Callable[[Any], Any] = str,
                 description: Optional[Text] = None, to_name: Optional[Text] = None):
    ...


def add_argument(*args, **kwargs):
    return _add_argument_implementation(*args, **kwargs)


@singledispatch
def _add_argument_implementation(key: Text, from_name: Text, *, const_value: Optional[Any] = None,
                                 default: Optional[Any] = None, type_converter: Callable[[Any], Any] = str,
                                 description: Optional[Text] = None, to_name: Optional[Text] = None):
    __add_argument_implementation(_MainGetter.get_to_add(), key, from_name, const_value=const_value, default=default,
                                  type_converter=type_converter, description=description, to_name=to_name)


@_add_argument_implementation.register(ArgumentGetter)
def __add_argument_implementation(argument_getter: ArgumentGetter, key: Text, from_name: Text, *,
                                  const_value: Optional[Any] = None, default: Optional[Any] = None,
                                  type_converter: Callable[[Any], Any] = str, description: Optional[Text] = None,
                                  to_name: Optional[Text] = None):
    argument: Argument = Argument(from_name, to_name if to_name is not None else from_name, const_value, default,
                                  type_converter, description)
    _to_names[key].append(argument.to_name)
    argument_getter.add(argument)


@overload
def get_arguments(key: Text) -> Dict[Text, Any]:
    ...


@overload
def get_arguments(argument_getter: ArgumentGetter, key: Text) -> Dict[Text, Any]:
    ...


def get_arguments(*args, **kwargs) -> Dict[Text, Any]:
    return _get_arguments_implementation(*args, **kwargs)


@singledispatch
def _get_arguments_implementation(key: Text) -> Dict[Text, Any]:
    return __get_arguments_implementation(_MainGetter.get(), key)


@_get_arguments_implementation.register(ArgumentGetter)
def __get_arguments_implementation(argument_getter: ArgumentGetter, key: Text) -> Dict[Text, Any]:
    to_names: List[Text] = _to_names.get(key, [])
    return {to_name: argument_getter.get(to_name) for to_name in to_names}
