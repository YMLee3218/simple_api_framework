from dataclasses import dataclass
from typing import Any, Dict, Text, Type
import unittest

from slotdataclass import slotdataclass


class TestSlotdataclass(unittest.TestCase):
    def test_slot(self):
        @slotdataclass
        class SlotClass:
            a: int
            b: Text

        test_all(self, SlotClass)

    def test_slot_data(self):
        @slotdataclass
        @dataclass
        class SlotAndDataClass:
            a: int
            b: Text

        @dataclass
        @slotdataclass
        class DataAndSlotClass:
            a: int
            b: Text

        test_all(self, SlotAndDataClass)
        test_all(self, DataAndSlotClass)

    def test_empty_data(self):
        @slotdataclass
        class EmptyData:
            pass

        data: EmptyData = EmptyData()

    def test_slot_slot(self):
        @slotdataclass
        @slotdataclass
        class SlotSlotClass:
            a: int
            b: Text

        test_all(self, SlotSlotClass)


def test_all(test_case: unittest.TestCase, target_class: Type):
    test_initialize(test_case, target_class)
    test_no_dict(test_case, target_class)
    test_to_use(test_case, target_class)


def test_initialize(test_case: unittest.TestCase, target_class: Type):
    with test_case.assertRaises(TypeError):
        data: target_class = target_class()

    data: target_class = target_class(1, 'asdf')


def test_no_dict(test_case: unittest.TestCase, target_class: Type):
    data: target_class = target_class(1, 'asdf')
    with test_case.assertRaises(AttributeError):
        dict_in_data: Dict[Text, Any] = data.__dict__


def test_to_use(test_case: unittest.TestCase, target_class: Type):
    data: target_class = target_class(1, 'asdf')
    test_case.assertEqual(data.a, 1)
    test_case.assertEqual(data.b, 'asdf')
