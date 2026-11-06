import asyncio
from collections import defaultdict
from contextvars import ContextVar
from itertools import count
from typing import Any, Callable

import httpx
from fastapi import status

from app.core.constants import (
    HEADER_APPLIED_OFFSET,
    HEADER_OFFSET,
    HEADER_VERSION,
    SHARD_COMPOSITE_PATH,
    SHARD_ITEM_PATH,
    SHARD_OFFSET_PATH,
    SHARD_PARTITION_PATH,
)
from app.exceptions import ReadQuorumNotReached, ShardUnavailable, WriteQuorumNotReached
from app.schemas import Replica, Shard
from app.services.quorum import QuorumSettings
from app.services.shards import ShardRegistry
from app.storage.base import Storage
from app.storage.hashing import ShardRouter

served_replica: ContextVar[str | None] = ContextVar("served_replica", default=None)
read_replicas: ContextVar[str | None] = ContextVar("read_replicas", default=None)
write_acks: ContextVar[str | None] = ContextVar("write_acks", default=None)

QUORUM_POLL_INTERVAL = 0.02


def by_version(response: httpx.Response) -> int:
    return int(response.headers.get(HEADER_VERSION, "0"))


def by_applied_offset(response: httpx.Response) -> int:
    return int(response.headers.get(HEADER_APPLIED_OFFSET, "-1"))


class ShardedStorage(Storage):
    def __init__(self, registry: ShardRegistry, router: ShardRouter, fallback: Storage,
                 quorum: QuorumSettings, timeout: float):
        self._registry = registry
        self._router = router
        self._fallback = fallback
        self._quorum = quorum
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
        if HEADER_OFFSET in response.headers:
            await self._wait_for_write_quorum(shard, int(response.headers[HEADER_OFFSET]))

        return response

    async def _applied_offset(self, replica: Replica) -> int:
        try:
            response = await self._client.get(replica.url + SHARD_OFFSET_PATH)
        except httpx.RequestError:
            return -1

        return response.json()["applied_offset"]

    async def _wait_for_write_quorum(self, shard: Shard, offset: int) -> None:
        acks = [shard.leader.id]
        waiting = [replica for replica in shard.followers if replica.alive]
        deadline = asyncio.get_running_loop().time() + self._quorum.timeout

        while len(acks) < self._quorum.write_quorum:
            if not waiting or asyncio.get_running_loop().time() > deadline:
                write_acks.set(",".join(acks))
                raise WriteQuorumNotReached(shard.id, len(acks), self._quorum.write_quorum)

            offsets = await asyncio.gather(*(self._applied_offset(replica)
                                             for replica in waiting))
            for replica, applied in zip(list(waiting), offsets):
                if applied >= offset:
                    acks.append(replica.id)
                    waiting.remove(replica)

            if len(acks) < self._quorum.write_quorum:
                await asyncio.sleep(QUORUM_POLL_INTERVAL)

        write_acks.set(",".join(acks))

    def _readers(self, shard: Shard) -> list[Replica]:
        alive = [replica for replica in shard.replicas if replica.alive] or shard.replicas
        start = next(self._turns[shard.id]) % len(alive)

        return alive[start:] + alive[:start]

    async def _ask(self, replica: Replica, method: str, path: str,
                   params: dict | None) -> tuple[Replica, httpx.Response | None]:
        try:
            return replica, await self._client.request(method, replica.url + path, params=params)
        except httpx.RequestError:
            self._registry.mark_down(replica.id)
            return replica, None

    async def _read(self, shard: Shard, method: str, path: str,
                    freshness: Callable[[httpx.Response], int],
                    params: dict | None = None) -> httpx.Response:
        candidates = self._readers(shard)
        required = self._quorum.read_quorum
        answers: list[tuple[Replica, httpx.Response]] = []

        while len(answers) < required and candidates:
            missing = required - len(answers)
            batch, candidates = candidates[:missing], candidates[missing:]
            results = await asyncio.gather(*(self._ask(replica, method, path, params)
                                             for replica in batch))
            answers += [(replica, response) for replica, response in results if response is not None]

        if len(answers) < required:
            raise ReadQuorumNotReached(shard.id, len(answers), required)

        replica, response = max(answers, key=lambda answer: freshness(answer[1]))
        served_replica.set(replica.id)
        read_replicas.set(",".join(f"{replica.id}:{freshness(response)}"
                                   for replica, response in answers))

        return response

    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.exists(table, key, sort_key)

        response = await self._read(shard, "HEAD", self._path(table, key, sort_key), by_version)
        return response.status_code == status.HTTP_200_OK

    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        shard = self._shard_for(key)
        if shard is None:
            return await self._fallback.get(table, key, sort_key)

        response = await self._read(shard, "GET", self._path(table, key, sort_key), by_version)
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

        response = await self._read(shard, "GET", path, by_applied_offset, params=params)
        return [(row["sort_key"], row["value"]) for row in response.json()["items"]]

    async def close(self) -> None:
        await self._client.aclose()
