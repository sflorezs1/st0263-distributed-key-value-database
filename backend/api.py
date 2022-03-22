from http import HTTPStatus
import json
import os
import dotenv

from .db import Database
from libs.singleton import Singleton


@Singleton
class API(object):

    def __init__(self):
        dotenv.load_dotenv()
        self.database = Database(
            os.getenv('SEGMENT_BASENAME', 'segment-1'),
            os.getenv('SEGMENTS_DIRECTORY', './'),
            os.getenv('WAL_BASENAME', 'memtable_bk')
        )

    def process_request(self, method):
        match method := method.path[1:] :
            case 'ping':
                return lambda *args, **kwargs: ('PONG', HTTPStatus.OK)
            case 'sync':
                return lambda *args, **kwargs: ('', HTTPStatus.OK)
            case 'query':
                return lambda *args, **kwargs: self.query(*args, **kwargs)
            case 'set':
                return lambda *args, **kwargs: self.set(*args, **kwargs)
            case _:
                return lambda *args, **kwargs: (f'Action "{method}" does not exist!',  HTTPStatus.BAD_REQUEST)

    def query(self, data=None):
        value = self.database.get(data)
        statusCode = HTTPStatus.OK if value else HTTPStatus.NOT_FOUND
        return value, statusCode

    def set(self, data=None):
        value = data
        value['value'] = bytes.fromhex(value['value'])
        key = value.pop('key', None)
        result = self.database.set(bytes.fromhex(key), value)
        statusCode = HTTPStatus.BAD_REQUEST if not result else HTTPStatus.OK
        return result, statusCode