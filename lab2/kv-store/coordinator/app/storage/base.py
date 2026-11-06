from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    @abstractmethod
    def locate(self, key: str) -> str:
        ...

    @abstractmethod
    async def exists(self, table: str, key: str, sort_key: str | None = None) -> bool: ...

    @abstractmethod
    async def get(self, table: str, key: str, sort_key: str | None = None) -> Any | None:
        ...

    @abstractmethod
    async def insert(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        ...

    @abstractmethod
    async def update(self, table: str, key: str, value: Any,
                     sort_key: str | None = None) -> bool:
        ...

    @abstractmethod
    async def delete(self, table: str, key: str, sort_key: str | None = None) -> bool:
        ...

    @abstractmethod
    async def query(self, table: str, key: str, sk_from: str | None = None,
                    sk_to: str | None = None) -> list[tuple[str, Any]]:
        ...
