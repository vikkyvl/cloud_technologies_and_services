import bisect

from app.schemas import Shard
from app.storage.hashing import ShardRouter, hash_key


class HashRing:
    def __init__(self, shard_ids: list[str], vnodes: int):
        points = sorted(
            (hash_key(f"{shard_id}#{vnode}"), shard_id)
            for shard_id in shard_ids
            for vnode in range(vnodes)
        )

        self._hashes = [point_hash for point_hash, _ in points]
        self._owners = [shard_id for _, shard_id in points]

    def get(self, key: str) -> str:
        position = bisect.bisect(self._hashes, hash_key(key)) % len(self._hashes)
        return self._owners[position]


class ConsistentHashRouter(ShardRouter):
    def __init__(self, vnodes: int):
        self._vnodes = vnodes
        self._ids: tuple[str, ...] = ()
        self._ring: HashRing | None = None

    def choose(self, key: str, shards: list[Shard]) -> Shard:
        shard_ids = tuple(shard.id for shard in shards)
        if shard_ids != self._ids:
            self._ids, self._ring = shard_ids, HashRing(list(shard_ids), self._vnodes)

        owner = self._ring.get(key)
        return next(shard for shard in shards if shard.id == owner)
