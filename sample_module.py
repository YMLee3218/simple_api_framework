from dataclasses import dataclass
from typing import NamedTuple, Text

from data import ResponseError, register_as_receiver, send
from slotdataclass import slotdataclass


RECEIVER2_KEY: Text = "Receive2"


class MyItem(NamedTuple):
    a: int
    b: Text


@slotdataclass
@dataclass
class MyItem2:
    c: int
    d: int


@register_as_receiver
async def receive1(item: MyItem) -> MyItem:
    item2: MyItem2
    error: ResponseError
    item2, error = await send(item, MyItem2, RECEIVER2_KEY, url="http://127.0.0.1:8000/")
    print(f"Error: {error}")

    return MyItem(item.a + item2.c, f"{item.b}: length is {item2.d}")


@register_as_receiver(RECEIVER2_KEY)
def receive2(item: MyItem) -> MyItem2:
    return MyItem2(item.a + 1, len(item.b))


@register_as_receiver(RECEIVER2_KEY)
def receive2_error(item: MyItem) -> MyItem2:
    raise Exception("Error is occurred!")
