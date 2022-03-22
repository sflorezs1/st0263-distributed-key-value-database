# Original code adapted from: https://github.com/chrislessard/LSM-Tree/blob/master/src/lsm_tree.py

from copy import deepcopy
from operator import le
import pickle
from pathlib import Path
from typing import List, Optional
import json
from os import remove as remove_file, rename as rename_file

from libs.red_black_tree import RedBlackTree
from libs.bloom_filter import CountingBloomFilter
from libs.types import Value
from libs.append_log import AppendLog


class LSMTree(object):

    def __init__(self, segment_basename: str, segments_directory: str, wal_basename: str, threshold: int = 1000000, sparcity_factor: int = 100) -> None:
        self.segments_directory: str = segments_directory
        self.wal_basename: str = wal_basename
        self.current_segment = segment_basename
        self.segments: List[str] = []

        self.threshold: int = threshold #  in bytes
        self.memtable: RedBlackTree = RedBlackTree()

        self.index: RedBlackTree = RedBlackTree()
        self.sparcity_factor: int = sparcity_factor

        self.bf_num_items: int = 1000000
        self.bf_false_pos_prob: int = 0.2
        self.bloom_filter: CountingBloomFilter = CountingBloomFilter(self.bf_num_items, self.bf_false_pos_prob)

        if not (Path(segments_directory).exists() and Path(segments_directory).is_dir()):
            Path(segments_directory).mkdir(parents=True)

        if not self.load_past_state():
            self.save_state()
        self.restore_memtable()

    def db_set(self, key: bytes, value: Value) -> None:
        log = self.to_log_entry(key, value)
        node = self.memtable.find_node(key)
        if node:
            self.memtable_wal().write(log)
            node.value = value
            return
        
        additional_size = len(key) + len(self.serialize_value(value))
        if self.memtable.total_bytes + additional_size > self.threshold:
            self.flush_memtable_to_disk(self.current_segment_path())
            self.save_state()
            self.memtable = RedBlackTree()
            self.memtable_wal().clear()

            self.segments.append(self.current_segment)
            new_segment_name = self.incremented_segment_name()
            self.current_segment = new_segment_name
            self.memtable.total_bytes = 0
        
        self.memtable_wal().write(log)

        self.memtable.add(key, value)
        self.memtable.total_bytes += additional_size

    def db_get(self, key: bytes) -> Value:
        node = self.memtable.find_node(key)
        if node:
            return node.value
        if not self.bloom_filter.check(key):
            return None
        floor_val = self.index.floor(key)
        floor_node = self.index.find_node(floor_val)

        if floor_node:
            path = self.segment_path(floor_node.segment)
            with open(path, 'r') as segment_file:
                segment_file.seek(floor_node.offset)
                for line in segment_file:
                    s_key, value = line.strip().split(',', 1)
                    s_key = bytes.fromhex(s_key)
                    if key == s_key:
                        value = json.loads(value)
                        value['value'] = bytes.fromhex(value['value'])
                        return value
        return self.search_all_segments(key)

    def set_threshold(self, threshold: int) -> None:
        self.threshold = threshold
    
    def set_sparcity_factor(self, factor: int) -> None:
        self.sparcity_factor = factor
    
    def memtable_wal(self) -> AppendLog:
        return AppendLog.instance(self.memtable_wal_path())

    def search_all_segments(self, key: bytes) -> Optional[Value]:
        segments: List[str] = self.segments[:]
        while segments:
            segment: str = segments.pop()
            value = self.search_segment(key, segment)
            if value:
                return value

    def search_segment(self, key: bytes, segment_name: str) -> Optional[Value]:
        with open(self.segment_path(segment_name), 'r') as segment_file:
            pairs = [line.strip() for line in segment_file]
            while pairs:
                ptr = (len(pairs) - 1) // 2
                k, v = pairs[ptr].split(',', 1)

                k = bytes.fromhex(k)

                if k == key:
                    v = json.loads(v)
                    v['value'] = bytes.fromhex(v['value'])
                    return v
                
                if key < k:
                    pairs = pairs[:ptr]
                else:
                    pairs = pairs[ptr + 1:]
    
    def load_past_state(self):
        if Path(self.past_state_path()).exists():
            with open(self.past_state_path(), 'rb') as state_file:
                state = pickle.load(state_file)
                self.segments = state['segments']
                self.current_segment = state['current_segment']
                self.bloom_filter = state['bloom_filter']
                self.bf_num_items = state['bf_num_items']
                self.bf_false_pos_prob = state['bf_false_pos_prob']
                self.index = state['index']
            return True
        else:
            return False
    
    def save_state(self):
        state = {
            'current_segment': self.current_segment,
            'segments': self.segments,
            'bloom_filter': self.bloom_filter,
            'bf_num_items': self.bf_num_items,
            'bf_false_pos_prob': self.bf_false_pos_prob,
            'index': self.index
        }

        with open(self.past_state_path(), 'wb') as state_file:
            pickle.dump(state, state_file)
    
    def restore_memtable(self):
        if Path(self.memtable_wal_path()).exists():
            with open(self.memtable_wal_path(), 'r') as memtable_file:
                for line in memtable_file:
                    key, value = line.strip().split(',', 1)
                    key = bytes.fromhex(key)
                    value = json.loads(value)
                    value['value'] = bytes.fromhex(value['value'])
                    self.memtable.add(key, value)
                    self.memtable.total_bytes += len(line)
    
    def flush_memtable_to_disk(self, path: str):
        sparcity_counter = self.sparcity()

        key_offset: int = 0

        with open(path, 'w') as file:
            for node in self.memtable.in_order_traversal():
                log = self.to_log_entry(node.key, node.value)

                if sparcity_counter == 1:
                    # Do not store value in an index!!!!!!!!
                    self.index.add(node.key, None, offset=key_offset, segment=self.current_segment)
                    sparcity_counter = self.sparcity() + 1
        
                self.bloom_filter.add(node.key)
                file.write(log)
                key_offset += len(log)
                sparcity_counter -= 1
    
    def serialize_value(self, value: Value) -> str:
        j_value = deepcopy(value)
        j_value['value'] = value['value'].hex()
        return str(json.dumps(j_value))

    def to_log_entry(self, key: bytes, value: Value) -> str:
        return f'{key.hex()}, {self.serialize_value(value)}\n'

    def incremented_segment_name(self) -> str:
        name, number = self.current_segment.split('-')
        new_number: int = str(int(number) + 1)

        return f'{name}-{new_number}'

    def merge(self, segment_a, segment_b) -> None:
        path_a = Path.joinpath(Path(self.segments_directory), segment_a)
        path_b = Path.joinpath(Path(self.segments_directory), segment_b)
        new_path = Path.joinpath(Path(self.segments_directory), 'temp')

        with open(new_path, 'w') as temp:
            with open(path_a, 'r') as file_a:
                with open(path_b, 'r') as file_b:
                    line_a, line_b = file_a.readline(), file_b.readline()
                    while line_a != '' or line_b != '':
                        key_a = bytes.fromhex(line_a.strip().split(',', 1)[0])
                        key_b = bytes.fromhex(line_b.strip().split(',', 1)[0])
                        if key_a == '' or key_b == key_a:
                            temp.write(line_b)
                            line_a, line_b = file_a.readline(), file_b.readline()
                        elif key_b == '' or key_a < key_b:
                            temp.write(line_a)
                            line_a = file_a.readline()
                        else:
                            temp.write(line_b)
                            line_b = file_b.readline()
        
        remove_file(path_a)
        remove_file(path_b)
        rename_file(new_path, path_a)

        return segment_a

    def get_file_size(self, path: str) -> int:
        return Path(path).stat().st_size
    
    def sparcity(self) -> int:
        return self.threshold // self.sparcity_factor
    
    def repopulate_index(self) -> None:
        self.index = RedBlackTree()
        for segment in self.segments:
            path = self.segment_path(segment)
            counter = self.sparcity()
            n_bytes: int = 0
            with open(path, 'r') as segment_file:
                for line in segment_file:
                    key, value = line.strip().split(',', 1)
                    key = bytes.fromhex(key)
                    value = json.loads(value)
                    value['value'] = bytes.fromhex(value['value'])
                    if counter == 1:
                        self.index.add(key, value, offset=bytes, segment=segment)
                        counter = self.sparcity() + 1
                    n_bytes += len(line)
                    counter -= 1
    
    def set_bloom_filter_num_items(self, num_items: int) -> None:
        self.bf_num_items = num_items
        self.bloom_filter = CountingBloomFilter(self.bf_num_items, self.bf_false_pos_prob)

    def set_bloom_filter_false_pos_prob(self, false_pos_prob: int) -> None:
        self.bf_false_pos_prob = false_pos_prob
        self.bloom_filter = CountingBloomFilter(self.bf_num_items, self.bf_false_pos_prob)

    def current_segment_path(self) -> str:
        return Path.joinpath(Path(self.segments_directory), self.current_segment)

    def memtable_wal_path(self) -> str:
        return Path.joinpath(Path(self.segments_directory), self.wal_basename)

    def segment_path(self, segment_name: str) -> str:
        return Path.joinpath(Path(self.segments_directory), segment_name)
    
    def past_state_path(self) -> str:
        return Path.joinpath(Path(self.segments_directory), 'database_state')
    
