from datetime import datetime
from typing import Dict
from copy import deepcopy

class Database(object):
    
    def __init__(self, db: Dict[bytes, Dict[str, str | bytes]], serialization_path: str) -> None:
        self.db: Dict[bytes, Dict[str, str | bytes]] = deepcopy(db)
        self.serialization_path: str = serialization_path

    def serialize(self):
        now = str(datetime.now())
        with open(self.serialization_path + now + '.db.bk', 'wb') as file:
            pass
        
        

