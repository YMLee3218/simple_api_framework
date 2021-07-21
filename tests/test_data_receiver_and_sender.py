from asyncio import run
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Coroutine, List, Text
import unittest

from data import DataSender, DEFAULT_KEY, Response, send, to_json_from
from data.data_receiver import DataReceiver, NoReceiverError, Receiver, get_registered_receivers, register_as_receiver
from json_data import DeserializingFailError, JsonFormat, SerializingFailError
from logger import intercept_log


class TestReceiver(DataReceiver):
    def route(self, receive: Callable[[JsonFormat, Text], Coroutine[Any, Any, JsonFormat]], **kwargs):
        sender: TestSender = kwargs['sender']
        sender.route(receive)


class TestSender(DataSender):
    send: Callable[[JsonFormat, Text, Any], Coroutine[Any, Any, JsonFormat]]

    def route(self, receive: Callable[[JsonFormat, Text], Coroutine[Any, Any, JsonFormat]]):
        async def new_send(data: JsonFormat, key: Text = DEFAULT_KEY, **kwargs) -> JsonFormat:
            return await receive(data, key)

        self.send = new_send


class TestDataReceiver(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sender: TestSender = TestSender()
        cls.send = partial(send, cls.sender)

    def test_single_receiver(self):
        receiver: Receiver = Receiver(get_increased_data)
        TestReceiver(receiver, sender=self.sender)

        input_: TestData = TestData(1, 'test')
        expected: TestData = TestData(2, 'test2')
        actual, error = run(self.send(input_, TestData))
        response: Response = run(self.send(input_, TestData))

        self.assertEqual(actual, expected)
        self.assertEqual(response.instance, expected)

    def test_no_annotation_receiver(self):
        input_: TestData = TestData(1, 'test')

        def get_and_return_no_annotation(item):
            self.assertEqual(item, to_json_from(input_))
            return item

        receiver: Receiver = Receiver(get_and_return_no_annotation)
        TestReceiver(receiver, sender=self.sender)

        run(self.send(input_, TestData))

    def test_duplicate_key_receiver(self):
        receiver: Receiver = Receiver(get_increased_data)
        TestReceiver(receiver, receiver, sender=self.sender)

        input_: TestData = TestData(1, 'test')
        expected: List[TestData] = [TestData(2, 'test2'), TestData(2, 'test2')]
        actual, error = run(self.send(input_, TestData))

        self.assertEqual(actual, expected)

    def test_error_handling(self):
        def raise_exception(target: TestData) -> None:
            raise Exception("Error is occurred!")

        receiver: Receiver = Receiver(raise_exception)
        TestReceiver(receiver, sender=self.sender)

        input_: TestData = TestData(1, 'test')
        with intercept_log(lambda message: self.assertTrue(0 <= message.find("Error is occurred!"))):
            actual, error = run(self.send(input_, TestData))

        self.assertEqual(error.exception, Exception.__name__)

    def test_no_receiver(self):
        TestReceiver(sender=self.sender)

        input_: TestData = TestData(1, 'test')
        with intercept_log(lambda message: self.assertTrue(0 <= message.find("no receiver"))):
            actual, error = run(self.send(input_, TestData))

        self.assertEqual(error.exception, NoReceiverError.__name__)

    def test_serialize_fail(self):
        @dataclass
        class InvalidData:
            a: Callable

        def pass_data(target: InvalidData) -> Any:
            return target

        receiver: Receiver = Receiver(pass_data)
        TestReceiver(receiver, sender=self.sender)

        input_: TestData = TestData(1, 'test')
        with intercept_log(lambda message: self.assertTrue(0 <= message.find("Fail to deserialize"))):
            actual, error = run(self.send(input_, TestData))

        self.assertEqual(error.exception, DeserializingFailError.__name__)

        input_2: InvalidData = InvalidData(print)
        try:
            run(self.send(input_2, InvalidData))
        except SerializingFailError:
            pass
        except Exception as e:
            self.assertEqual(type(e).__name__, SerializingFailError.__name__)

    def test_register_as_receiver(self):
        @register_as_receiver
        def get_increased_data2(target: TestData) -> TestData:
            return TestData(target.a + 1, f'{target.b}2')

        @register_as_receiver('test')
        def get_increased_data3(target: TestData) -> TestData:
            return TestData(target.a + 2, f'{target.b}3')

        TestReceiver(*get_registered_receivers(), sender=self.sender)

        input_: TestData = TestData(1, 'test')
        expected: TestData = TestData(2, 'test2')
        expected2: TestData = TestData(3, 'test3')

        actual, error = run(self.send(input_, TestData))
        actual2, error2 = run(self.send(input_, TestData, 'test'))

        self.assertEqual(actual, expected)
        self.assertEqual(actual2, expected2)


@dataclass
class TestData:
    a: int
    b: Text

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b


def get_increased_data(target: TestData) -> TestData:
    return TestData(target.a + 1, f'{target.b}2')
