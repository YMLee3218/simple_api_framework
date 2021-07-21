from slotdataclass import slotdataclass
from typing import Any, Callable, List, Text
from logging import Handler, LogRecord, NOTSET


@slotdataclass
class _Observer:
    observer: Callable[[Text], Any]
    needs_full_format_log: bool


class InterceptHandler(Handler):
    def __init__(self, level=NOTSET):
        super().__init__(level)
        self.observers: List[_Observer] = []

    def register(self, observer: Callable[[Text], Any], needs_full_format_log: bool = True):
        self.observers.append(_Observer(observer, needs_full_format_log))

    def emit(self, record: LogRecord) -> None:
        for observer in self.observers:
            self.emit_to_observer(record, observer)

    def emit_to_observer(self, record: LogRecord, observer: _Observer):
        try:
            message: Text = self.format(record) if observer.needs_full_format_log else record.getMessage()
            observer.observer(message)
        except Exception:
            self.handleError(record)
