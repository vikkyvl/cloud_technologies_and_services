from typing import Any

from fastapi import APIRouter, Body, Response, status
from fastapi.responses import JSONResponse

from ..core.config import SHARD_ID
from ..core.constants import HEADER_OFFSET, ITEMS_PREFIX, MSG_KEY_NOT_FOUND, TAG_ITEMS
from ..dependencies import read_headers, replication_service, storage

router = APIRouter(prefix=ITEMS_PREFIX, tags=[TAG_ITEMS])


def item(key: str, value: Any, written: dict | None = None) -> dict:
    result = {"key": key, "value": value, "shard": SHARD_ID}
    if written is not None:
        result.update(version=written["version"], offset=written["offset"])

    return result


@router.head("")
async def exists_item(table: str, key: str):
    found = await storage.exists(table, key)
    return Response(status_code=status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND,
                    headers=read_headers(table, key))


@router.put("", status_code=status.HTTP_201_CREATED)
async def create_item(table: str, key: str, response: Response, value: Any = Body(...)):
    written = await replication_service.create(table, key, value)
    response.headers[HEADER_OFFSET] = str(written["offset"])

    return item(key, value, written)


@router.get("")
async def read_item(table: str, key: str):
    value = await storage.get(table, key)
    headers = read_headers(table, key)

    if value is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, headers=headers,
                            content={"detail": MSG_KEY_NOT_FOUND.format(key=key)})

    return JSONResponse(content=item(key, value), headers=headers)


@router.patch("")
async def update_item(table: str, key: str, response: Response, value: Any = Body(...)):
    written = await replication_service.update(table, key, value)
    response.headers[HEADER_OFFSET] = str(written["offset"])

    return item(key, value, written)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(table: str, key: str):
    written = await replication_service.delete(table, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT,
                    headers={HEADER_OFFSET: str(written["offset"])})
