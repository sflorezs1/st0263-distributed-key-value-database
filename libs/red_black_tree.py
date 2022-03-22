# Original code adapted from: https://github.com/chrislessard/LSM-Tree/blob/master/src/red_black_tree.py

from collections import deque
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional, Tuple
# from .types import Value
Value = Dict[str, bytes | str]


class Colors(Enum):
    NIL = 0
    BLACK = 1
    RED = 2


class Directions(Enum):
    L = 0
    R = 1


class Node(object):
    def __init__(
        self,
        key: bytes,
        color: Colors,
        parent: 'Node',
        left: 'Node' = None,
        right: 'Node' = None,
        value: Value = None,
        offset: int = None,
        segment: int = None
    ) -> None:
        self.key: bytes = key
        self.color: Colors = color
        self.parent: 'Node' = parent
        self.left: 'Node' = left
        self.right: 'Node' = right
        self.value: Value = value
        self.offset: int = offset
        self.segment: int = segment

    def __iter__(self):
        if self.left.color != Colors.NIL:
            yield from iter(self.left)

        yield self.key

        if self.right.color != Colors.NIL:
            yield from iter(self.right)

    def __repr__(self) -> str:
        return f'Node({self.color}, {self.key}, {self.value}, {self.offset}, {self.segment})'

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, self.__class__):
            if self.color == Colors.NIL and self.color == __o.color:
                return True

            if self.parent is None or __o.parent is None:
                same_parent = self.parent is None and __o.parent is None
            else:
                same_parent = self.parent.key == __o.parent.key and self.parent.color == __o.parent.color
            return self.key == __o.key and self.color == __o.color and same_parent

    def has_children(self) -> bool:
        return self.left.color != Colors.NIL or self.right.color != Colors.NIL

    def get_children_count(self) -> bool:
        return int(self.left.color != Colors.NIL) + int(self.right.color != Colors.NIL)

    def in_order_traversal(self, traversal: List['Node']):
        if self.left.color != Colors.NIL:
            self.left.in_order_traversal(traversal)
        traversal.append(self)
        if self.right.color != Colors.NIL:
            self.right.in_order_traversal(traversal)


