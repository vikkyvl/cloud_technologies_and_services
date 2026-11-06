from fastapi import status

from app.core.constants import (
    MSG_KEY_EXISTS,
    MSG_KEY_NOT_FOUND,
    MSG_INVALID_QUORUM,
    MSG_QUORUM_NOT_REACHED,
    MSG_READ_QUORUM_NOT_REACHED,
    MSG_REPLICA_SET_FULL,
    MSG_SHARD_UNAVAILABLE,
    MSG_SORT_KEY_NOT_SUPPORTED,
    MSG_SORT_KEY_REQUIRED,
    MSG_TABLE_EXISTS,
    MSG_TABLE_NOT_FOUND,
)


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TableNotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, table: str):
        super().__init__(MSG_TABLE_NOT_FOUND.format(table=table))


class TableAlreadyExists(DomainError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, table: str):
        super().__init__(MSG_TABLE_EXISTS.format(table=table))


class KeyNotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, key: str):
        super().__init__(MSG_KEY_NOT_FOUND.format(key=key))


class KeyAlreadyExists(DomainError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, key: str):
        super().__init__(MSG_KEY_EXISTS.format(key=key))


class ShardUnavailable(DomainError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, shard: str):
        super().__init__(MSG_SHARD_UNAVAILABLE.format(shard=shard))


class SortKeyRequired(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, table: str):
        super().__init__(MSG_SORT_KEY_REQUIRED.format(table=table))


class SortKeyNotSupported(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, table: str):
        super().__init__(MSG_SORT_KEY_NOT_SUPPORTED.format(table=table))


class ReplicaSetFull(DomainError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, shard: str, count: int):
        super().__init__(MSG_REPLICA_SET_FULL.format(shard=shard, count=count))


class WriteQuorumNotReached(DomainError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, shard: str, acks: int, required: int):
        super().__init__(MSG_QUORUM_NOT_REACHED.format(shard=shard, acks=acks, required=required))


class ReadQuorumNotReached(DomainError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, shard: str, answers: int, required: int):
        super().__init__(MSG_READ_QUORUM_NOT_REACHED.format(shard=shard, answers=answers,
                                                            required=required))


class InvalidQuorum(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, replicas: int):
        super().__init__(MSG_INVALID_QUORUM.format(replicas=replicas))
