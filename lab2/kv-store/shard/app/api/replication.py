from fastapi import APIRouter

from ..core.config import REPLICA_ID
from ..core.constants import REPLICATION_PREFIX, TAG_REPLICATION
from ..dependencies import log_follower, replica_offset

router = APIRouter(prefix=REPLICATION_PREFIX, tags=[TAG_REPLICATION])


def status() -> dict:
    return {"replica": REPLICA_ID, "applied_offset": replica_offset(),
            "paused": log_follower.paused}


@router.get("/offset")
async def applied_offset():
    return status()


@router.post("/pause")
async def pause():
    log_follower.paused = True
    return status()


@router.post("/resume")
async def resume():
    log_follower.paused = False
    return status()
