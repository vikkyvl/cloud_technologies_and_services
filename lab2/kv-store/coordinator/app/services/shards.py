"""Registry of shards that announced themselves to the coordinator."""
from app.core.constants import STATUS_REGISTERED, STATUS_UPDATED
from app.schemas import Shard


class ShardRegistry:
    def __init__(self):
        self._shards: dict[str, Shard] = {}  # shard id -> shard

    def register(self, shard: Shard) -> str:
        """Add a new shard or update the URL of a known one."""
        status = STATUS_UPDATED if shard.id in self._shards else STATUS_REGISTERED
        self._shards[shard.id] = shard
        return status

    def list(self) -> list[Shard]:
        """Shards sorted by id, so the order does not depend on registration order."""
        return [self._shards[k] for k in sorted(self._shards)]

    def is_empty(self) -> bool:
        return not self._shards
