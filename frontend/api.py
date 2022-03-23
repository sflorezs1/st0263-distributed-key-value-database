from http import HTTPStatus
from re import L
from typing import List
import requests

from libs.singleton import Singleton

@Singleton
class API(object):

    def __init__(self, dht_lookup):
        self.dht_lookup = dht_lookup

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

    def search_partion(self, key):
        for (start, end), node in self.dht_lookup.items():
            if start <= key <= end:
                return node
        return None

    def query(self, data=None):
        key = bytes.fromhex(data.decode())
        node = self.search_partion(key)
        if not node:
            return '', HTTPStatus.BAD_REQUEST
        res = requests.post(f'http://{node}/query', data=data)
        return res.json(), res.status_code

    def set(self, data=None):
        value = data
        key = bytes.fromhex(value['key'])
        node = self.search_partion(key)
        if not node:
            return '', HTTPStatus.BAD_REQUEST
        res = requests.put(f'http://{node}/set', json=value)
        return res.text, res.status_code
    
    