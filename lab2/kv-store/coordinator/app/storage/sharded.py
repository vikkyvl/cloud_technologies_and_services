"""Storage that forwards every operation to the shard chosen by the key hash."""
from typing import Any

import httpx
from fastapi import status

from app.core.constants import SHARD_ITEM_URL
from app.exceptions import ShardUnavailable
from app.schemas import Shard
from app.services.shards import ShardRegistry
from app.storage.base import Storage
from app.storage.hashing import ShardRouter


class ShardedStorage(Storage):
    def __init__(self, registry: ShardRegistry, router: ShardRouter, fallback: Storage,
                 timeout: float):
        self._registry = registry
        self._router = router  # strategy of choosing a shard: hash % N or hash ring
        self._fallback = fallback  # used while no shard is registered (single-node mode)
        self._client = httpx.AsyncClient(timeout=timeout)

    # ---------- routing ----------
    def _shard_for(self, key: str) -> Shard | None:
        if self._registry.is_empty():
            return None
        return self._router.choose(key, self._registry.list())

    def locate(self, key: str) -> str:
        shard = self._shard_for(key)
        return shard.id if shard else self._fallback.locate(key)

    async def _send(self, shard: Shard, method: str, table: str, key: str,
                    value: Any = None) -> httpx.Response:
        url = SHARD_ITEM_URL.format(base=shard.url, table=table, key=key)
        kwargs = {"json": value} if value is not None else {}
        try:
            return await self._client.request(method, url, **kwargs)
        except httpx.RequestError:
            raise ShardUnavailable(shard.id)

    # ---------- operations ----------
    async def exists(self, table: str, key: str) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.exists(table, key)
        r = await self._send(shard, "HEAD", table, key)
        return r.status_code == status.HTTP_200_OK

    async def get(self, table: str, key: str) -> Any | None:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.get(table, key)
        r = await self._send(shard, "GET", table, key)
        if r.status_code == status.HTTP_404_NOT_FOUND:
            return None
        return r.json()["value"]

    async def insert(self, table: str, key: str, value: Any) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.insert(table, key, value)
        r = await self._send(shard, "PUT", table, key, value)
        return r.status_code == status.HTTP_201_CREATED

    async def update(self, table: str, key: str, value: Any) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.update(table, key, value)
        r = await self._send(shard, "PATCH", table, key, value)
        return r.status_code == status.HTTP_200_OK

    async def delete(self, table: str, key: str) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.delete(table, key)
        r = await self._send(shard, "DELETE", table, key)
        return r.status_code == status.HTTP_204_NO_CONTENT

    async def close(self) -> None:
        await self._client.aclose()