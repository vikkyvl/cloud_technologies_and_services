"""Request and response models (match components/schemas in openapi.yaml)."""
from typing import Any

from pydantic import BaseModel, Field


class TableDefinition(BaseModel):
    name: str = Field(min_length=1, examples=["users"])
    partition_key: str = Field(min_length=1, examples=["id"])


class Item(BaseModel):
    key: str
    value: Any
    shard: str


class Shard(BaseModel):
    id: str = Field(min_length=1, examples=["shard-0"])
    url: str = Field(min_length=1, examples=["http://shard0:8000"])


class ShardRegistration(BaseModel):
    status: str
    shards: list[Shard]


class ClusterState(BaseModel):
    mode: str
    shards: list[Shard]
