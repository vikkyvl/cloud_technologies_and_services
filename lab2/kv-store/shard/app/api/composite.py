"""Operations on records with a composite key (partition key + sort key) stored on this shard."""
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Response, status

from ..core.config import SHARD_ID
from ..core.constants import (
    COMPOSITE_ITEMS_PREFIX,
    MSG_KEY_EXISTS,
    MSG_KEY_NOT_FOUND,
    PARTITION_PREFIX,
    TAG_COMPOSITE,
)
from ..dependencies import storage

router = APIRouter(tags=[TAG_COMPOSITE])


def item(key: str, sort_key: str, value: Any) -> dict:
    return {"key": key, "sort_key": sort_key, "value": value, "shard": SHARD_ID}


def not_found(key: str, sort_key: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, MSG_KEY_NOT_FOUND.format(key=f"{key}/{sort_key}"))


@router.head(COMPOSITE_ITEMS_PREFIX)
async def exists_composite(table: str, key: str, sort_key: str):
    found = await storage.exists(table, key, sort_key)
    return Response(status_code=status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND)


@router.put(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_201_CREATED)
async def create_composite(table: str, key: str, sort_key: str, value: Any = Body(...)):
    if not await storage.insert(table, key, value, sort_key):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            MSG_KEY_EXISTS.format(key=f"{key}/{sort_key}"))
    return item(key, sort_key, value)


@router.get(COMPOSITE_ITEMS_PREFIX)
async def read_composite(table: str, key: str, sort_key: str):
    value = await storage.get(table, key, sort_key)
    if value is None:
        raise not_found(key, sort_key)
    return item(key, sort_key, value)


@router.patch(COMPOSITE_ITEMS_PREFIX)
async def update_composite(table: str, key: str, sort_key: str, value: Any = Body(...)):
    if not await storage.update(table, key, value, sort_key):
        raise not_found(key, sort_key)
    return item(key, sort_key, value)


@router.delete(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_204_NO_CONTENT)
async def delete_composite(table: str, key: str, sort_key: str):
    if not await storage.delete(table, key, sort_key):
        raise not_found(key, sort_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(PARTITION_PREFIX)
async def query_partition(table: str, key: str,
                          sk_from: str | None = Query(None), sk_to: str | None = Query(None)):
    rows = await storage.query(table, key, sk_from, sk_to)
    return {"partition_key": key, "shard": SHARD_ID,
            "items": [{"sort_key": sk, "value": v} for sk, v in rows]}
