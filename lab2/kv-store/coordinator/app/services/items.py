"""Business rules for record operations: EXISTS, CREATE, READ, UPDATE, DELETE, QUERY."""
from typing import Any

from app.exceptions import KeyAlreadyExists, KeyNotFound
from app.schemas import Item, Partition, PartitionItem
from app.services.tables import TableRegistry
from app.storage.base import Storage


def full_key(key: str, sort_key: str | None) -> str:
    """Key shown in error messages: user1 or user1/2026-10-01."""
    return key if sort_key is None else f"{key}/{sort_key}"


class ItemService:
    def __init__(self, tables: TableRegistry, storage: Storage):
        self._tables = tables
        self._storage = storage

    def locate(self, key: str) -> str:
        """Shard is chosen ONLY by the partition key."""
        return self._storage.locate(key)

    def _item(self, key: str, sort_key: str | None, value: Any) -> Item:
        return Item(key=key, sort_key=sort_key, value=value, shard=self.locate(key))

    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        if not self._tables.matches(table, sort_key):
            return False
        return await self._storage.exists(table, key, sort_key)

    async def create(self, table: str, key: str, value: Any, sort_key: str | None = None) -> Item:
        self._tables.check_key_shape(table, sort_key)
        if not await self._storage.insert(table, key, value, sort_key):
            raise KeyAlreadyExists(full_key(key, sort_key))
        return self._item(key, sort_key, value)

    async def read(self, table: str, key: str, sort_key: str | None = None) -> Item:
        self._tables.check_key_shape(table, sort_key)
        value = await self._storage.get(table, key, sort_key)
        if value is None:
            raise KeyNotFound(full_key(key, sort_key))
        return self._item(key, sort_key, value)

    async def update(self, table: str, key: str, value: Any, sort_key: str | None = None) -> Item:
        self._tables.check_key_shape(table, sort_key)
        if not await self._storage.update(table, key, value, sort_key):
            raise KeyNotFound(full_key(key, sort_key))
        return self._item(key, sort_key, value)

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> None:
        self._tables.check_key_shape(table, sort_key)
        if not await self._storage.delete(table, key, sort_key):
            raise KeyNotFound(full_key(key, sort_key))

    async def query(self, table: str, key: str,
                    sk_from: str | None = None, sk_to: str | None = None) -> Partition:
        """All records of one partition sorted by sort key, optionally within [sk_from, sk_to]."""
        self._tables.ensure_composite(table)
        rows = await self._storage.query(table, key, sk_from, sk_to)
        return Partition(partition_key=key, shard=self.locate(key),
                         items=[PartitionItem(sort_key=sk, value=v) for sk, v in rows])
