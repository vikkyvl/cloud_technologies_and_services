from ..core.constants import ROLE_LEADER, ROLE_UNKNOWN


class ReplicaState:
    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.role = ROLE_UNKNOWN
        self.leader_url: str | None = None

    def update(self, shard: dict) -> None:
        replicas = shard["replicas"]
        for replica in replicas:
            if replica["id"] == self.replica_id:
                self.role = replica["role"]

        self.leader_url = replicas[0]["url"]

    @property
    def is_leader(self) -> bool:
        return self.role == ROLE_LEADER
