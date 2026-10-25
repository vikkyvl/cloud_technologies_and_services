"""Settings of the shard read from environment variables."""
import os

# Unique id of this shard, for example shard-0
SHARD_ID = os.environ.get("SHARD_ID", "shard-0")
# Address at which the coordinator can reach this shard
SHARD_URL = os.environ.get("SHARD_URL", "http://localhost:8001")
# Address of the coordinator where the shard registers
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "http://localhost:8000")
# How often (seconds) the shard repeats registration
REGISTER_INTERVAL = float(os.environ.get("REGISTER_INTERVAL", "10"))
