from typing import Dict, Optional

from libs.lsm_tree import LSMTree
from libs.types import Value


class Database(object):
    
    def __init__(self, segment_basename: str, segments_directory: str, wal_basename: str) -> None:
        self.db: LSMTree = LSMTree(segment_basename, segments_directory, wal_basename)
    
    def get(self, key: bytes) -> Optional[str]:
        val = self.db.db_get(key)
        return self.db.serialize_value(val) if val else val
    
    def set(self, key: bytes, value: Value) -> None:
        try:
            self.db.db_set(key, value)
            return True
        except Exception as e:
            print(e)
            return False
        
        

