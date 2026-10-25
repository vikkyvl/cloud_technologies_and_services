"""Storage that forwards every operation to the shard chosen by the partition key."""
from typing import Any

import httpx
from fastapi import status

from app.core.constants import SHARD_COMPOSITE_URL, SHARD_ITEM_URL, SHARD_PARTITION_URL
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
        """Only the partition key is hashed, so all sort keys of it live on one shard."""
        if self._registry.is_empty():
            return None
        return self._router.choose(key, self._registry.list())

    def locate(self, key: str) -> str:
        shard = self._shard_for(key)
        return shard.id if shard else self._fallback.locate(key)

    async def _send(self, shard: Shard, method: str, url: str,
                    value: Any = None, params: dict | None = None) -> httpx.Response:
        kwargs = {"json": value} if value is not None else {}
        try:
            return await self._client.request(method, url, params=params, **kwargs)
        except httpx.RequestError:
            raise ShardUnavailable(shard.id)

    @staticmethod
    def _url(shard: Shard, table: str, key: str, sort_key: str | None) -> str:
        if sort_key is None:
            return SHARD_ITEM_URL.format(base=shard.url, table=table, key=key)
        return SHARD_COMPOSITE_URL.format(base=shard.url, table=table, key=key,
                                          sort_key=sort_key)

    # ---------- operations ----------
    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.exists(table, key, sort_key)
        r = await self._send(shard, "HEAD", self._url(shard, table, key, sort_key))
        return r.status_code == status.HTTP_200_OK

    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.get(table, key, sort_key)
        r = await self._send(shard, "GET", self._url(shard, table, key, sort_key))
        if r.status_code == status.HTTP_404_NOT_FOUND:
            return None
        return r.json()["value"]

    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.insert(table, key, value, sort_key)
        r = await self._send(shard, "PUT", self._url(shard, table, key, sort_key), value)
        return r.status_code == status.HTTP_201_CREATED

    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.update(table, key, value, sort_key)
        r = await self._send(shard, "PATCH", self._url(shard, table, key, sort_key), value)
        return r.status_code == status.HTTP_200_OK

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.delete(table, key, sort_key)
        r = await self._send(shard, "DELETE", self._url(shard, table, key, sort_key))
        return r.status_code == status.HTTP_204_NO_CONTENT

    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.query(table, key, sk_from, sk_to)
        params = {k: v for k, v in (("sk_from", sk_from), ("sk_to", sk_to)) if v is not None}
        url = SHARD_PARTITION_URL.format(base=shard.url, table=table, key=key)
        r = await self._send(shard, "GET", url, params=params)
        return [(row["sort_key"], row["value"]) for row in r.json()["items"]]

    async def close(self) -> None:
        await self._client.aclose()
