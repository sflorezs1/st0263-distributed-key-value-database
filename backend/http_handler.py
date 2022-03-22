from enum import Enum
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
import socketserver

from .api import API


class HTTPMethod(Enum):
    GET = 1
    POST = 2
    PUT = 3


class HTTPHandler(BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer) -> None:
        super().__init__(request, client_address, server)

    def __send_response(self, result, status_code) -> None:
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(str(result).encode())

    def do_GET(self) -> None:
        result, status_code = API.instance().process_request(urlparse(self.path))()
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
            result, status_code = API.instance().process_request(urlparse(self.path))(content)
            return result, status_code
