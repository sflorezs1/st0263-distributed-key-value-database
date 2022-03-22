# Original code adapted from: https://github.com/chrislessard/LSM-Tree/blob/master/src/bloom_filter.py

from math import log
from typing import List
from mmh3 import hash
import numpy as np


class CountingBloomFilter(object):
    def __init__(self, num_items: int, false_positive_prob: float, dtype = np.uint8) -> None:
        self.false_positive_prob: float = false_positive_prob
        self.bit_array_size: int = int(-(num_items * log(self.false_positive_prob)) / (log(2)**2))
        self.num_hash_fns: int = int((self.bit_array_size/num_items) * log(2))

        self.bit_array: np.ndarray = np.zeros(shape=self.bit_array_size, dtype=dtype)

    def add(self, item) -> None:
        digests: List[bytes] = []
        for seed in range(self.num_hash_fns):
            # each seed creates a different digest.
            digest: bytes = hash(item, seed) % self.bit_array_size
            digests.append(digest)

            self.bit_array[digest] += 1

    def check(self, item) -> bool:
        for seed in range(self.num_hash_fns):
            digest = hash(item, seed) % self.bit_array_size
            if self.bit_array[digest] == 0.:
                # if any bit is false, the item is not definitely present
                return False
        return True