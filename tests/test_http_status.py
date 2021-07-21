import unittest

from data import HTTPStatus, HTTPStatusError, StatusInfo

NAME_OF_405_ERROR: str = "Method Not Allowed"


class TestHTTPStatus(unittest.TestCase):

    def test_get_status_info(self):
        info: StatusInfo = HTTPStatus[405]
        self.assertEqual(info.name, NAME_OF_405_ERROR)

    def test_http_status_error(self):
        error: HTTPStatusError = HTTPStatusError(405)
        error.message.find(NAME_OF_405_ERROR)
