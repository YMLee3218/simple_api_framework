from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from re import Pattern, compile
from typing import Any, Dict, List, NamedTuple, Optional, Text, Union
import unittest

from json_data import DeserializingFailError, InvalidAnnotationError, JsonFormat, from_data_to, serializing_option
from logger import intercept_log


class TestDeserialization(unittest.TestCase):
    def test_value_deserialize(self):
        json_data: JsonFormat = 1
        deserialized_data: int = from_data_to(int, json_data)
        self.assertEqual(deserialized_data, 1)

    def test_1_dimension_deserialize(self):
        @dataclass
        class DataItem(Item):
            a: int
            b: Text

        json_data: JsonFormat = {'a': 1, 'b': 'test'}
        deserialized_data: DataItem = from_data_to(DataItem, json_data)
        test_item_1(self, deserialized_data)

    def test_named_tuple_deserialize(self):
        class TupleItem(NamedTuple):
            a: int
            b: Text

        json_data: JsonFormat = {'a': 1, 'b': 'test'}
        deserialized_data: TupleItem = from_data_to(TupleItem, json_data)
        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b, 'test')

    def test_list_deserialize(self):
        json_data: JsonFormat = [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}]
        deserialized_data: List[Item] = from_data_to(Item, json_data)
        test_item_list(self, deserialized_data)

        json_data2: JsonFormat = [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}]
        deserialized_data2: List = from_data_to(type(json_data2), json_data)
        self.assertEqual(json_data2, deserialized_data2)

    def test_contains_reserved_deserialize(self):
        class ContainsReserved:
            self: Text
            args: Text
            kwargs: Text

        json_data: JsonFormat = {'self': 'aa', 'args': 'bb', 'kwargs': 'cc'}
        deserialized_data: ContainsReserved = from_data_to(ContainsReserved, json_data)
        self.assertEqual(deserialized_data.self, 'aa')
        self.assertEqual(deserialized_data.args, 'bb')
        self.assertEqual(deserialized_data.kwargs, 'cc')

    def test_less_args_deserialize(self):
        @dataclass
        class LessArgs:
            a: int
            b: Text
            c: bool

        json_data: JsonFormat = {'a': 1, 'b': 'test'}
        with intercept_log(lambda message: self.assertTrue(is_in_log('c', message))):
            deserialized_data: LessArgs = from_data_to(LessArgs, json_data)

        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b, 'test')
        self.assertEqual(deserialized_data.c, None)

    def test_too_many_args_deserialize(self):
        @dataclass
        class DataItem(Item):
            a: int
            b: Text

        json_data: JsonFormat = {'a': 1, 'b': 'test', 'c': True}
        with intercept_log(lambda message: self.assertTrue(is_in_log('c', message))):
            deserialized_data: DataItem = from_data_to(DataItem, json_data)

        test_item_1(self, deserialized_data)
        with self.assertRaises(AttributeError):
            c: bool = deserialized_data.c

    def test_derived_deserialize(self):
        class Derived(Item):
            b: int
            c: Text

        json_data: JsonFormat = {'a': 1, 'b': 2, 'c': 'test'}
        deserialized_data: Derived = from_data_to(Derived, json_data)
        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b, 2)
        self.assertEqual(deserialized_data.c, 'test')

    def test_item_in_object_deserialize(self):
        class Container:
            item: Item
            id: int

        json_data: JsonFormat = {'item': {'a': 1, 'b': 'test'}, 'id': 0}
        deserialized_data: Container = from_data_to(Container, json_data)
        test_item_1(self, deserialized_data.item)
        self.assertEqual(deserialized_data.id, 0)

    def test_items_in_list_deserialize(self):
        class ItemList:
            items: List[Item]
            items_in_items: List[List[Item]]
            id: int

        json_data: JsonFormat = {'items': [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}],
                                 'items_in_items': [[{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}],
                                                    [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}]],
                                 'id': 0}
        deserialized_data: ItemList = from_data_to(ItemList, json_data)

        test_item_list(self, deserialized_data.items)
        for items in deserialized_data.items_in_items:
            test_item_list(self, items)

        self.assertEqual(deserialized_data.id, 0)

    def test_items_in_dict_deserialize(self):
        class ItemDict:
            text_item: Dict[Text, Item]
            text_item_list: Dict[Text, List[Item]]
            dict_list: List[Dict[Text, Item]]
            id: int

        json_data: JsonFormat = {'text_item': {'aa': {'a': 1, 'b': 'test'}, 'bb': {'a': 2, 'b': 'test2'}},
                                 'text_item_list': {'aa': [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}],
                                                    'bb': [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}]},
                                 'dict_list': [{'aa': {'a': 1, 'b': 'test'}, 'bb': {'a': 2, 'b': 'test2'}},
                                               {'cc': {'a': 1, 'b': 'test'}, 'dd': {'a': 2, 'b': 'test2'}}],
                                 'id': 0}
        deserialized_data: ItemDict = from_data_to(ItemDict, json_data)

        test_item_dict_1(self, deserialized_data.text_item)
        test_item_list(self, deserialized_data.text_item_list['aa'])
        test_item_list(self, deserialized_data.text_item_list['bb'])
        test_item_dict_1(self, deserialized_data.dict_list[0])
        test_item_dict_2(self, deserialized_data.dict_list[1])
        self.assertEqual(deserialized_data.id, 0)

    def test_dict_deserialize(self):
        json_data: JsonFormat = {'a': 1, 'b': 'test'}
        deserialized_data: Dict[Text, Any] = from_data_to(dict, json_data)
        self.assertEqual(deserialized_data['a'], 1)
        self.assertEqual(deserialized_data['b'], 'test')

    def test_any_deserialize(self):
        class AnyItem(Item):
            a: Any
            b: Any

        json_data: JsonFormat = {'a': 1, 'b': [1, [2, 3], {'aa': 4}]}
        deserialized_data: AnyItem = from_data_to(AnyItem, json_data)
        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b[0], 1)
        self.assertEqual(deserialized_data.b[1][0], 2)
        self.assertEqual(deserialized_data.b[1][1], 3)
        self.assertEqual(deserialized_data.b[2]['aa'], 4)

    def test_optional_deserialize(self):
        class OptionalItem(Item):
            a: Optional[int]
            b: Optional[Text]

        class Container:
            item: Optional[OptionalItem]
            item2: Optional[OptionalItem]
            items: Optional[List[Optional[OptionalItem]]]

        json_data: JsonFormat = {'item': {'a': 1, 'b': 'test'}, 'item2': None,
                                 'items': [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}, None]}
        deserialized_data: Container = from_data_to(Container, json_data)
        test_item_1(self, deserialized_data.item)
        self.assertEqual(deserialized_data.item2, None)
        test_item_list(self, deserialized_data.items)
        self.assertEqual(deserialized_data.items[2], None)

    def test_union_deserialize(self):
        class UnionItem(Item):
            a: Union[int, Text]
            b: Union[int, Text]

        class UnionItem2:
            b: Union[int, Text]
            c: Union[int, Text]

        class Container:
            value_or_item: Union[int, Item]
            value_or_item2: Union[Text, Item]
            item_or_2: Union[UnionItem, UnionItem2]
            item_or_2_2: Union[UnionItem, UnionItem2]
            item_or_list: Union[UnionItem, List[UnionItem]]
            item_or_list2: Union[UnionItem, List[UnionItem]]

        json_data: JsonFormat = {'value_or_item': 1, 'value_or_item2': 'test',
                                 'item_or_2': {'a': 1, 'b': 'test'}, 'item_or_2_2': {'b': 1, 'c': 'test'},
                                 'item_or_list': {'a': 1, 'b': 'test'},
                                 'item_or_list2': [{'a': 1, 'b': 'test'}, {'a': 2, 'b': 'test2'}]}
        deserialized_data: Container = from_data_to(Container, json_data)
        self.assertEqual(deserialized_data.value_or_item, 1)
        self.assertEqual(deserialized_data.value_or_item2, 'test')
        test_item_1(self, deserialized_data.item_or_2)
        self.assertEqual(deserialized_data.item_or_2_2.b, 1)
        self.assertEqual(deserialized_data.item_or_2_2.c, 'test')
        test_item_1(self, deserialized_data.item_or_list)
        test_item_list(self, deserialized_data.item_or_list2)

    def test_enum_deserialize(self):
        class MyIntEnum(IntEnum):
            A = 1
            B = auto()
            C = auto()

        class MyEnum(Enum):
            A = 'a'
            B = 'b'
            C = 'c'

        class EnumItem:
            a: int
            b: MyIntEnum
            c: MyEnum

        json_data: JsonFormat = {'a': 1, 'b': 2, 'c': 'c'}
        deserialized_data: EnumItem = from_data_to(EnumItem, json_data)
        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b, MyIntEnum.B)
        self.assertEqual(deserialized_data.c, MyEnum.C)
        self.assertTrue(isinstance(deserialized_data.b, MyIntEnum))
        self.assertTrue(isinstance(deserialized_data.c, MyEnum))

        json_data2: JsonFormat = 1
        deserialized_data2: MyIntEnum = from_data_to(MyIntEnum, json_data2)
        self.assertEqual(deserialized_data2, MyIntEnum.A)

    def test_field_deserialize(self):
        @dataclass
        class FieldItem:
            a: int = field(init=False, default=5)
            b: int = field(init=False, default=6)

        @dataclass
        class Container:
            a: int
            b: int = field(init=True)
            c: int = 3
            d: int = field(default=4)
            e: FieldItem = field(default_factory=FieldItem)

        json_data: JsonFormat = {'a': 1, 'b': 2}
        deserialized_data: Container = from_data_to(Container, json_data)
        self.assertEqual(deserialized_data.a, 1)
        self.assertEqual(deserialized_data.b, 2)
        self.assertEqual(deserialized_data.c, 3)
        self.assertEqual(deserialized_data.d, 4)
        self.assertEqual(deserialized_data.e.a, 5)
        self.assertEqual(deserialized_data.e.b, 6)

    def test_option_deserialize(self):
        true_json_data: JsonFormat = {'a': 1}
        print_log_checker: PrintLogChecker = PrintLogChecker()
        with intercept_log(lambda message: print_log_checker.set_is_printed(True)):
            true_option_data: Item = from_data_to(Item, true_json_data, checks_validation=True, includes_none=True)

        self.assertTrue(print_log_checker.is_printed)
        self.assertEqual(true_option_data.a, 1)
        self.assertEqual(true_option_data.b, None)

        class OptionContainer:
            items: List[Item]
            b: Text

        false_json_data: JsonFormat = {'items': [{'a': 1}]}
        with intercept_log(lambda message: self.assertTrue(False)):
            false_option_data: OptionContainer = from_data_to(OptionContainer, false_json_data,
                                                              checks_validation=False, includes_none=False)
        self.assertEqual(false_option_data.items[0].a, 1)
        with self.assertRaises(AttributeError):
            b: Text = false_option_data.items[0].b

        with self.assertRaises(AttributeError):
            b: Text = false_option_data.b

        @serializing_option(checks_validation=False, includes_none=False)
        class OptionContainer2:
            items: List[Item]
            b: Text

        false_json_data2: JsonFormat = {'items': [{'a': 1}]}
        with intercept_log(lambda message: self.assertTrue(False)):
            false_option_data2: OptionContainer2 = from_data_to(OptionContainer2, false_json_data2)
        self.assertEqual(false_option_data2.items[0].a, 1)
        with self.assertRaises(AttributeError):
            b: Text = false_option_data2.items[0].b

        with self.assertRaises(AttributeError):
            b: Text = false_option_data2.b

    def test_not_matched_deserialize(self):
        class Container:
            a: bool
            b: Item

        json_data: JsonFormat = {'a': True, 'b': 'test'}
        with self.assertRaises(DeserializingFailError):
            from_data_to(Container, json_data)

        json_data2: JsonFormat = {'a': 'test', 'b': {'a': 1, 'b': 'test'}}
        with self.assertRaises(InvalidAnnotationError):
            from_data_to(Container, json_data2)


