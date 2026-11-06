API_TITLE = "KV Store Shard"
API_VERSION = "1.0.0"

ITEMS_PREFIX = "/tables/{table}/items/{key}"
COMPOSITE_ITEMS_PREFIX = "/tables/{table}/items/{key}/{sort_key}"
PARTITION_PREFIX = "/tables/{table}/partitions/{key}"
REGISTER_PATH = "/internal/shards"
LOG_PATH = "/log"
REPLICATION_PREFIX = "/replication"

HEADER_VERSION = "X-Version"
HEADER_APPLIED_OFFSET = "X-Applied-Offset"
HEADER_OFFSET = "X-Offset"

TAG_ITEMS = "Items"
TAG_DEBUG = "Debug"
TAG_COMPOSITE = "Composite key"
TAG_REPLICATION = "Replication"

STATUS_REGISTERED = "registered"

ROLE_LEADER = "leader"
ROLE_FOLLOWER = "follower"
ROLE_UNKNOWN = "unknown"

OP_CREATE = "create"
OP_UPDATE = "update"
OP_DELETE = "delete"

MSG_KEY_NOT_FOUND = "Key '{key}' not found"
MSG_KEY_EXISTS = "Key '{key}' already exists"
MSG_NOT_LEADER = "Replica '{replica}' is not the leader of '{shard}'"
MSG_LOG_UNAVAILABLE = "Replication log is unavailable"
