import hashlib
from abc import ABC, abstractmethod

from app.schemas import Shard


def hash_key(key: str) -> int:
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)


class ShardRouter(ABC):
    @abstractmethod
    def choose(self, key: str, shards: list[Shard]) -> Shard: ...


class ModuloRouter(ShardRouter):
    def choose(self, key: str, shards: list[Shard]) -> Shard:
        return shards[hash_key(key) % len(shards)]
