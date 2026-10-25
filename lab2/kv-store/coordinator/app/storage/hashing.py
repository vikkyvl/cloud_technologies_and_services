"""Choosing a shard for a key: stable hash of the key modulo number of shards."""
import hashlib

from app.schemas import Shard


def hash_key(key: str) -> int:
    """MD5 gives the same number for the same key in every process and after restarts."""
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)


def pick_shard(key: str, shards: list[Shard]) -> Shard:
    return shards[hash_key(key) % len(shards)]
