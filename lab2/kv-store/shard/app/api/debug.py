"""Debug endpoint: shows what is stored on this shard."""
from fastapi import APIRouter

from ..core.config import SHARD_ID
from ..core.constants import TAG_DEBUG
from ..dependencies import storage

router = APIRouter(tags=[TAG_DEBUG])


@router.get("/dump")
def dump():
    return {"shard": SHARD_ID, "data": storage.dump()}
