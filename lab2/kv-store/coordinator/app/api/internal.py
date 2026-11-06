import logging

from fastapi import APIRouter, Depends

from app.core.config import REPLICATION_FACTOR
from app.core.constants import (
    INTERNAL_PREFIX,
    MODE_SHARDED,
    MODE_SINGLE_NODE,
    STATUS_REGISTERED,
    TAG_INTERNAL,
)
from app.dependencies import get_quorum, get_shard_registry
from app.schemas import (
    ClusterState,
    QuorumConfig,
    QuorumState,
    ReplicaRegistration,
    ShardRegistration,
)
from app.services.quorum import QuorumSettings
from app.services.shards import ShardRegistry

router = APIRouter(prefix=INTERNAL_PREFIX, tags=[TAG_INTERNAL])
log = logging.getLogger("uvicorn.error")


@router.post("/shards", response_model=ShardRegistration)
def register_replica(registration: ReplicaRegistration,
                     registry: ShardRegistry = Depends(get_shard_registry)):
    result = registry.register(registration)
    shard = registry.get(registration.shard_id)

    if result == STATUS_REGISTERED:
        log.info("Registered %s of %s at %s (%d/%d replicas)",
                 registration.replica_id, registration.shard_id, registration.url,
                 len(shard.replicas), REPLICATION_FACTOR)

    return ShardRegistration(status=result, shard=shard)


@router.get("/shards", response_model=ClusterState)
def cluster_state(registry: ShardRegistry = Depends(get_shard_registry)):
    mode = MODE_SINGLE_NODE if registry.is_empty() else MODE_SHARDED
    return ClusterState(mode=mode, replication_factor=REPLICATION_FACTOR,
                        shards=registry.list())


@router.get("/quorum", response_model=QuorumState)
def read_quorum_settings(quorum: QuorumSettings = Depends(get_quorum)):
    return quorum.state()


@router.put("/quorum", response_model=QuorumState)
def change_quorum_settings(config: QuorumConfig, quorum: QuorumSettings = Depends(get_quorum)):
    quorum.change(config.write_quorum, config.read_quorum)
    log.info("Quorum changed to W=%d, R=%d, N=%d", quorum.write_quorum, quorum.read_quorum,
             quorum.replication_factor)
    return quorum.state()
