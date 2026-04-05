from __future__ import annotations


class LeafService:
    def value(self) -> int:
        return 21


class MidService:
    def __init__(self, leaf: LeafService):
        self.leaf = leaf

    def value(self) -> int:
        return self.leaf.value() + 11


class TopService:
    def __init__(self, mid: MidService):
        self.mid = mid

    def value(self) -> int:
        return self.mid.value() * 2
