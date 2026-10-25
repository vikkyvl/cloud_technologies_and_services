"""Storage abstraction. Services depend on this interface, not on a concrete storage."""
from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """Where records are physically kept (coordinator memory or shards).
    sort_key is None for tables with a simple key."""

    @abstractmethod
    def locate(self, key: str) -> str:
        """Return the id of the node that stores the partition key."""

    @abstractmethod
    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool: ...

    @abstractmethod
    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        """Return the value or None if the record is missing."""

    @abstractmethod
    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        """Store a new record. Return False if it already exists."""

    @abstractmethod
    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        """Replace the value. Return False if the record is missing."""

    @abstractmethod
    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        """Remove the record. Return False if it is missing."""

    @abstractmethod
    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        """Records of one partition as (sort_key, value), sorted by sort_key."""
