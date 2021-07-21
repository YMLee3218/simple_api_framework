from typing import Any, Dict, List, Text, Union

JsonObject = Dict[Text, Any]
JsonValue = Union[int, Text, bool, type(None)]
JsonList = List[Union[JsonObject, JsonValue]]
JsonFormat = Union[JsonObject, JsonValue, JsonList]
