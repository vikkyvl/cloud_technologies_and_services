"""HTTP endpoints for tables."""
from fastapi import APIRouter, Depends, status

from app.core.constants import TABLES_PREFIX, TAG_TABLES
from app.dependencies import get_table_registry
from app.schemas import TableDefinition
from app.services.tables import TableRegistry

router = APIRouter(prefix=TABLES_PREFIX, tags=[TAG_TABLES])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TableDefinition)
def create_table(definition: TableDefinition,
                 registry: TableRegistry = Depends(get_table_registry)):
    return registry.register(definition)


@router.get("", response_model=dict[str, str])
def list_tables(registry: TableRegistry = Depends(get_table_registry)):
    return registry.list()
