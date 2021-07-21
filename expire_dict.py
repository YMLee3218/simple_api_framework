import asyncio
from dataclasses import dataclass
from slotdataclass import slotdataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, TypeVar

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


@slotdataclass
@dataclass
class _Item:
    set_time: datetime
    item: ValueType

    @staticmethod
    def create(item: ValueType) -> "_Item":
        return _Item(datetime.now(), item)

    def reset_time(self):
        self.set_time = datetime.now()


class ExpireDict(Generic[KeyType, ValueType]):
    def __init__(self, life_time: int, expire_cycle: int, **kwargs):
        self.life_time: timedelta = timedelta(seconds=life_time)
        self.expire_cycle: int = expire_cycle
        self._expire_handler: Optional[asyncio.TimerHandle] = None
        self._dict: Dict[KeyType, _Item] = dict(kwargs)

    def __getitem__(self, key: KeyType) -> ValueType:
        item: _Item = self._dict.__getitem__(key)
        item.reset_time()
        return item.item

    def __setitem__(self, key: KeyType, value: ValueType):
        if self._is_empty():
            self._start_auto_expire()

        return self._dict.__setitem__(key, _Item.create(value))

    def __delitem__(self, key: KeyType):
        if self._has_single_item():
            self._stop_auto_expire()

        return self._dict.__delitem__(key)

    def get(self, key: KeyType, default: Optional[ValueType] = None) -> ValueType:
        item: Any = self._dict.get(key, default)
        if not isinstance(item, _Item):
            return item

        item.reset_time()
        return item.item

    def setdefault(self, key: KeyType, default: Optional[ValueType] = None) -> ValueType:
        if key in self:
            return self[key]

        if self._is_empty():
            self._start_auto_expire()

        item: _Item = _Item.create(default)
        self[key] = item
        return item.item

    def __contains__(self, key: KeyType) -> bool:
        return self._dict.__contains__(key)

    def _is_empty(self) -> bool:
        return len(self._dict) <= 0

    def _has_single_item(self) -> bool:
        return len(self._dict) == 1

    def _start_auto_expire(self):
        if self._expire_handler is not None:
            self._stop_auto_expire()

        self._set_expire_handler()

    def _stop_auto_expire(self):
        if self._expire_handler is None:
            return

        self._expire_handler.cancel()
        self._expire_handler = None

    def _set_expire_handler(self):
        self._expire_handler = asyncio.get_event_loop().call_later(self.expire_cycle, self._run_auto_expire)

    def _run_auto_expire(self):
        self.expire()
        if not self._is_empty():
            self._set_expire_handler()

    def expire(self):
        now: datetime = datetime.now()
        del_keys: List[KeyType] = []
        for key in self._dict.keys():
            item: _Item = self._dict[key]
            if item.set_time + self.life_time <= now:
                del_keys.append(key)

        for key in del_keys:
            del self[key]
