from argparse import ArgumentParser
from functools import lru_cache
from typing import Any, Dict, Optional, Text

from argument_getter import Argument, ArgumentGetter
from concrete import concrete


@concrete
class ParserArgumentGetter(ArgumentGetter):
    parser: ArgumentParser
    added_argument_count: int

    def initialize(self, **kwargs):
        self.parser = ArgumentParser(**kwargs)
        self.added_argument_count = 0

    def add(self, argument: Argument):
        const_value: Optional[Any] = argument.const_value
        kwargs: Dict[Text, Any] = {'action': 'store' if const_value is None else 'store_const', 'const': const_value,
                                   'default': argument.default, 'help': argument.description}
        if const_value is None:
            kwargs['type'] = argument.type_converter

        if argument.default is not None:
            kwargs['dest'] = argument.to_name

        self.parser.add_argument(f"{'' if argument.default is None else '--'}{argument.from_name}", **kwargs)
        self.added_argument_count = self.added_argument_count + 1

    def get(self, name: Text) -> Any:
        return _get_cached_parsed_arguments(self.parser, self.added_argument_count)[name]


@lru_cache(1)
def _get_cached_parsed_arguments(parser: ArgumentParser, added_arguments_count: int) -> Dict[Text, Any]:
    return vars(parser.parse_known_args()[0])
