from http import HTTPStatus
from typing import List
import requests

from libs.singleton import Singleton

@Singleton
class API(object):

    def __init__(self, nodes: List[str]):
        self.nodes = nodes

    def process_request(self, method, fn_arg):
        match method := method.path[1:]:
            case 'ping':
                return ('PONG', HTTPStatus.OK)
            case 'query':
                return self.query(fn_arg)
            case 'set':
                return self.set(fn_arg)
            case _:
                return (f'Action "{method}" does not exist!',  HTTPStatus.BAD_REQUEST)

    def query(self, fn_arg):
        
        pass

    def set(self, fn_arg):
        pass
