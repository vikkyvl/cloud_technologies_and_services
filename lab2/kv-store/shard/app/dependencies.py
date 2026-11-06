from .core.config import KAFKA_BOOTSTRAP, KAFKA_RETRY_INTERVAL, LOG_TOPIC, REPLICA_ID, SHARD_ID
from .services.follower import LogFollower
from .services.log import ReplicationLog
from .services.replication import ReplicationService
from .services.state import ReplicaState
from .storage.memory import InMemoryStorage

storage = InMemoryStorage(node_id=SHARD_ID)
replica_state = ReplicaState(replica_id=REPLICA_ID)
replication_log = ReplicationLog(KAFKA_BOOTSTRAP, LOG_TOPIC, KAFKA_RETRY_INTERVAL)
replication_service = ReplicationService(storage, replication_log, replica_state, SHARD_ID)
log_follower = LogFollower(storage, KAFKA_BOOTSTRAP, LOG_TOPIC, KAFKA_RETRY_INTERVAL)
