from typing import Dict, List, NamedTuple, Optional, Text, Tuple, get_type_hints

from concrete import AbstractMeta


class StatusInfo(NamedTuple):
    name: Text
    description: Text


class _HTTPStatusListBase(metaclass=AbstractMeta):
    unknown_status: StatusInfo = StatusInfo("Unknown", "Unknown status code.")

    def __init__(self):
        status_info_length: int = len(get_type_hints(StatusInfo))
        class_dict_tuples: List[Tuple] = [property_ for name, property_ in vars(type(self)).items()
                                          if isinstance(property_, tuple) and len(property_) == status_info_length + 1]
        self.statuses: Dict[int, StatusInfo] = {code: StatusInfo(name, description) for code, name, description
                                                in class_dict_tuples if isinstance(code, int) and isinstance(name, str)
                                                and isinstance(description, str)}

    def get(self, code: int) -> StatusInfo:
        return self.statuses.get(code, _HTTPStatusListBase.unknown_status)


class _HTTPStatusMeta(type):
    status_list: Optional[_HTTPStatusListBase] = None

    def __getitem__(self, code: int) -> StatusInfo:
        if _HTTPStatusMeta.status_list is None:
            _HTTPStatusMeta.status_list = _HTTPStatusListBase()

        return _HTTPStatusMeta.status_list.get(code)


class HTTPStatus(metaclass=_HTTPStatusMeta):
    pass


class HTTPStatusError(Exception):
    def __init__(self, code: int):
        name, description = HTTPStatus[code]
        self.message: Text = f"{code} {name}: {description}"

    def __str__(self) -> Text:
        return self.message
