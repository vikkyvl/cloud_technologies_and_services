"""Shared objects of the shard."""
from .core.config import SHARD_ID
from .storage.memory import InMemoryStorage

storage = InMemoryStorage(node_id=SHARD_ID)
