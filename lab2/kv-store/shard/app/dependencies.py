from .core.config import (
    KAFKA_BOOTSTRAP,
    KAFKA_RETRY_INTERVAL,
    LOG_TOPIC,
    REPLICA_ID,
    SHARD_ID,
    STATE_DIR,
)
from .core.constants import HEADER_APPLIED_OFFSET, HEADER_VERSION
from .services.follower import LogFollower
from .services.log import ReplicationLog
from .services.replication import ReplicationService
from .services.snapshot import SnapshotStore
from .services.state import ReplicaState
from .storage.memory import InMemoryStorage

storage = InMemoryStorage(node_id=SHARD_ID)
replica_state = ReplicaState(replica_id=REPLICA_ID)
replication_log = ReplicationLog(KAFKA_BOOTSTRAP, LOG_TOPIC, KAFKA_RETRY_INTERVAL)
replication_service = ReplicationService(storage, replication_log, replica_state, SHARD_ID)
snapshots = SnapshotStore(STATE_DIR, REPLICA_ID)
log_follower = LogFollower(storage, snapshots, KAFKA_BOOTSTRAP, LOG_TOPIC, KAFKA_RETRY_INTERVAL)


def replica_offset() -> int:
    return max(log_follower.applied_offset, replication_service.last_offset)


def read_headers(table: str, key: str, sort_key: str | None = None) -> dict[str, str]:
    return {
        HEADER_VERSION: str(storage.version(table, key, sort_key)),
        HEADER_APPLIED_OFFSET: str(replica_offset()),
    }
