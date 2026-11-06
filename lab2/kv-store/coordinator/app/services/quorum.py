from app.exceptions import InvalidQuorum
from app.schemas import QuorumState


class QuorumSettings:
    def __init__(self, replication_factor: int, write_quorum: int, read_quorum: int,
                 timeout: float):
        self.replication_factor = replication_factor
        self.timeout = timeout
        self.write_quorum = write_quorum
        self.read_quorum = read_quorum
        self.change(write_quorum, read_quorum)

    def change(self, write_quorum: int, read_quorum: int) -> None:
        for value in (write_quorum, read_quorum):
            if not 1 <= value <= self.replication_factor:
                raise InvalidQuorum(self.replication_factor)

        self.write_quorum = write_quorum
        self.read_quorum = read_quorum

    @property
    def consistent(self) -> bool:
        return self.read_quorum + self.write_quorum > self.replication_factor

    def state(self) -> QuorumState:
        return QuorumState(replication_factor=self.replication_factor,
                           write_quorum=self.write_quorum, read_quorum=self.read_quorum,
                           consistent=self.consistent)
