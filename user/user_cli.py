from http import HTTPStatus
import json
import os
import this
import dotenv
import requests
import mmh3



class YADDBClient:
    def __init__(self, host, port) -> None:
        # frontend
        self.host = host
        self.port = port

        # ping front
        res = requests.get(f'http://{host}:{port}/ping')
        if not res.ok:
            print('FATHER is dead')
            raise Exception("Server is down or not running the software!")
        

    def read(self, key):
        hash_key = mmh3.hash_bytes(key)
        res = requests.post(f'http://{self.host}:{self.port}/query', data=hash_key.hex())
        if res.ok:
            response=res.json()
            response['value']=bytes.fromhex(response['value'])
            return response
        else:
            return None

    def write(self, key, value,content_type,encoding):
        hash_key = mmh3.hash_bytes(key)

        data = {
            "key": hash_key.hex(),
            "content_type": content_type,
            "encoding": encoding,
            "value": value.hex()
            }

        res = requests.put(f'http://{self.host}:{self.port}/set', json=data)
        if res.ok:
            return res.text
        else:
            return None

    
    
