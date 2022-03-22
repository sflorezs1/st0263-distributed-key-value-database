from http import HTTPStatus
import json
import os
import dotenv
import requests
import mmh3

from backend.db import Database
from libs.singleton import Singleton


class Client:
    def __init__(self, host, port) -> None:
        # frontend
        self.host = host
        self.port = port

        # ping front
        res = requests.get(f'http://{host}:{port}/ping')
        if not res.ok:
            print('FATHER is dead')
            raise Exception("Server is down or not running the software!")
        

    def get(self, key):
        hash_key = mmh3.hash_bytes(key)
        res = requests.post(f'http://{self.host}:{self.port}/query', data=hash_key.hex())
        if res.ok:
            return res.text
        else:
            return None
    
    
