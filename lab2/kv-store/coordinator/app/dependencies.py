"""Composition root: creates shared objects and gives them to the API layer."""
from app.core.config import NODE_ID, SHARD_TIMEOUT
from app.services.items import ItemService
from app.services.shards import ShardRegistry
from app.services.tables import TableRegistry
from app.storage.memory import InMemoryStorage
from app.storage.sharded import ShardedStorage

table_registry = TableRegistry()
shard_registry = ShardRegistry()
storage = ShardedStorage(
    registry=shard_registry,
    fallback=InMemoryStorage(node_id=NODE_ID),
    timeout=SHARD_TIMEOUT,
)
item_service = ItemService(table_registry, storage)


def get_table_registry() -> TableRegistry:
    return table_registry


def get_shard_registry() -> ShardRegistry:
    return shard_registry


def get_item_service() -> ItemService:
    return item_service
