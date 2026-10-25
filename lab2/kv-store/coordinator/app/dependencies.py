"""Composition root: creates shared objects and gives them to the API layer."""
from app.core.config import HASH_STRATEGY, NODE_ID, SHARD_TIMEOUT, VNODES
from app.core.constants import STRATEGY_MODULO
from app.services.items import ItemService
from app.services.shards import ShardRegistry
from app.services.tables import TableRegistry
from app.storage.hashing import ModuloRouter, ShardRouter
from app.storage.memory import InMemoryStorage
from app.storage.ring import ConsistentHashRouter
from app.storage.sharded import ShardedStorage


def make_router() -> ShardRouter:
    if HASH_STRATEGY == STRATEGY_MODULO:
        return ModuloRouter()
    return ConsistentHashRouter(vnodes=VNODES)


table_registry = TableRegistry()
shard_registry = ShardRegistry()
router = make_router()
storage = ShardedStorage(
    registry=shard_registry,
    router=router,
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
