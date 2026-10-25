"""HTTP endpoints for tables with a composite primary key (partition key + sort key)."""
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Response, status

from app.core.constants import COMPOSITE_ITEMS_PREFIX, HEADER_SHARD, PARTITION_PREFIX, TAG_COMPOSITE
from app.dependencies import get_item_service
from app.schemas import Item, Partition
from app.services.items import ItemService

router = APIRouter(tags=[TAG_COMPOSITE])


def shard_header(service: ItemService, key: str) -> dict[str, str]:
    return {HEADER_SHARD: service.locate(key)}


@router.head(COMPOSITE_ITEMS_PREFIX)
async def exists_composite(table: str, key: str, sort_key: str,
                           service: ItemService = Depends(get_item_service)):
    found = await service.exists(table, key, sort_key)
    code = status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND
    return Response(status_code=code, headers=shard_header(service, key))


@router.put(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_201_CREATED, response_model=Item)
async def create_composite(table: str, key: str, sort_key: str, response: Response,
                           value: Any = Body(...),
                           service: ItemService = Depends(get_item_service)):
    item = await service.create(table, key, value, sort_key)
    response.headers.update(shard_header(service, key))
    return item


@router.get(COMPOSITE_ITEMS_PREFIX, response_model=Item)
async def read_composite(table: str, key: str, sort_key: str, response: Response,
                         service: ItemService = Depends(get_item_service)):
    item = await service.read(table, key, sort_key)
    response.headers.update(shard_header(service, key))
    return item


@router.patch(COMPOSITE_ITEMS_PREFIX, response_model=Item)
async def update_composite(table: str, key: str, sort_key: str, response: Response,
                           value: Any = Body(...),
                           service: ItemService = Depends(get_item_service)):
    item = await service.update(table, key, value, sort_key)
    response.headers.update(shard_header(service, key))
    return item


@router.delete(COMPOSITE_ITEMS_PREFIX, status_code=status.HTTP_204_NO_CONTENT)
async def delete_composite(table: str, key: str, sort_key: str,
                           service: ItemService = Depends(get_item_service)):
    await service.delete(table, key, sort_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=shard_header(service, key))


@router.get(PARTITION_PREFIX, response_model=Partition)
async def query_partition(table: str, key: str, response: Response,
                          sk_from: str | None = Query(None, description="Lowest sort key"),
                          sk_to: str | None = Query(None, description="Highest sort key"),
                          service: ItemService = Depends(get_item_service)):
    """All records of one partition sorted by sort key (range is optional)."""
    partition = await service.query(table, key, sk_from, sk_to)
    response.headers.update(shard_header(service, key))
    return partition
