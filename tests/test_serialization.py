from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Callable, Dict, List, NamedTuple, Text
import unittest

from json_data import JsonFormat, JsonList, JsonObject, SerializingFailError
from json_data import to_json_from
from slotdataclass import slotdataclass


class TestSerialization(unittest.TestCase):
    def test_value_serialize(self):
        item: int = 1
        serialized_data: JsonFormat = to_json_from(item)
        self.assertEqual(serialized_data, 1)

    def test_1_dimension_serialize(self):
        item: Item = Item(1, 'test')
        serialized_data: JsonFormat = to_json_from(item)
        test_item_1(self, serialized_data)

    def test_dict_serialize(self):
        class DictItem:
            def __init__(self, a: int, b: Text):
                self.a: int = a
                self.b: Text = b

        item: DictItem = DictItem(1, 'test')
        serialized_data: JsonFormat = to_json_from(item)
        test_item_1(self, serialized_data)

    def test_slots_serialize(self):
        class SlotsItem:
            __slots__ = ('a', 'b')

            def __init__(self, a: int, b: Text):
                self.a: int = a
                self.b: Text = b

        item: SlotsItem = SlotsItem(1, 'test')
        serialized_data: JsonFormat = to_json_from(item)
        test_item_1(self, serialized_data)

        @slotdataclass
        @dataclass
        class SlotDataItem:
            a: int
            b: Text

        item2: SlotDataItem = SlotDataItem(1, 'test')
        serialized_data2: JsonFormat = to_json_from(item2)
        test_item_1(self, serialized_data2)

    def test_named_tuple_serialize(self):
        class NamedTupleItem(NamedTuple):
            a: int
            b: Text

        item: NamedTupleItem = NamedTupleItem(1, 'test')
        serialized_data: JsonFormat = to_json_from(item)
        test_item_1(self, serialized_data)

    def test_list_serialize(self):
        items: List[Item] = [Item(1, 'test'), Item(2, 'test2')]
        serialized_data: JsonFormat = to_json_from(items)
        test_item_list(self, serialized_data)

    def test_derived_serialize(self):
        @dataclass
        class Derived(Item):
            b: int
            c: Text

        item: Derived = Derived(1, 2, 'test')
        serialized_data: JsonFormat = to_json_from(item)
        self.assertEqual(serialized_data, {'a': 1, 'b': 2, 'c': 'test'})

    def test_item_in_object_serialize(self):
        @dataclass
        class Container:
            item: Item
            id: int

        item: Container = Container(Item(1, 'test'), 0)
        serialized_data: JsonFormat = to_json_from(item)
        test_item_1(self, serialized_data['item'])
        self.assertEqual(serialized_data['id'], 0)

    def test_items_in_list_serialize(self):
        @dataclass
        class ItemList:
            items: List[Item]
            items_in_items: List[List[Item]]
            id: int

        item: ItemList = ItemList([Item(1, 'test'), Item(2, 'test2')],
                                  [[Item(1, 'test'), Item(2, 'test2')], [Item(1, 'test'), Item(2, 'test2')]],
                                  0)
        serialized_data: JsonFormat = to_json_from(item)

        test_item_list(self, serialized_data['items'])
        for items in serialized_data['items_in_items']:
            test_item_list(self, items)

        self.assertEqual(serialized_data['id'], 0)

    def test_items_in_dict_deserialize(self):
        @dataclass
        class ItemDict:
            text_item: Dict[Text, Item]
            text_item_list: Dict[Text, List[Item]]
            dict_list: List[Dict[Text, Item]]
            id: int

        item: ItemDict = ItemDict({'aa': Item(1, 'test'), 'bb': Item(2, 'test2')},
                                  {'aa': [Item(1, 'test'), Item(2, 'test2')],
                                   'bb': [Item(1, 'test'), Item(2, 'test2')]},
                                  [{'aa': Item(1, 'test'), 'bb': Item(2, 'test2')},
                                   {'cc': Item(1, 'test'), 'dd': Item(2, 'test2')}], 0)
        serialized_data: JsonFormat = to_json_from(item)

        test_item_dict_1(self, serialized_data['text_item'])
        test_item_list(self, serialized_data['text_item_list']['aa'])
        test_item_list(self, serialized_data['text_item_list']['bb'])
        test_item_dict_1(self, serialized_data['dict_list'][0])
        test_item_dict_2(self, serialized_data['dict_list'][1])
        self.assertEqual(serialized_data['id'], 0)

    def test_dict_deserialize(self):
        item: Dict[Text, Any] = {'a': 1, 'b': 'test'}
        serialized_data: Dict[Text, Any] = to_json_from(item)
        self.assertEqual(serialized_data['a'], 1)
        self.assertEqual(serialized_data['b'], 'test')

    def test_enum_serialize(self):
        class MyEnum(IntEnum):
            A = 1
            B = auto()
            C = auto()

        @dataclass
        class EnumItem:
            a: int
            b: MyEnum

        item: EnumItem = EnumItem(1, MyEnum.B)
        serialized_data: JsonFormat = to_json_from(item)
        self.assertEqual(serialized_data['a'], 1)
        self.assertEqual(serialized_data['b'], MyEnum.B.value)
        self.assertTrue(isinstance(serialized_data['b'], int))

        item2: MyEnum = MyEnum.A
        serialized_data2: int = to_json_from(item2)
        self.assertEqual(serialized_data2, MyEnum.A.value)

    def test_no_serializable_value(self):
        @dataclass
        class NoSerializableItem:
            a: int
            b: Callable

        item: NoSerializableItem = NoSerializableItem(1, print)
        with self.assertRaises(SerializingFailError):
            to_json_from(item)


@dataclass
class Item:
    a: int
    b: Text


def test_item_1(test_case: unittest.TestCase, item: JsonObject):
    test_case.assertEqual(item, {'a': 1, 'b': 'test'})


def test_item_2(test_case: unittest.TestCase, item: JsonObject):
    test_case.assertEqual(item, {'a': 2, 'b': 'test2'})


def test_item_list(test_case: unittest.TestCase, items: JsonList):
    test_item_1(test_case, items[0])
    test_item_2(test_case, items[1])


def test_item_dict_1(test_case: unittest.TestCase, items: JsonObject):
    test_item_1(test_case, items['aa'])
    test_item_2(test_case, items['bb'])


def test_item_dict_2(test_case: unittest.TestCase, items: JsonObject):
    test_item_1(test_case, items['cc'])
    test_item_2(test_case, items['dd'])
