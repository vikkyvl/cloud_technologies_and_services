from typing import Any

from pydantic import BaseModel, Field


class TableDefinition(BaseModel):
    name: str = Field(min_length=1, examples=["orders"])
    partition_key: str = Field(min_length=1, examples=["user_id"])
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


class ReplicaRegistration(BaseModel):
    shard_id: str = Field(min_length=1, examples=["shard-0"])
    replica_id: str = Field(min_length=1, examples=["shard-0-r1"])
    url: str = Field(min_length=1, examples=["http://shard0-r1:8000"])


class Replica(BaseModel):
    id: str
    url: str
    role: str
    alive: bool


class Shard(BaseModel):
    id: str
    replicas: list[Replica]
    complete: bool

    @property
    def leader(self) -> Replica:
        return self.replicas[0]

    @property
    def followers(self) -> list[Replica]:
        return self.replicas[1:]


class ShardRegistration(BaseModel):
    status: str
    shard: Shard


class ClusterState(BaseModel):
    mode: str
    replication_factor: int
    shards: list[Shard]


class QuorumConfig(BaseModel):
    write_quorum: int = Field(ge=1, examples=[2])
    read_quorum: int = Field(ge=1, examples=[2])


class QuorumState(BaseModel):
    replication_factor: int
    write_quorum: int
    read_quorum: int
    consistent: bool
