from typing import Any

from fastapi import APIRouter, Body, Query, Response, status
from fastapi.responses import JSONResponse

from ..core.config import SHARD_ID
from ..core.constants import (
    COMPOSITE_ITEMS_PREFIX,
    HEADER_APPLIED_OFFSET,
    HEADER_OFFSET,
    MSG_KEY_NOT_FOUND,
    PARTITION_PREFIX,
    TAG_COMPOSITE,
)
from ..dependencies import read_headers, replica_offset, replication_service, storage

router = APIRouter(tags=[TAG_COMPOSITE])


def item(key: str, sort_key: str, value: Any, written: dict | None = None) -> dict:
    result = {"key": key, "sort_key": sort_key, "value": value, "shard": SHARD_ID}
    if written is not None:
        result.update(version=written["version"], offset=written["offset"])

    return result


@router.head(COMPOSITE_ITEMS_PREFIX)
async def exists_composite(table: str, key: str, sort_key: str):
    found = await storage.exists(table, key, sort_key)
    return Response(status_code=status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND,
                    headers=read_headers(table, key, sort_key))


@router.put(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_201_CREATED)
async def create_composite(table: str, key: str, sort_key: str, response: Response,
                           value: Any = Body(...)):
    written = await replication_service.create(table, key, value, sort_key)
    response.headers[HEADER_OFFSET] = str(written["offset"])

    return item(key, sort_key, value, written)


@router.get(COMPOSITE_ITEMS_PREFIX)
async def read_composite(table: str, key: str, sort_key: str):
    value = await storage.get(table, key, sort_key)
    headers = read_headers(table, key, sort_key)

    if value is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, headers=headers,
                            content={"detail": MSG_KEY_NOT_FOUND.format(key=f"{key}/{sort_key}")})

    return JSONResponse(content=item(key, sort_key, value), headers=headers)


@router.patch(COMPOSITE_ITEMS_PREFIX)
async def update_composite(table: str, key: str, sort_key: str, response: Response,
                           value: Any = Body(...)):
    written = await replication_service.update(table, key, value, sort_key)
    response.headers[HEADER_OFFSET] = str(written["offset"])

    return item(key, sort_key, value, written)


@router.delete(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_204_NO_CONTENT)
async def delete_composite(table: str, key: str, sort_key: str):
    written = await replication_service.delete(table, key, sort_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT,
                    headers={HEADER_OFFSET: str(written["offset"])})


@router.get(PARTITION_PREFIX)
async def query_partition(table: str, key: str,
                          sk_from: str | None = Query(None), sk_to: str | None = Query(None)):
    rows = await storage.query(table, key, sk_from, sk_to)
    items = [{"sort_key": sort_key, "value": value} for sort_key, value in rows]

    return JSONResponse(content={"partition_key": key, "shard": SHARD_ID, "items": items},
                        headers={HEADER_APPLIED_OFFSET: str(replica_offset())})