class RedBlackTree(object):
    NIL_LEAF = Node(key=None, color=Colors.NIL, parent=None, value=None)

    def __init__(self) -> None:
        self.count: int = 0
        self.root: Node = None
        self.ROTATIONS: Dict[Directions, Callable] = {
            Directions.R: self._left_rotation,
            Directions.L: self._right_rotation
        }
        self.total_bytes: int = 0

    def __iter__(self) -> Optional[List[Node]]:
        if not self.root:
            return list()
        yield from iter(self.root)

    def add(self, key: bytes, value: Value, offset: int = None, segment: int = None) -> None:
        if not self.root:
            self.root = Node(
                key=key,
                color=Colors.BLACK,
                parent=None,
                left=self.NIL_LEAF,
                right=self.NIL_LEAF,
                value=value,
                offset=offset,
                segment=segment
            )
            self.count += 1
            return
        parent, node_dir = self._find_parent(key)
        if node_dir is None:
            parent.value = value
            return

        new_node = Node(
            key=key,
            color=Colors.RED,
            parent=parent,
            left=self.NIL_LEAF,
            right=self.NIL_LEAF,
            value=value,
            offset=offset,
            segment=segment
        )

        if node_dir == Directions.L:
            parent.left = new_node
        else:
            parent.right = new_node

        self._try_rebalance(new_node)
        self.count += 1
        return

    def remove(self, key: bytes) -> None:

        def cases(node: Node):

            def __case_1(node: Node):
                if self.root == node:
                    node.color = Colors.BLACK
                    return
                __case_2(node)

            def __case_2(node: Node):
                parent = node.parent
                sibling, direction = self._get_sibling(node)
                if sibling.color == Colors.RED and parent.color == Colors.BLACK and\
                        sibling.left.color != Colors.RED and sibling.right.color != Colors.RED:
                    self.ROTATIONS[direction](
                        node=None, parent=sibling, grandfather=parent)
                    parent.color = Colors.RED
                    sibling.color = Colors.BLACK
                    return __case_1(node)
                return __case_3(node)

            def __case_3(node: Node):
                parent: Node = node.parent
                sibling, _ = self._get_sibling(node)
                if sibling.color == Colors.BLACK and parent.color == Colors.BLACK and\
                        sibling.left.color != Colors.RED and sibling.right.color != Colors.RED:
                    sibling.color = Colors.RED
                    return __case_1(parent)
                return __case_4(node)

            def __case_4(node: Node):
                parent = node.parent
                if parent.color == Colors.RED:
                    sibling, direction = self._get_sibling(node)
                    if sibling.color == Colors.BLACK and sibling.left.color != Colors.RED and sibling.right.color != Colors.RED:
                        parent.color, sibling.color = sibling.color, parent.color
                        return
                return __case_5(node)

            def __case_5(node: Node):
                sibling, direction = self._get_sibling(node)
                closer_node = sibling.right if direction == Directions.L else sibling.left
                outer_node = sibling.left if direction == Directions.L else sibling.right
                if closer_node.color == Colors.RED and outer_node.color != Colors.RED and sibling.color == Colors.BLACK:
                    (self._left_rotation
                     if direction == Directions.L
                     else self._right_rotation)(node=None, parent=closer_node, grandfather=sibling)
                    closer_node.color = Colors.BLACK
                    sibling.color = Colors.RED
                return __case_6(node)

            def __case_6(node: Node):
                sibling, direction = self._get_sibling(node)
                outer_node = sibling.left if direction == 'L' else sibling.right

                if sibling.color == Colors.BLACK and outer_node.color == Colors.RED:
                    parent_color = sibling.parent.color
                    self.ROTATIONS[direction](
                        node=None, parent=sibling, grandfather=sibling.parent)
                    # new parent is sibling
                    sibling.color = parent_color
                    sibling.right.color = Colors.BLACK
                    sibling.left.color = Colors.BLACK
                    return
                raise Exception(
                    'Well this is embarrasing, we should not be here, something is wrong!')

            return __case_1(node)

        node_to_remove: Node = self.find_node(key)
        if node_to_remove is None:
            return
        if node_to_remove.get_children_count() == 2:
            succ = self._find_in_order_successor(node_to_remove)
            node_to_remove.key = succ.key
            node_to_remove = succ

        left_child = node_to_remove.left
        right_child = node_to_remove.right
        not_nil_child = left_child if left_child != self.NIL_LEAF else right_child

        if node_to_remove == self.root:
            if not_nil_child != self.NIL_LEAF:
                self.root = not_nil_child
                self.root.parent = None
                self.root.color = Colors.BLACK
            else:
                self.root = None
        elif node_to_remove.color == Colors.RED:
            if not node_to_remove.has_children():
                self._remove_leaf(node_to_remove)
            else:
                raise Exception('RED Node has children!')
        else:
            if right_child.has_children() or left_child.has_children():
                raise Exception(
                    'The RED Child of a BLACK Node with 0 or 1 children cannot have children!')
            if not_nil_child.color == Colors.RED:
                node_to_remove.key = not_nil_child.key
                node_to_remove.left = not_nil_child.left
                node_to_remove.right = not_nil_child.right
            else:
                cases(self, node_to_remove)
                self._remove_leaf(node_to_remove)

        self.count -= 1

    def contains(self, key: bytes) -> bool:
        return bool(self.find_node(key))

    def ceil(self, key: bytes) -> Optional[bytes]:
        if self.root is None:
            return None
        last_found_val: bytes = None if self.root.key < key else self.root.key

        queue: Deque = deque()

        queue.append(self.root)

        while queue:
            node: Node = queue.popleft()

            if node == self.NIL_LEAF:
                break
            if node.key == key:
                last_found_val = node.key
                break
            elif node.key < key:
                queue.append(node.right)
            else:
                last_found_val = node.key
                queue.append(node.left)

        return last_found_val

    def floor(self, key: bytes) -> Optional[bytes]:
        if self.root is None:
            return None
        last_found_val: bytes = None if self.root.key > key else self.root.key

        queue: Deque = deque()

        queue.append(self.root)

        while queue:
            node: Node = queue.popleft()

            if node == self.NIL_LEAF:
                break
            if node.key == key:
                last_found_val = node.key
                break
            elif node.key < key:
                last_found_val = node.key
                queue.append(node.right)
            else:
                queue.append(node.left)

        return last_found_val

    def _remove_leaf(self, leaf: Node) -> None:
        if leaf.key >= leaf.parent.key:
            leaf.parent.right = self.NIL_LEAF
        else:
            leaf.parent.left = self.NIL_LEAF

    def _try_rebalance(self, node) -> None:
        parent: Optional[Node] = node.parent
        key: bytes = node.key
        if parent is None or\
                parent.parent is None or\
                node.color != Colors.RED or parent.color != Colors.RED:
            return
        grandfather: Node = parent.parent
        node_dir = Directions.L if parent.key > key else Directions.R
        parent_dir = Directions.L if grandfather.key > parent.key else Directions.R
        uncle = grandfather.right if parent_dir == Directions.L else grandfather.left
        general_direction = node_dir.name + parent_dir.name

        if uncle == self.NIL_LEAF or uncle.color == Colors.BLACK:
            if general_direction == 'LL':
                self._right_rotation(
                    node, parent, grandfather, to_recolor=True)
            elif general_direction == 'RR':
                self._left_rotation(node, parent, grandfather, to_recolor=True)
            elif general_direction == 'LR':
                self._right_rotation(
                    node=None, parent=node, grandfather=parent)
                self._left_rotation(node=parent, parent=node,
                                    grandfather=grandfather, to_recolor=True)
            elif general_direction == 'RL':
                self._left_rotation(node=None, parent=node, grandfather=parent)
                self._right_rotation(
                    node=parent, parent=node, grandfather=grandfather, to_recolor=True)
            else:
                raise Exception(
                    f'{general_direction} is not a valid direction!')
        else:
            self._recolor(grandfather)

    def __update_parent(self, node: Node, parent_old_child: Node, new_parent: Node) -> None:
        node.parent = new_parent
        if new_parent:
            if new_parent.key > parent_old_child.key:
                new_parent.left = node
            else:
                new_parent.right = node
        else:
            self.root = node

    def _right_rotation(self, node: Node, parent: Node, grandfather: Node, to_recolor=False) -> None:
        grand_grandfather: Node = grandfather.parent
        self.__update_parent(
            node=parent, parent_old_child=grand_grandfather, new_parent=grand_grandfather)

        old_right: Node = parent.right
        parent.right = grandfather
        grandfather.parent = parent

        grandfather.left = old_right
        old_right.parent = grandfather

        if to_recolor:
            parent.color = Colors.BLACK
            node.color = Colors.RED
            grandfather.color = Colors.RED

    def _left_rotation(self, node: Node, parent: Node, grandfather: Node, to_recolor=False) -> None:
        grand_grandfather: Node = grandfather.parent
        self.__update_parent(
            node=parent, 
            parent_old_child=grandfather, 
            new_parent=grand_grandfather
        )

        old_left: Node = parent.left
        parent.left = grandfather
        grandfather.parent = parent

        grandfather.right = old_left
        old_left.parent = grandfather

        if to_recolor:
            parent.color = Colors.BLACK
            node.color = Colors.RED
            grandfather.color = Colors.RED

    def _recolor(self, grandfather: Node) -> None:
        grandfather.right.color = Colors.BLACK
        grandfather.left.color = Colors.BLACK
        if grandfather != self.root:
            grandfather.color = Colors.RED
        self._try_rebalance(grandfather)

    def _find_parent(self, key: bytes) -> Tuple[Node, Directions]:
        queue: Deque = deque()

        queue.append(self.root)

        current_parent: Node = self.root
        current_direction: Directions = None

        while queue:
            parent: Node = queue.popleft()
            if key == parent.key:
                current_parent = parent
                current_direction = None
                break
            elif parent.key < key:
                if parent.right.color == Colors.NIL:
                    current_parent = parent
                    current_direction = Directions.R
                    break
                queue.append(parent.right)
            elif parent.key > key:
                if parent.left.color == Colors.NIL:
                    current_parent = parent
                    current_direction = Directions.L
                    break
                queue.append(parent.left)

        return current_parent, current_direction

    def find_node(self, key: bytes) -> Node:
        queue: Deque = deque()

        queue.append(self.root)

        current_node: Node = self.root

        while queue:
            node: Node = queue.popleft()
            if node is None or node == self.NIL_LEAF:
                current_node = None
                break
            if node.key < key:
                queue.append(node.right)
            elif node.key > key:
                queue.append(node.left)
            else:
                current_node = node
                break

        return current_node

    def _find_in_order_successor(self, node: Node) -> Node:
        right: Node = node.right
        left: Node = node.left

        if left == self.NIL_LEAF:
            return right
        while left.left != self.NIL_LEAF:
            left = left.left
        return left

    def _get_sibling(self, node: Node) -> Tuple[Node, Directions]:
        parent: Node = node.parent
        if node.key >= parent.key:
            sibling: Node = parent.left
            direction: Directions = Directions.L
        else:
            sibling: Node = parent.right
            direction: Directions = Directions.R
        return sibling, direction

    def in_order_traversal(self) -> List[Node]:
        traversal: List[Node] = []
        if self.root:
            self.root.in_order_traversal(traversal)
        return traversal
