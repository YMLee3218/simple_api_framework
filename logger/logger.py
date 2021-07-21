from contextlib import contextmanager
from typing import Any, Callable, List, Optional, Text, Tuple
from logging import Handler, Logger, getLogger

from logger.handlers_factory import create_handlers
from logger.intercept_handler import InterceptHandler


def get_logger(module_name: Optional[Text]) -> Logger:
    return getLogger(module_name)


def _create_root() -> Logger:
    root: Logger = get_logger(None)
    handlers: Tuple[Handler] = create_handlers()
    for handler in handlers:
        root.addHandler(handler)

    return root


_root_logger = _create_root()


def set_level(level: int):
    _root_logger.setLevel(level)


@contextmanager
def intercept_log(interceptor: Callable[[Text], Any], needs_full_format_log: bool = True):
    intercept_handler: InterceptHandler = InterceptHandler()
    intercept_handler.register(interceptor, needs_full_format_log)

    origin_handlers: List[Handler] = _root_logger.handlers
    try:
        _root_logger.handlers = []
        _root_logger.addHandler(intercept_handler)
        yield intercept_handler
    finally:
        _root_logger.handlers = origin_handlers
