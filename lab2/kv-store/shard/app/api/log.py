from fastapi import APIRouter, Query

from ..core.config import REPLICA_ID, SHARD_ID
from ..core.constants import LOG_PATH, TAG_REPLICATION
from ..dependencies import replication_log

router = APIRouter(tags=[TAG_REPLICATION])


@router.get(LOG_PATH)
async def read_log(from_offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    events = await replication_log.read(from_offset, limit)
    return {"shard": SHARD_ID, "replica": REPLICA_ID, "topic": replication_log.topic,
            "events": events}
