from fastapi import APIRouter

from ..core.config import REPLICA_ID, SHARD_ID
from ..core.constants import TAG_DEBUG
from ..dependencies import log_follower, replica_state, storage

router = APIRouter(tags=[TAG_DEBUG])


@router.get("/dump")
def dump():
    return {
        "shard": SHARD_ID,
        "replica": REPLICA_ID,
        "role": replica_state.role,
        "applied_offset": log_follower.applied_offset,
        "paused": log_follower.paused,
        "restored_offset": log_follower.restored_offset,
        "data": storage.dump(),
        "versions": storage.versions(),
    }
