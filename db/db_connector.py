from typing import NamedTuple, Text

from concrete import AbstractMeta
from json_data import JsonFormat


class ExecuteResult(NamedTuple):
    changed_count: int
    result: JsonFormat


class DBConnector(metaclass=AbstractMeta):
    def __init__(self, readonly: bool):
        self._initialize(readonly)

    def _initialize(self, readonly: bool):
        pass

    def execute(self, sql: Text, *args, should_return_single: bool) -> ExecuteResult:
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass
