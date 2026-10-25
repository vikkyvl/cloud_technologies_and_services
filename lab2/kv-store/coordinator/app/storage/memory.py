"""In-memory storage used in single-node mode."""
from typing import Any

from app.storage.base import Storage


class InMemoryStorage(Storage):
    def __init__(self, node_id: str):
        self._node_id = node_id
        self._data: dict[str, dict[str, Any]] = {}  # table -> {key -> value}

    def _table(self, table: str) -> dict[str, Any]:
        return self._data.setdefault(table, {})

    def locate(self, key: str) -> str:
        return self._node_id

    async def exists(self, table: str, key: str) -> bool:
        return key in self._table(table)

    async def get(self, table: str, key: str) -> Any | None:
        return self._table(table).get(key)

    async def insert(self, table: str, key: str, value: Any) -> bool:
        records = self._table(table)
        if key in records:
            return False
        records[key] = value
        return True

    async def update(self, table: str, key: str, value: Any) -> bool:
        records = self._table(table)
        if key not in records:
            return False
        records[key] = value
        return True

    async def delete(self, table: str, key: str) -> bool:
        return self._table(table).pop(key, None) is not None
