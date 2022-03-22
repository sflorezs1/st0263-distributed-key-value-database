from http import HTTPStatus
import json
import os
import dotenv
import requests

from backend.db import Database
from libs.singleton import Singleton