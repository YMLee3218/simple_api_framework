from aiohttp import ClientSession, ClientResponse
from functools import lru_cache
from typing import Text

from concrete import concrete
from data import DEFAULT_KEY, HTTPStatusError, JsonFormat
from data.data_sender import DataSender

URL_PARAMETER: Text = 'url'


@concrete
class AIOHTTPDataSender(DataSender):
    async def send(self, data: JsonFormat, key: Text = DEFAULT_KEY, **kwargs) -> JsonFormat:
        if URL_PARAMETER not in kwargs:
            raise URLNotFoundError()

        url: Text = kwargs[URL_PARAMETER]
        key_url: Text = _get_key_url(url, key)
        async with ClientSession() as session:
            async with session.post(key_url, json=data) as response:
                return await _get_data(response)


async def _get_data(response: ClientResponse) -> JsonFormat:
    if 400 <= response.status:
        raise HTTPStatusError(response.status)

    return await response.json()


@lru_cache
def _get_key_url(base_url: Text, key: Text) -> Text:
    if key == DEFAULT_KEY:
        return base_url

    return f"{base_url if base_url[-1] != '/' else base_url[0:-1]}/{key}"


class URLNotFoundError(Exception):
    def __init__(self):
        self.message: Text = (f"Cannot find url in arguments. "
                              f"{AIOHTTPDataSender.__name__} must receive 'url' as argument.")

    def __str__(self) -> Text:
        return self.message
