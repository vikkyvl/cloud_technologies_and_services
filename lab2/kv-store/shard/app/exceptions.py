from fastapi import status

from .core.constants import MSG_KEY_EXISTS, MSG_KEY_NOT_FOUND, MSG_LOG_UNAVAILABLE, MSG_NOT_LEADER


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class KeyNotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, key: str):
        super().__init__(MSG_KEY_NOT_FOUND.format(key=key))


class KeyAlreadyExists(DomainError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, key: str):
        super().__init__(MSG_KEY_EXISTS.format(key=key))


class NotLeader(DomainError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, replica: str, shard: str):
        super().__init__(MSG_NOT_LEADER.format(replica=replica, shard=shard))


class LogUnavailable(DomainError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self):
        super().__init__(MSG_LOG_UNAVAILABLE)
