"""Settings read from environment variables."""
import os

from app.core.constants import DEFAULT_NODE_ID

# Identifier of this node in single-node mode
NODE_ID = os.environ.get("NODE_ID", DEFAULT_NODE_ID)
# Timeout (seconds) for requests from the coordinator to shards
SHARD_TIMEOUT = float(os.environ.get("SHARD_TIMEOUT", "5"))
HASH_STRATEGY = os.environ.get("HASH_STRATEGY", "ring")
# Number of virtual nodes of every shard on the hash ring
VNODES = int(os.environ.get("VNODES", "100"))