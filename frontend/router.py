from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import re
from typing import List
from urllib.parse import urlparse
import json

from .api import API


class HTTPMethod(Enum):
    GET = 1
    POST = 2
    PUT = 3


def makeHTTPHandler(dht_lookup):
    class HTTPHandler(BaseHTTPRequestHandler):

        def __send_response(self, result, status_code) -> None:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(str(result).encode())

        def do_GET(self) -> None:
            result, status_code = API.instance(dht_lookup).process_request(urlparse(self.path), fn_arg=None)
            return self.__send_response(result, status_code)

        def do_POST(self) -> None:
            return self.__send_response(
                *self.__do_POST_or_PUT()
            )

        def do_PUT(self) -> None:
            return self.__send_response(
                *self.__do_POST_or_PUT()
            )

        def __do_POST_or_PUT(self):
            content_length = int(self.headers.get('content-length', 0))
            content_ = self.rfile.read(content_length)
            try:
                content = json.loads(content_)
            except json.JSONDecodeError:
                content = content_
            finally:
                result, status_code = API.instance(dht_lookup).process_request(urlparse(self.path), fn_arg=content)
                return result, status_code

    return HTTPHandler