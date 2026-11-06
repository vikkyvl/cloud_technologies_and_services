from collections import defaultdict
from contextvars import ContextVar
from itertools import count
from typing import Any

import httpx
from fastapi import status

from app.core.constants import SHARD_COMPOSITE_PATH, SHARD_ITEM_PATH, SHARD_PARTITION_PATH
from app.exceptions import ShardUnavailable
from app.schemas import Replica, Shard
from app.services.shards import ShardRegistry
from app.storage.base import Storage
from app.storage.hashing import ShardRouter

served_replica: ContextVar[str | None] = ContextVar("served_replica", default=None)


class ShardedStorage(Storage):
    def __init__(self, registry: ShardRegistry, router: ShardRouter, fallback: Storage,
                 timeout: float):
        self._registry = registry
        self._router = router
        self._fallback = fallback
        self._client = httpx.AsyncClient(timeout=timeout)
        self._turns: dict[str, count] = defaultdict(count)

    def _shard_for(self, key: str) -> Shard | None:
        shards = self._registry.active()
        if not shards:
            return None

        return self._router.choose(key, shards)

    def locate(self, key: str) -> str:
        shard = self._shard_for(key)
        return shard.id if shard else self._fallback.locate(key)

    @staticmethod
    def _path(table: str, key: str, sort_key: str | None) -> str:
        if sort_key is None:
            return SHARD_ITEM_PATH.format(table=table, key=key)

        return SHARD_COMPOSITE_PATH.format(table=table, key=key, sort_key=sort_key)

    async def _write(self, shard: Shard, method: str, path: str,
                     value: Any = None) -> httpx.Response:
        body = {"json": value} if value is not None else {}

        try:
            response = await self._client.request(method, shard.leader.url + path, **body)
        except httpx.RequestError:
            self._registry.mark_down(shard.leader.id)
            raise ShardUnavailable(shard.id)

        served_replica.set(shard.leader.id)
        return response

    def _readers(self, shard: Shard) -> list[Replica]:
        alive = [replica for replica in shard.replicas if replica.alive] or shard.replicas
        start = next(self._turns[shard.id]) % len(alive)

        return alive[start:] + alive[:start]

    async def _read(self, shard: Shard, method: str, path: str,
                    params: dict | None = None) -> httpx.Response:
        for replica in self._readers(shard):
            try:
                response = await self._client.request(method, replica.url + path, params=params)
            except httpx.RequestError:
                self._registry.mark_down(replica.id)
                continue

            served_replica.set(replica.id)
            return response

        raise ShardUnavailable(shard.id)

    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.exists(table, key, sort_key)

        response = await self._read(shard, "HEAD", self._path(table, key, sort_key))
        return response.status_code == status.HTTP_200_OK

    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.get(table, key, sort_key)

        response = await self._read(shard, "GET", self._path(table, key, sort_key))
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None

        return response.json()["value"]

    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.insert(table, key, value, sort_key)

        response = await self._write(shard, "PUT", self._path(table, key, sort_key), value)
        return response.status_code == status.HTTP_201_CREATED

    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.update(table, key, value, sort_key)

        response = await self._write(shard, "PATCH", self._path(table, key, sort_key), value)
        return response.status_code == status.HTTP_200_OK

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.delete(table, key, sort_key)

        response = await self._write(shard, "DELETE", self._path(table, key, sort_key))
        return response.status_code == status.HTTP_204_NO_CONTENT

    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.query(table, key, sk_from, sk_to)

        bounds = (("sk_from", sk_from), ("sk_to", sk_to))
        params = {name: bound for name, bound in bounds if bound is not None}
        path = SHARD_PARTITION_PATH.format(table=table, key=key)

        response = await self._read(shard, "GET", path, params=params)
        return [(row["sort_key"], row["value"]) for row in response.json()["items"]]

    async def close(self) -> None:
        await self._client.aclose()
