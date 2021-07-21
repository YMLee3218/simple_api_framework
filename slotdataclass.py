from dataclasses import dataclass, _FIELDS
from typing import Any, Dict, Text


_ANNOTATIONS: Text = '__annotations__'
_DICT: Text = '__dict__'
_SLOTS: Text = '__slots__'


def slotdataclass(cls: type) -> type:
    annotations: Dict[Text, type] = getattr(cls, _ANNOTATIONS, None)
    attributes: Dict[Text, Any]
    if annotations is not None:
        attributes = {name: value for name, value in vars(cls).items() if name not in annotations and name != _DICT}
        attributes[_ANNOTATIONS] = annotations
        attributes[_SLOTS] = annotations.keys()
    else:
        attributes = {_SLOTS: ()}

    wrapper: type = type(cls.__name__, cls.__bases__, attributes)
    return dataclass(wrapper) if _FIELDS not in attributes else wrapper
