import json
import os


class SnapshotStore:
    def __init__(self, directory: str, replica_id: str):
        self._path = os.path.join(directory, f"{replica_id}.json")

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> dict | None:
        if not os.path.exists(self._path):
            return None

        with open(self._path, encoding="utf-8") as file:
            return json.load(file)

    def save(self, snapshot: dict) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        temporary_path = f"{self._path}.tmp"

        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(snapshot, file)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, self._path)
