"""In-memory storage.
Simple key:     table -> {key -> value}
Composite key:  table -> {partition key -> {sort key -> value}}"""
from typing import Any

from app.storage.base import Storage


class InMemoryStorage(Storage):
    def __init__(self, node_id: str):
        self._node_id = node_id
        self._data: dict[str, dict[str, Any]] = {}

    def _slot(self, table: str, key: str, sort_key: str | None,
              create: bool = False) -> tuple[dict[str, Any], str]:
        """Dictionary that holds the record and the name of the record inside it."""
        records = self._data.setdefault(table, {}) if create else self._data.get(table, {})
        if sort_key is None:
            return records, key
        partition = records.setdefault(key, {}) if create else records.get(key, {})
        return partition, sort_key

    def locate(self, key: str) -> str:
        return self._node_id

    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        box, name = self._slot(table, key, sort_key)
        return name in box

    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        box, name = self._slot(table, key, sort_key)
        return box.get(name)

    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        box, name = self._slot(table, key, sort_key, create=True)
        if name in box:
            return False
        box[name] = value
        return True

    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        box, name = self._slot(table, key, sort_key)
        if name not in box:
            return False
        box[name] = value
        return True

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        box, name = self._slot(table, key, sort_key)
        if box.pop(name, None) is None:
            return False
        if sort_key is not None and not box:  # remove an empty partition
            self._data[table].pop(key, None)
        return True

    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        partition = self._data.get(table, {}).get(key, {})
        return [
            (sk, value) for sk, value in sorted(partition.items())
            if (sk_from is None or sk >= sk_from) and (sk_to is None or sk <= sk_to)
        ]

    def dump(self) -> dict[str, dict[str, Any]]:
        """Copy of all data (used by the shard debug endpoint)."""
        return {t: dict(r) for t, r in self._data.items()}
