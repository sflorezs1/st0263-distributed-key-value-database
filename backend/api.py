from http import HTTPStatus
import json
import os
import dotenv
import requests

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
        self.replicas = [None]
        self.current_replica_index = 0
        self.master_mode = os.getenv('DB_NODE_MODE') == 'master'

    def process_request(self, method, fn_arg):
        match method := method.path[1:] :
            case 'ping':
                return ('PONG', HTTPStatus.OK)
            case 'subscribe': #  Asked to be added as a slave
                if self.master_mode:
                    self.replicas.append(f"{fn_arg['ip']}:{fn_arg['port']}")
                    return 'Subscribed', HTTPStatus.OK
                else:
                    return 'I am not a master', HTTPStatus.IM_A_TEAPOT
            case 'query':
                if self.master_mode:
                    # Operate via a round robin
                    # not the best solution but should help
                    if self.current_replica_index == 0 or len(self.replicas) == 1:
                        self.current_replica_index = (self.current_replica_index + 1) % len(self.replicas)
                        return self.query(fn_arg)
                    else:
                        n = self.current_replica_index
                        self.current_replica_index = (self.current_replica_index + 1) % len(self.replicas)
                        return (str(self.replicas[n]), HTTPStatus.TEMPORARY_REDIRECT)
            case 'set':
                result = self.set(fn_arg)
                with requests.Session() as r:
                    for replica in self.replicas[1:]:
                        res = r.put(f'http://{ replica }/set', data=fn_arg)
                        if res.ok:
                            print(f'Replica { replica } synced!')
                return result
            case _:
                return (f'Action "{method}" does not exist!',  HTTPStatus.BAD_REQUEST)


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