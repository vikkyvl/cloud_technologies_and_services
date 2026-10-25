"""Constants of the shard service."""

API_TITLE = "KV Store Shard"
API_VERSION = "1.0.0"

ITEMS_PREFIX = "/tables/{table}/items/{key}"
COMPOSITE_ITEMS_PREFIX = "/tables/{table}/items/{key}/{sort_key}"
PARTITION_PREFIX = "/tables/{table}/partitions/{key}"
REGISTER_PATH = "/internal/shards"

TAG_ITEMS = "Items"
TAG_DEBUG = "Debug"
TAG_COMPOSITE = "Composite key"

STATUS_REGISTERED = "registered"

MSG_KEY_NOT_FOUND = "Key '{key}' not found"
MSG_KEY_EXISTS = "Key '{key}' already exists"
