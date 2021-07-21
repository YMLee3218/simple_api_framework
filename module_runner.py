from importlib import import_module
from typing import Any, Dict, List, Text

from data import DataReceiver, RECEIVER_KEY, Receiver, SENDER_KEY, get_registered_receivers, pass_sender_arguments
from argument_getter import get_arguments


def run(module_name: Text):
    import_module(module_name)

    receivers: List[Receiver] = get_registered_receivers()
    receiver_arguments: Dict[Text, Any] = get_arguments(RECEIVER_KEY)
    data_receiver: DataReceiver = DataReceiver(*receivers, **receiver_arguments)

    sender_arguments: Dict[Text, Any] = get_arguments(SENDER_KEY)
    pass_sender_arguments(**sender_arguments)
