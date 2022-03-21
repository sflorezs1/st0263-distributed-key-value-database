from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from urllib.parse import urlparse
import json
import socketserver

from .api import API


class HTTPMethod(Enum):
    GET = 1
    POST = 2
    PUT = 3


class HTTPHandler(BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer, api: API) -> None:
        super().__init__(request, client_address, server)
        self.__api = api

    def __send_response(self, result, status_code) -> None:
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(result)

    def do_GET(self) -> None:
        return self.__send_response(
            *self.__api.process_request(urlparse(self.path))()
        )

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
        content = json.loads(self.rfile.read(content_length))
        result, status_code = self.__api.process_request(urlparse(self.path))(**{
            'data': content
        })
        return result, status_code