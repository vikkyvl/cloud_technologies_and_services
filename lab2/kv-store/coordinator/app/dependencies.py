from app.core.config import (
    HASH_STRATEGY,
    NODE_ID,
    QUORUM_TIMEOUT,
    READ_QUORUM,
    REPLICA_TTL,
    REPLICATION_FACTOR,
    SHARD_TIMEOUT,
    VNODES,
    WRITE_QUORUM,
)
from app.core.constants import STRATEGY_MODULO
from app.services.items import ItemService
from app.services.quorum import QuorumSettings
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
shard_registry = ShardRegistry(replication_factor=REPLICATION_FACTOR, replica_ttl=REPLICA_TTL)
router = make_router()
quorum = QuorumSettings(REPLICATION_FACTOR, WRITE_QUORUM, READ_QUORUM, QUORUM_TIMEOUT)

storage = ShardedStorage(
    registry=shard_registry,
    router=router,
    fallback=InMemoryStorage(node_id=NODE_ID),
    quorum=quorum,
    timeout=SHARD_TIMEOUT,
)

item_service = ItemService(table_registry, storage)


def get_table_registry() -> TableRegistry:
    return table_registry


def get_shard_registry() -> ShardRegistry:
    return shard_registry


def get_quorum() -> QuorumSettings:
    return quorum


def get_item_service() -> ItemService:
    return item_service
