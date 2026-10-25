"""Constants used across the application."""

# ---------- API metadata ----------
API_TITLE = "Distributed KV Store API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Coordinator of the key-value store."

# ---------- routes ----------
TABLES_PREFIX = "/tables"
ITEMS_PREFIX = "/tables/{table}/items/{key}"
INTERNAL_PREFIX = "/internal"
SHARD_ITEM_URL = "{base}/tables/{table}/items/{key}"

# ---------- OpenAPI tags ----------
TAG_TABLES = "Tables"
TAG_ITEMS = "Items"
TAG_INTERNAL = "Internal"

# ---------- headers ----------
HEADER_SHARD = "X-Shard"

# ---------- nodes and modes ----------
DEFAULT_NODE_ID = "local"
MODE_SINGLE_NODE = "single-node"
MODE_SHARDED = "sharded"

# ---------- shard registration ----------
STATUS_REGISTERED = "registered"
STATUS_UPDATED = "updated"

# ---------- error messages ----------
MSG_TABLE_NOT_FOUND = "Table '{table}' is not registered"
MSG_TABLE_EXISTS = "Table '{table}' already exists"
MSG_KEY_NOT_FOUND = "Key '{key}' not found"
MSG_KEY_EXISTS = "Key '{key}' already exists"
MSG_SHARD_UNAVAILABLE = "Shard '{shard}' is unavailable"
