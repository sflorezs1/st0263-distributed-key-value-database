from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from unittest import result
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

    def __process_request(self, method: HTTPMethod) -> None:
        parsed_path = urlparse(self.path)

        match method:
            case HTTPMethod.GET:
                result, status_code = self.__api.process_request(parsed_path)()
            case (HTTPMethod.POST | HTTPMethod.PUT):
                content_length = int(self.headers.get('content-length', 0))
                content = json.loads(self.rfile.read(content_length))
                result, status_code = self.__api.process_request(parsed_path)(**{
                    'data': content
                })
            case _:
                result, status_code = {
                    'message': 'Error, invalid method!',
                }, HTTPStatus.BAD_REQUEST
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(result)
        

    def do_GET(self) -> None:
        self.__process_request(HTTPMethod.GET)

    def do_POST(self) -> None:
        self.__process_request(HTTPMethod.POST)

    def do_PUT(self) -> None:
        self.__process_request(HTTPMethod.PUT)