import os

SHARD_ID = os.environ.get("SHARD_ID", "shard-0")
REPLICA_ID = os.environ.get("REPLICA_ID", f"{SHARD_ID}-r0")
SHARD_URL = os.environ.get("SHARD_URL", "http://localhost:8001")
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "http://localhost:8000")
REGISTER_INTERVAL = float(os.environ.get("REGISTER_INTERVAL", "10"))
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
LOG_TOPIC = os.environ.get("LOG_TOPIC", f"kv-{SHARD_ID}")
KAFKA_RETRY_INTERVAL = float(os.environ.get("KAFKA_RETRY_INTERVAL", "2"))
