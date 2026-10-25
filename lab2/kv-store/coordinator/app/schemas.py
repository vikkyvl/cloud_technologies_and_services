"""Request and response models (match components/schemas in openapi.yaml)."""
from typing import Any

from pydantic import BaseModel, Field


class TableDefinition(BaseModel):
    name: str = Field(min_length=1, examples=["orders"])
    partition_key: str = Field(min_length=1, examples=["user_id"])
    # Optional second part of the primary key. If set, records are addressed
    # by (partition key, sort key) and sorted by the sort key inside a partition.
    sort_key: str | None = Field(default=None, min_length=1, examples=["order_date"])


class Item(BaseModel):
    key: str
    sort_key: str | None = None
    value: Any
    shard: str


class PartitionItem(BaseModel):
    sort_key: str
    value: Any


class Partition(BaseModel):
    partition_key: str
    shard: str
    items: list[PartitionItem]


class Shard(BaseModel):
    id: str = Field(min_length=1, examples=["shard-0"])
    url: str = Field(min_length=1, examples=["http://shard0:8000"])


class ShardRegistration(BaseModel):
    status: str
    shards: list[Shard]


class ClusterState(BaseModel):
    mode: str
    shards: list[Shard]
