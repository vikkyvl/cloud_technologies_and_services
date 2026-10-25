"""Registry of table definitions (metadata is always kept in the coordinator)."""
from app.exceptions import (
    SortKeyNotSupported,
    SortKeyRequired,
    TableAlreadyExists,
    TableNotFound,
)
from app.schemas import TableDefinition


class TableRegistry:
    def __init__(self):
        self._tables: dict[str, TableDefinition] = {}  # table name -> definition

    def register(self, definition: TableDefinition) -> TableDefinition:
        if definition.name in self._tables:
            raise TableAlreadyExists(definition.name)
        self._tables[definition.name] = definition
        return definition

    def list(self) -> dict[str, str]:
        """Table name -> partition key name."""
        return {name: d.partition_key for name, d in self._tables.items()}

    def get(self, table: str) -> TableDefinition:
        if table not in self._tables:
            raise TableNotFound(table)
        return self._tables[table]

    def ensure_exists(self, table: str) -> None:
        self.get(table)

    def is_registered(self, table: str) -> bool:
        return table in self._tables

    def check_key_shape(self, table: str, sort_key: str | None) -> None:
        """A table with a sort key needs (key, sort_key), a table without it needs only key."""
        definition = self.get(table)
        if definition.sort_key and sort_key is None:
            raise SortKeyRequired(table)
        if not definition.sort_key and sort_key is not None:
            raise SortKeyNotSupported(table)

    def ensure_composite(self, table: str) -> None:
        """Partition queries are allowed only for tables with a sort key."""
        if not self.get(table).sort_key:
            raise SortKeyNotSupported(table)

    def matches(self, table: str, sort_key: str | None) -> bool:
        if not self.is_registered(table):
            return False
        return bool(self._tables[table].sort_key) == (sort_key is not None)
