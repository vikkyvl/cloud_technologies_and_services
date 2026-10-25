"""Constants of the shard service."""

API_TITLE = "KV Store Shard"
API_VERSION = "1.0.0"

ITEMS_PREFIX = "/tables/{table}/items/{key}"
REGISTER_PATH = "/internal/shards"

TAG_ITEMS = "Items"
TAG_DEBUG = "Debug"

STATUS_REGISTERED = "registered"

MSG_KEY_NOT_FOUND = "Key '{key}' not found"
MSG_KEY_EXISTS = "Key '{key}' already exists"
