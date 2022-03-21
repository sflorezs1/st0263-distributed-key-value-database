from http import HTTPStatus
from ..backend import Database


class API(object):
    """
    Defines the public APIs for the http Server
    """

    def __init__(self):
        self.database = Database()

    def process_request(self, method):
        match method:
            case 'fetch':
                return lambda *args, **kwargs: self.fetch(self, *args, **kwargs)
            case 'query':
                return lambda *args, **kwargs: self.query(self, *args, **kwargs)
            case 'set':
                return lambda *args, **kwargs: self.set(self, *args, **kwargs)
            case _:
                return lambda *args, **kwargs: HTTPStatus.BAD_REQUEST, f'Action "{method}" does not exist!'

    def fetch(self):
        """
        Path: /fetch
        Method: GET - to get all
        """
        status_code = HTTPStatus.IM_A_TEAPOT
        result = None
        try:
            result = self.database.fetch()
        except Exception as e:
            print(e)
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            return result, status_code

    def query(self, data=None):
        keys = self.database.query(**{"data": data})
        keysFound = filter(lambda k: k["value"] == True, keys)
        statusCode = HTTPStatus.OK if len(keysFound) == len(keys) else HTTPStatus.NOT_FOUND
        return keys, statusCode

    def set(self, data=None):
        keysAdded, keysFailed = self.database.set(**{"data": data})
        result = {
            "keys_added": keysAdded,
            "keys_failed": keysFailed
        }
        statusCode = HTTPStatus.BAD_REQUEST if keysFailed else HTTPStatus.OK
        return result, statusCode