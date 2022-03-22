from typing import Any

from .singleton import Singleton


@Singleton
class AppendLog(object):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.stream = open(filename, 'a')

    def write(self, val: str) -> None:
        try:
            self.stream.write(val)
            self.stream.flush()
        except IOError:
            print('The file isn\'t currently open')
    
    def clear(self) -> None:
        self.stream = open(self.filename, 'w')
