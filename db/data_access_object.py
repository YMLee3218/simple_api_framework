from contextlib import contextmanager
from copy import deepcopy
from functools import reduce, singledispatch
from typing import Any, Dict, List, Text, Tuple, Type, Union, cast, overload

from db.db_connector import DBConnector
from json_data import JsonFormat, JsonObject, from_data_to, to_json_from
from logger import get_logger
from methoddispatcher import methoddispatcher

_logger = get_logger(__name__)


class _IDataAccessObject:
    def __init__(self, connector: DBConnector):
        pass


class DataAccessObject(_IDataAccessObject):
    def __init__(self, data_object_class: Type, table_name: Text, primary_key: Any, connector: DBConnector):
        super().__init__(connector)
        self.data_object_class: Type = data_object_class
        self.table_name: Text = table_name
        self.primary_key: Any = primary_key
        self.connector: DBConnector = connector

    def _create_primary_key(self) -> Any:
        sql: Text = f"select {self.table_name}_seq.nextval as {self.primary_key} from dual"
        return self.connector.execute(sql, should_return_single=True).result[self.primary_key]

    def insert(self, data_object: Any) -> Union[Any, List]:
        return ([self._insert_single(single_data_object) for single_data_object in data_object]
                if isinstance(data_object, list) else self._insert_single(data_object))

    def _insert_single(self, data_object: Any) -> Any:
        new_primary_key: int = self._create_primary_key()
        json_data: JsonFormat = to_json_from(data_object)
        json_data[self.primary_key] = new_primary_key
        sql: Text = (f"insert into {self.table_name}({', '.join(json_data.keys())}) values "
                     f"({','.join('?' * len(json_data))})")
        self.connector.execute(sql, *json_data.values(), should_return_single=True)
        return from_data_to(self.data_object_class, json_data)

    def select(self, primary_key: Any) -> Union[Any, List, None]:
        return self.select_where(f"{self.primary_key} = ?", primary_key, should_return_single=True)

    @overload
    def select_where(self, condition: Any, should_return_single: bool) -> Union[Any, List, None]:
        ...

    @overload
    def select_where(self, condition: Text, *args, should_return_single: bool) -> Union[Any, List, None]:
        ...

    def select_where(self, *args, **kwargs) -> Union[Any, List, None]:
        return self._select_where_implementation(*args, **kwargs)

    @methoddispatcher
    def _select_where_implementation(self, condition: Any, should_return_single: bool) -> Union[Any, List, None]:
        condition_sql, args = _convert_to_condition(condition, ' and ')
        return self.__select_where_implementation(condition_sql, *args, should_return_single=should_return_single)

    @_select_where_implementation.register(str)
    def __select_where_implementation(self, condition: Text, *args,
                                      should_return_single: bool) -> Union[Any, List, None]:
        sql: Text = f"select * from {self.table_name} where {condition}"
        selected_json_data: JsonObject = self.connector.execute(sql, *args,
                                                                should_return_single=should_return_single).result
        return (from_data_to(self.data_object_class, selected_json_data) if selected_json_data is not None
                else selected_json_data)

    def select_all(self) -> Union[List, None]:
        sql: Text = f"select * from {self.table_name}"
        selected_json_data: JsonObject = self.connector.execute(sql, should_return_single=False).result
        return from_data_to(self.data_object_class, selected_json_data)

    def update(self, data_object: Any) -> int:
        return self.update_where(data_object, f"{self.primary_key} = ?", getattr(data_object, self.primary_key))

    @overload
    def update_where(self, data_object: Any, condition: Any) -> int:
        ...

    @overload
    def update_where(self, data_object: Any, condition: Text, *condition_args) -> int:
        ...

    def update_where(self, *args, **kwargs) -> int:
        return self._update_where_implementation(*args, **kwargs)

    @methoddispatcher(2)
    def _update_where_implementation(self, data_object: Any, condition: Any) -> int:
        condition_sql, args = _convert_to_condition(condition, ' and ')
        return self.__update_where_implementation(data_object, condition_sql, *args)

    @_update_where_implementation.register(str)
    def __update_where_implementation(self, data_object: Any, condition: Text, *condition_args) -> int:
        update_sql, update_args = _convert_to_condition(data_object, ', ', self.primary_key)
        sql: Text = f"update {self.table_name} set {update_sql} where {condition}"
        return self.connector.execute(sql, *update_args, *condition_args, should_return_single=False).changed_count

    def delete(self, primary_key: Any) -> int:
        return self.delete_where(f"{self.primary_key} = ?", primary_key)

    @overload
    def delete_where(self, condition: Any) -> int:
        ...

    @overload
    def delete_where(self, condition: Text, *args) -> int:
        ...

    def delete_where(self, *args, **kwargs) -> int:
        return self._delete_where_implementation(*args, **kwargs)

    @methoddispatcher
    def _delete_where_implementation(self, condition: Any) -> int:
        condition_sql, args = _convert_to_condition(condition, ' and ')
        return self.__delete_where_implementation(condition_sql, *args)

    @_delete_where_implementation.register(str)
    def __delete_where_implementation(self, condition: Text, *args) -> int:
        sql: Text = f"delete from {self.table_name} where {condition}"
        return self.connector.execute(sql, *args, should_return_single=False).changed_count


def _convert_to_condition(data_object, delimiter: Text, *except_keys) -> Tuple[Text, Tuple]:
    json_data: JsonObject = to_json_from(data_object)
    filtered_json_data: JsonObject = {key: value for key, value in json_data.items() if key not in except_keys}
    return reduce(lambda acc, key: f"{acc}{'' if acc == '' else delimiter}{key} = ?",
                  filtered_json_data.keys(), ""), tuple(filtered_json_data.values())


class DAOGetter:
    def __init__(self, connector: DBConnector):
        self._connector: DBConnector = connector
        self._objects: Dict[Type[DataAccessObject], DataAccessObject] = {}

    def __getitem__(self, item: Type[DataAccessObject]) -> DataAccessObject:
        return self.get(item)

    def get(self, dao_type: Type[DataAccessObject]) -> DataAccessObject:
        if dao_type not in self._objects:
            self._objects[dao_type] = cast(DataAccessObject, cast(Type[_IDataAccessObject], dao_type)(self._connector))

        return self._objects[dao_type]


@overload
def access_to_db(readonly: bool):
    ...


@overload
def access_to_db(connector: DBConnector):
    ...


@contextmanager
def access_to_db(*args, **kwargs):
    return _access_to_db_implementation(*args, **kwargs)


@singledispatch
def _access_to_db_implementation(readonly: bool):
    connector: DBConnector = DBConnector(readonly)
    return _(connector)


@_access_to_db_implementation.register(DBConnector)
def _(connector: DBConnector):
    dao_getter: DAOGetter = DAOGetter(connector)
    try:
        yield dao_getter
        connector.commit()
    except Exception as e:
        connector.rollback()
        _logger.error(e)
        raise e
    finally:
        connector.close()
