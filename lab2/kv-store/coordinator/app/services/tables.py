"""Registry of table definitions (metadata is always kept in the coordinator)."""
from app.exceptions import TableAlreadyExists, TableNotFound
from app.schemas import TableDefinition


class TableRegistry:
    def __init__(self):
        self._tables: dict[str, str] = {}  # table name -> partition key name

    def register(self, definition: TableDefinition) -> TableDefinition:
        if definition.name in self._tables:
            raise TableAlreadyExists(definition.name)
        self._tables[definition.name] = definition.partition_key
        return definition

    def list(self) -> dict[str, str]:
        return dict(self._tables)

    def ensure_exists(self, table: str) -> None:
        if table not in self._tables:
            raise TableNotFound(table)

    def is_registered(self, table: str) -> bool:
        return table in self._tables
