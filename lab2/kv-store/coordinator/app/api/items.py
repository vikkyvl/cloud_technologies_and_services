"""HTTP endpoints for records. Only HTTP details here, rules live in ItemService."""
from typing import Any

from fastapi import APIRouter, Body, Depends, Response, status

from app.core.constants import HEADER_SHARD, ITEMS_PREFIX, TAG_ITEMS
from app.dependencies import get_item_service
from app.schemas import Item
from app.services.items import ItemService

# sort_key is null for simple tables, so it is hidden in responses
router = APIRouter(prefix=ITEMS_PREFIX, tags=[TAG_ITEMS])


def shard_header(service: ItemService, key: str) -> dict[str, str]:
    return {HEADER_SHARD: service.locate(key)}


@router.head("")
async def exists_item(table: str, key: str,
                      service: ItemService = Depends(get_item_service)):
    found = await service.exists(table, key)
    code = status.HTTP_200_OK if found else status.HTTP_404_NOT_FOUND
    return Response(status_code=code, headers=shard_header(service, key))


@router.put("", status_code=status.HTTP_201_CREATED, response_model=Item, response_model_exclude_none=True)
async def create_item(table: str, key: str, response: Response, value: Any = Body(...),
                      service: ItemService = Depends(get_item_service)):
    item = await service.create(table, key, value)
    response.headers.update(shard_header(service, key))
    return item


@router.get("", response_model=Item, response_model_exclude_none=True)
async def read_item(table: str, key: str, response: Response,
                    service: ItemService = Depends(get_item_service)):
    item = await service.read(table, key)
    response.headers.update(shard_header(service, key))
    return item


@router.patch("", response_model=Item, response_model_exclude_none=True)
async def update_item(table: str, key: str, response: Response, value: Any = Body(...),
                      service: ItemService = Depends(get_item_service)):
    item = await service.update(table, key, value)
    response.headers.update(shard_header(service, key))
    return item


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(table: str, key: str,
                      service: ItemService = Depends(get_item_service)):
    await service.delete(table, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=shard_header(service, key))
