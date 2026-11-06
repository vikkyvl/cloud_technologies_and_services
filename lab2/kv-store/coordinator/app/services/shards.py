from __future__ import annotations

import time

from app.core.constants import ROLE_FOLLOWER, ROLE_LEADER, STATUS_REGISTERED, STATUS_UPDATED
from app.exceptions import ReplicaSetFull
from app.schemas import Replica, ReplicaRegistration, Shard


class ShardRegistry:
    def __init__(self, replication_factor: int, replica_ttl: float):
        self._replication_factor = replication_factor
        self._replica_ttl = replica_ttl
        self._replica_sets: dict[str, dict[str, str]] = {}
        self._last_seen: dict[str, float] = {}

    def register(self, registration: ReplicaRegistration) -> str:
        replicas = self._replica_sets.setdefault(registration.shard_id, {})

        if registration.replica_id in replicas:
            replicas[registration.replica_id] = registration.url
            self._last_seen[registration.replica_id] = time.monotonic()
            return STATUS_UPDATED

        if len(replicas) >= self._replication_factor:
            raise ReplicaSetFull(registration.shard_id, self._replication_factor)

        replicas[registration.replica_id] = registration.url
        self._last_seen[registration.replica_id] = time.monotonic()
        return STATUS_REGISTERED

    def mark_down(self, replica_id: str) -> None:
        self._last_seen[replica_id] = float("-inf")

    def _is_alive(self, replica_id: str) -> bool:
        return time.monotonic() - self._last_seen[replica_id] <= self._replica_ttl

    def get(self, shard_id: str) -> Shard:
        replicas = self._replica_sets[shard_id]
        replica_ids = sorted(replicas)

        return Shard(
            id=shard_id,
            replicas=[Replica(id=replica_id, url=replicas[replica_id],
                              role=ROLE_LEADER if index == 0 else ROLE_FOLLOWER,
                              alive=self._is_alive(replica_id))
                      for index, replica_id in enumerate(replica_ids)],
            complete=len(replica_ids) == self._replication_factor,
        )

    def list(self) -> list[Shard]:
        return [self.get(shard_id) for shard_id in sorted(self._replica_sets)]

    def active(self) -> list[Shard]:
        return [shard for shard in self.list() if shard.complete]

    def is_empty(self) -> bool:
        return not self.active()
