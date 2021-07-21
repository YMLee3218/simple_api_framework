from datetime import datetime
from enum import Enum
from time import mktime
from typing import Dict, List, Text, Union

from json_data import JsonList, JsonObject, JsonValue
from json_data.serialization import to_json_from


@to_json_from.register(int)
@to_json_from.register(float)
@to_json_from.register(str)
@to_json_from.register(bool)
@to_json_from.register(type(None))
def serialize_value(instance: Union[int, float, Text, bool, type(None)]) -> JsonValue:
    return instance


@to_json_from.register(list)
def serialize_list(instances: List) -> JsonList:
    return [to_json_from(instance) for instance in instances]


@to_json_from.register(dict)
def serialize_dict(instances: Dict) -> JsonObject:
    return {name: to_json_from(value) for name, value in instances.items()}


@to_json_from.register(Enum)
def serialize_enum(instance: Enum) -> JsonValue:
    return instance.value


@to_json_from.register(datetime)
def serialize_datetime(instance: datetime) -> JsonValue:
    return instance
