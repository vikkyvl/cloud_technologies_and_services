"""Record operations executed by the shard on its own data."""
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Response, status

from ..core.config import SHARD_ID
from ..core.constants import ITEMS_PREFIX, MSG_KEY_EXISTS, MSG_KEY_NOT_FOUND, TAG_ITEMS
from ..dependencies import storage

router = APIRouter(prefix=ITEMS_PREFIX, tags=[TAG_ITEMS])


def item(key: str, value: Any) -> dict:
    return {"key": key, "value": value, "shard": SHARD_ID}


@router.head("")
async def exists_item(table: str, key: str):
    found = await storage.exists(table, key)
    return Response(status_code=status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND)


@router.put("", status_code=status.HTTP_201_CREATED)
async def create_item(table: str, key: str, value: Any = Body(...)):
    if not await storage.insert(table, key, value):
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_KEY_EXISTS.format(key=key))
    return item(key, value)


@router.get("")
async def read_item(table: str, key: str):
    value = await storage.get(table, key)
    if value is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_KEY_NOT_FOUND.format(key=key))
    return item(key, value)


@router.patch("")
async def update_item(table: str, key: str, value: Any = Body(...)):
    if not await storage.update(table, key, value):
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_KEY_NOT_FOUND.format(key=key))
    return item(key, value)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(table: str, key: str):
    if not await storage.delete(table, key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_KEY_NOT_FOUND.format(key=key))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
