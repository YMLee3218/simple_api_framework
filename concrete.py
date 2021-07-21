from functools import singledispatch
from typing import Any, Callable, Text, Tuple, Type, Union, cast, overload


@overload
def concrete(allow_overwrite: bool = False) -> Callable[[Type], Type]:
    ...


@overload
def concrete(cls: Type, allow_overwrite: bool = False) -> Type:
    ...


def concrete(*args, **kwargs) -> Union[Callable[[Type], Type], Type]:
    return _concrete_implementation(*args, **kwargs)


@singledispatch
def _concrete_implementation(allow_overwrite: bool = False) -> Callable[[Type], Type]:
    return lambda cls: _(cls, allow_overwrite)


@_concrete_implementation.register(type)
def _(cls: Type, allow_overwrite: bool = False) -> Type:
    abstract: Tuple[Type, ...] = tuple(filter(
        lambda base: issubclass(type(base), AbstractMeta), cls.__bases__))

    if len(abstract) <= 0:
        raise NoAbstractError(cls)

    for target in abstract:
        target_meta: object = target
        cast(AbstractMeta, target_meta).set_concrete(cls, allow_overwrite)

    return cls


class AbstractMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.concrete: Type = cls

    def set_concrete(cls, concrete_: Type, allow_overwrite=False):
        if not allow_overwrite and cls.concrete is not cls:
            raise OverwriteConcreteError(cls, cls.concrete, concrete_)

        cls.concrete = concrete_

    def __call__(cls, *args, **kwargs) -> Any:
        instance: cls.concrete = object.__new__(cls.concrete)
        instance.__init__(*args, **kwargs)
        return instance


class NoAbstractError(Exception):
    def __init__(self, cls: Type):
        self.message: Text = (f"Cannot find abstract class of '{cls.__name__}'. "
                              f"Set the metaclass to '{AbstractMeta.__name__}' of the base class "
                              f"you want to select as abstract class.")

    def __str__(self) -> Text:
        return self.message


class OverwriteConcreteError(Exception):
    def __init__(self, target_cls: Type, prev_cls: Type, tried_cls: Type):
        self.message: Text = (f"Tried to register '{tried_cls}' as concrete class to '{target_cls}' "
                              f"that already has an '{prev_cls}' as concrete class.")

    def __str__(self) -> Text:
        return self.message
