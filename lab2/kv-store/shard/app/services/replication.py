import asyncio
from typing import Any

from ..core.constants import OP_CREATE, OP_DELETE, OP_UPDATE
from ..exceptions import KeyAlreadyExists, KeyNotFound, NotLeader
from ..storage.memory import InMemoryStorage
from .log import ReplicationLog
from .state import ReplicaState


def full_key(key: str, sort_key: str | None) -> str:
    return key if sort_key is None else f"{key}/{sort_key}"


async def apply_event(storage: InMemoryStorage, event: dict) -> bool:
    table, key, sort_key = event["table"], event["key"], event["sort_key"]
    if event["version"] <= storage.version(table, key, sort_key):
        return False

    if event["op"] == OP_DELETE:
        await storage.delete(table, key, sort_key)
    elif await storage.exists(table, key, sort_key):
        await storage.update(table, key, event["value"], sort_key)
    else:
        await storage.insert(table, key, event["value"], sort_key)

    storage.set_version(table, key, sort_key, event["version"])
    return True


class ReplicationService:
    def __init__(self, storage: InMemoryStorage, replication_log: ReplicationLog,
                 state: ReplicaState, shard_id: str):
        self._storage = storage
        self._log = replication_log
        self._state = state
        self._shard_id = shard_id
        self._lock = asyncio.Lock()

    def _ensure_leader(self) -> None:
        if not self._state.is_leader:
            raise NotLeader(self._state.replica_id, self._shard_id)

    async def create(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> dict:
        self._ensure_leader()
        async with self._lock:
            if await self._storage.exists(table, key, sort_key):
                raise KeyAlreadyExists(full_key(key, sort_key))

            return await self._commit(OP_CREATE, table, key, sort_key, value)

    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> dict:
        self._ensure_leader()
        async with self._lock:
            if not await self._storage.exists(table, key, sort_key):
                raise KeyNotFound(full_key(key, sort_key))

            return await self._commit(OP_UPDATE, table, key, sort_key, value)

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> dict:
        self._ensure_leader()
        async with self._lock:
            if not await self._storage.exists(table, key, sort_key):
                raise KeyNotFound(full_key(key, sort_key))

            return await self._commit(OP_DELETE, table, key, sort_key, None)

    async def _commit(self, operation: str, table: str, key: str,
                      sort_key: str | None, value: Any) -> dict:
        event = {
            "op": operation,
            "table": table,
            "key": key,
            "sort_key": sort_key,
            "value": value,
            "version": self._storage.version(table, key, sort_key) + 1,
        }

        offset = await self._log.append(event)
        await apply_event(self._storage, event)

        return {**event, "offset": offset}
