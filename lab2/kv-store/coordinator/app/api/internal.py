"""Internal endpoints: shard registration and cluster state."""
import logging

from fastapi import APIRouter, Depends

from app.core.constants import (
    INTERNAL_PREFIX,
    MODE_SHARDED,
    MODE_SINGLE_NODE,
    STATUS_REGISTERED,
    TAG_INTERNAL,
)
from app.dependencies import get_shard_registry
from app.schemas import ClusterState, Shard, ShardRegistration
from app.services.shards import ShardRegistry

router = APIRouter(prefix=INTERNAL_PREFIX, tags=[TAG_INTERNAL])
log = logging.getLogger("uvicorn.error")


@router.post("/shards", response_model=ShardRegistration)
def register_shard(shard: Shard, registry: ShardRegistry = Depends(get_shard_registry)):
    """Called by a shard on startup (and periodically, to survive coordinator restarts)."""
    result = registry.register(shard)
    if result == STATUS_REGISTERED:
        log.info("Registered %s at %s (total %d)", shard.id, shard.url, len(registry.list()))
    return ShardRegistration(status=result, shards=registry.list())


@router.get("/shards", response_model=ClusterState)
def cluster_state(registry: ShardRegistry = Depends(get_shard_registry)):
    mode = MODE_SINGLE_NODE if registry.is_empty() else MODE_SHARDED
    return ClusterState(mode=mode, shards=registry.list())
