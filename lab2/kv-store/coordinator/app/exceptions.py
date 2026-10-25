"""Domain errors. Services raise them, the API layer maps them to HTTP codes."""
from fastapi import status

from app.core.constants import (
    MSG_KEY_EXISTS,
    MSG_KEY_NOT_FOUND,
    MSG_SHARD_UNAVAILABLE,
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
