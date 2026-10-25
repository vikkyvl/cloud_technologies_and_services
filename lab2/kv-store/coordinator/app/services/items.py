"""Business rules for record operations: EXISTS, CREATE, READ, UPDATE, DELETE."""
from typing import Any

from app.exceptions import KeyAlreadyExists, KeyNotFound
from app.schemas import Item
from app.services.tables import TableRegistry
from app.storage.base import Storage


class ItemService:
    def __init__(self, tables: TableRegistry, storage: Storage):
        self._tables = tables
        self._storage = storage

    def locate(self, key: str) -> str:
        return self._storage.locate(key)

    async def exists(self, table: str, key: str) -> bool:
        if not self._tables.is_registered(table):
            return False
        return await self._storage.exists(table, key)

    async def create(self, table: str, key: str, value: Any) -> Item:
        self._tables.ensure_exists(table)
        if not await self._storage.insert(table, key, value):
            raise KeyAlreadyExists(key)
        return Item(key=key, value=value, shard=self.locate(key))

    async def read(self, table: str, key: str) -> Item:
        self._tables.ensure_exists(table)
        value = await self._storage.get(table, key)
        if value is None:
            raise KeyNotFound(key)
        return Item(key=key, value=value, shard=self.locate(key))

    async def update(self, table: str, key: str, value: Any) -> Item:
        self._tables.ensure_exists(table)
        if not await self._storage.update(table, key, value):
            raise KeyNotFound(key)
        return Item(key=key, value=value, shard=self.locate(key))

    async def delete(self, table: str, key: str) -> None:
        self._tables.ensure_exists(table)
        if not await self._storage.delete(table, key):
            raise KeyNotFound(key)
