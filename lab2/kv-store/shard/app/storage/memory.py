from typing import Any

from .base import Storage


class InMemoryStorage(Storage):
    def __init__(self, node_id: str):
        self._node_id = node_id
        self._data: dict[str, dict[str, Any]] = {}
        self._versions: dict[tuple[str, str, str | None], int] = {}

    def _slot(self, table: str, key: str, sort_key: str | None,
              create: bool = False) -> tuple[dict[str, Any], str]:
        records = self._data.setdefault(table, {}) if create else self._data.get(table, {})
        if sort_key is None:
            return records, key

        partition = records.setdefault(key, {}) if create else records.get(key, {})
        return partition, sort_key

    def locate(self, key: str) -> str:
        return self._node_id

    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool:
        container, slot_key = self._slot(table, key, sort_key)
        return slot_key in container

    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        container, slot_key = self._slot(table, key, sort_key)
        return container.get(slot_key)

    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        container, slot_key = self._slot(table, key, sort_key, create=True)
        if slot_key in container:
            return False

        container[slot_key] = value
        return True

    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        container, slot_key = self._slot(table, key, sort_key)
        if slot_key not in container:
            return False

        container[slot_key] = value
        return True

    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        container, slot_key = self._slot(table, key, sort_key)
        if container.pop(slot_key, None) is None:
            return False

        if sort_key is not None and not container:
            self._data[table].pop(key, None)
        return True

    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        partition = self._data.get(table, {}).get(key, {})

        return [
            (sort_key, value) for sort_key, value in sorted(partition.items())
            if (sk_from is None or sort_key >= sk_from) and (sk_to is None or sort_key <= sk_to)
        ]

    def version(self, table: str, key: str, sort_key: str | None = None) -> int:
        return self._versions.get((table, key, sort_key), 0)

    def set_version(self, table: str, key: str, sort_key: str | None, version: int) -> None:
        self._versions[(table, key, sort_key)] = version

    def versions(self) -> dict[str, int]:
        return {"/".join(part for part in slot if part is not None): version
                for slot, version in sorted(self._versions.items(), key=lambda item: str(item[0]))}

    def dump(self) -> dict[str, dict[str, Any]]:
        return {table: dict(records) for table, records in self._data.items()}
