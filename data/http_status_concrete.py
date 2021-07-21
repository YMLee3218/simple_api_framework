from data.http_status import _HTTPStatusListBase

from concrete import concrete


@concrete
class HTTPStatusList(_HTTPStatusListBase):
    BAD_REQUEST = (400, "Bad Request", "The server could not understand the request due to invalid syntax.")
    UNAUTHORIZED = (401, "Unauthorized", "The client must authenticate itself to get the requested response.")
    FORBIDDEN = (403, "Forbidden", "The client does not have access rights to the content.")
    NOT_FOUND = (404, "Not Found", "The server can not find the requested resource.")
    METHOD_NOT_ALLOWED = (405, "Method Not Allowed", "The request method is not supported for the requested resource.")
    NOT_ACCEPTABLE = (406, "Not Acceptable", "The requested resource is capable of generating only content not "
                                             "acceptable according to the Accept headers sent in the request.")
    PROXY_AUTHENTICATION_REQUIRED = (407, "Proxy Authentication Required",
                                     "The client must first authenticate itself with the proxy.")
    REQUEST_TIMEOUT = (408, "Request Timeout", "The server timed out waiting for the request.")
    CONFLICT = (408, "Conflict", "The request could not be processed because of conflict in the current state "
                                 "of the resource.")
