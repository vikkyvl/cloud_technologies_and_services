"""Consistent hashing with virtual nodes."""
import bisect

from app.schemas import Shard
from app.storage.hashing import ShardRouter, hash_key


class HashRing:
    """Hash ring: every shard is placed on the ring as `vnodes` points.
    A key belongs to the first point clockwise from the hash of the key."""

    def __init__(self, shard_ids: list[str], vnodes: int):
        points = sorted(
            (hash_key(f"{shard_id}#{i}"), shard_id)
            for shard_id in shard_ids
            for i in range(vnodes)
        )
        self._hashes = [h for h, _ in points]
        self._owners = [shard_id for _, shard_id in points]

    def get(self, key: str) -> str:
        i = bisect.bisect(self._hashes, hash_key(key)) % len(self._hashes)
        return self._owners[i]


class ConsistentHashRouter(ShardRouter):
    def __init__(self, vnodes: int):
        self._vnodes = vnodes
        self._ids: tuple[str, ...] = ()
        self._ring: HashRing | None = None

    def choose(self, key: str, shards: list[Shard]) -> Shard:
        ids = tuple(s.id for s in shards)
        if ids != self._ids:  # rebuild the ring only when the set of shards changes
            self._ids, self._ring = ids, HashRing(list(ids), self._vnodes)
        owner = self._ring.get(key)
        return next(s for s in shards if s.id == owner)
