from os import environ
from pyodbc import Connection, Cursor, Row, connect
from typing import Any, Dict, List, Text

from concrete import concrete
from db.db_connector import DBConnector, ExecuteResult
from json_data import JsonFormat


@concrete
class TiberoConnector(DBConnector):
    is_initialized: bool = False
    connect_option: Text = "DSN=tibero6"
    connection: Connection

    @staticmethod
    def try_to_first_initialize():
        if TiberoConnector.is_initialized:
            return

        TiberoConnector.first_initialize()

    @staticmethod
    def first_initialize():
        environ["TBCLI_WCHAR_TYPE"] = "ucs2"

    def _initialize(self, readonly: bool):
        TiberoConnector.try_to_first_initialize()
        self.connection = connect(TiberoConnector.connect_option, readonly=readonly)
        self.connection.autocommit = False

    def execute(self, sql: Text, *args, should_return_single: bool) -> ExecuteResult:
        cursor: Cursor = self.connection.cursor()
        result_cursor: Cursor = cursor.execute(sql, *args)
        changed_count: int = result_cursor.rowcount
        result: JsonFormat = convert_result_to_json(result_cursor, should_return_single) if is_select(sql) else None
        return ExecuteResult(changed_count, result)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def is_select(sql: Text) -> bool:
    return sql.startswith('select')


def convert_result_to_json(cursor: Cursor, should_return_single: bool) -> JsonFormat:
    columns: List[Text] = [str.lower(description[0]) for description in cursor.description]
    values: List[Row] = [cursor.fetchone()] if should_return_single else cursor.fetchall()
    if None in values:
        return None

    result: List[Dict[Text, Any]] = [dict(zip(columns, value)) for value in values]
    return result[0] if should_return_single else result

