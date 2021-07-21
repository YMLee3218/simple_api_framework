from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, json
from typing import Any, Callable, Coroutine, Text

from concrete import concrete
from data import DEFAULT_KEY
from data.data_receiver import DataReceiver, RECEIVER_KEY
from argument_getter import add_argument
from json_data import JsonFormat

URL_PARAMETER: Text = 'url'
HOST_PARAMETER: Text = 'host'
PORT_PARAMETER: Text = 'port'

add_argument(RECEIVER_KEY, URL_PARAMETER, default='/')
add_argument(RECEIVER_KEY, HOST_PARAMETER, default='0.0.0.0')
add_argument(RECEIVER_KEY, PORT_PARAMETER, default=8000, type_converter=int, description="port to run server")


@concrete
class SanicDataReceiver(DataReceiver):
    def route(self, receive: Callable[[JsonFormat, Text], Coroutine[Any, Any, JsonFormat]], **kwargs):
        def handle(request: Request, key: Text) -> Coroutine[Any, Any, HTTPResponse]:
            return _handle_to(request, receive, key)
        app: Sanic = Sanic("Sanic Data Receiver")

        app.post(kwargs[URL_PARAMETER])(lambda request: handle(request, DEFAULT_KEY))
        key_url: Text = _get_key_url(kwargs[URL_PARAMETER])
        app.post(key_url)(handle)

        del kwargs[URL_PARAMETER]
        app.run(**kwargs)


def _get_key_url(base_url: Text) -> Text:
    return f"{base_url if base_url[-1] != '/' else base_url[0:-1]}/<key>"


async def _handle_to(request: Request, receive: Callable[[JsonFormat, Text], Coroutine[Any, Any, JsonFormat]],
                     key: Text) -> HTTPResponse:
    response: JsonFormat = await receive(request.json, key)
    return json(response)
