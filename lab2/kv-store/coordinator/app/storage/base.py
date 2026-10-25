"""Storage abstraction. Services depend on this interface, not on a concrete storage."""
from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """Where records are physically kept (coordinator memory now, shards later)."""

    @abstractmethod
    def locate(self, key: str) -> str:
        """Return the id of the node that stores the key."""

    @abstractmethod
    async def exists(self, table: str, key: str) -> bool: ...

    @abstractmethod
    async def get(self, table: str, key: str) -> Any | None:
        """Return the value or None if the key is missing."""

    @abstractmethod
    async def insert(self, table: str, key: str, value: Any) -> bool:
        """Store a new key. Return False if the key already exists."""

    @abstractmethod
    async def update(self, table: str, key: str, value: Any) -> bool:
        """Replace the value. Return False if the key is missing."""

    @abstractmethod
    async def delete(self, table: str, key: str) -> bool:
        """Remove the key. Return False if the key is missing."""
