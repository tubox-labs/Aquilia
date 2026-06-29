from __future__ import annotations

from aquilia.db.engine import AquiliaDatabase, get_database
from aquilia.di.decorators import service

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

@service(scope="app")
class AquiliaDatabaseProvider:
    def provide(self) -> AquiliaDatabase:
        return get_database()