@dataclass
class PrintLogChecker:
    _is_printed: bool = False

    @property
    def is_printed(self) -> bool:
        return self._is_printed

    def set_is_printed(self, is_printed: bool):
        self._is_printed = is_printed


def is_in_log(variable_name: Text, log: Text) -> bool:
    pattern: Pattern = compile(f' {variable_name}(,|$|\s)')
    return pattern.search(log) is not None


class Item:
    a: int
    b: Text


def test_item(test_case: unittest.TestCase, item: Item, **kwargs):
    for name, value in kwargs.items():
        test_case.assertEqual(getattr(item, name), value)


def test_item_1(test_case: unittest.TestCase, item: Item):
    test_item(test_case, item, a=1, b='test')


def test_item_2(test_case: unittest.TestCase, item: Item):
    test_item(test_case, item, a=2, b='test2')


def test_item_list(test_case: unittest.TestCase, items: List[Item]):
    test_item_1(test_case, items[0])
    test_item_2(test_case, items[1])


def test_item_dict_1(test_case: unittest.TestCase, items: Dict[Text, Item]):
    test_item_1(test_case, items['aa'])
    test_item_2(test_case, items['bb'])


def test_item_dict_2(test_case: unittest.TestCase, items: Dict[Text, Item]):
    test_item_1(test_case, items['cc'])
    test_item_2(test_case, items['dd'])

