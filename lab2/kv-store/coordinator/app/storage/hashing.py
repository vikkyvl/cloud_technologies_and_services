"""Choosing a shard for a key."""
import hashlib
from abc import ABC, abstractmethod

from app.schemas import Shard


def hash_key(key: str) -> int:
    """MD5 gives the same number for the same key in every process and after restarts."""
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)


class ShardRouter(ABC):
    """Strategy that maps a key to one of the shards."""

    @abstractmethod
    def choose(self, key: str, shards: list[Shard]) -> Shard: ...


class ModuloRouter(ShardRouter):
    """Simple hash % N."""

    def choose(self, key: str, shards: list[Shard]) -> Shard:
        return shards[hash_key(key) % len(shards)]