import os

from app.core.constants import DEFAULT_NODE_ID

NODE_ID = os.environ.get("NODE_ID", DEFAULT_NODE_ID)
SHARD_TIMEOUT = float(os.environ.get("SHARD_TIMEOUT", "5"))
HASH_STRATEGY = os.environ.get("HASH_STRATEGY", "ring")
VNODES = int(os.environ.get("VNODES", "100"))
REPLICATION_FACTOR = int(os.environ.get("REPLICATION_FACTOR", "3"))
REPLICA_TTL = float(os.environ.get("REPLICA_TTL", "30"))
