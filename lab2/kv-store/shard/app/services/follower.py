import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.errors import KafkaError

from ..storage.memory import InMemoryStorage
from .replication import apply_event
from .snapshot import SnapshotStore

log = logging.getLogger("uvicorn.error")


def deserialize(raw: bytes) -> dict:
    return json.loads(raw.decode())


class LogFollower:
    def __init__(self, storage: InMemoryStorage, snapshots: SnapshotStore, bootstrap: str,
                 topic: str, retry_interval: float):
        self._storage = storage
        self._snapshots = snapshots
        self._bootstrap = bootstrap
        self._partition = TopicPartition(topic, 0)
        self._retry_interval = retry_interval
        self._task: asyncio.Task | None = None
        self.applied_offset = -1
        self.restored_offset: int | None = None
        self.paused = False

    def restore(self) -> None:
        snapshot = self._snapshots.load()
        if snapshot is None:
            log.info("No snapshot found, reading the log from the beginning")
            return

        self._storage.import_state(snapshot["state"])
        self.applied_offset = snapshot["applied_offset"]
        self.restored_offset = self.applied_offset
        log.info("Restored snapshot at offset %d, resuming from offset %d",
                 self.applied_offset, self.applied_offset + 1)

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    async def _run(self) -> None:
        while True:
            try:
                await self._follow()
            except KafkaError as error:
                log.warning("Log follower lost Kafka connection: %s", error)
                await asyncio.sleep(self._retry_interval)

    async def _follow(self) -> None:
        consumer = AIOKafkaConsumer(bootstrap_servers=self._bootstrap, enable_auto_commit=False,
                                    value_deserializer=deserialize)
        await consumer.start()

        try:
            consumer.assign([self._partition])
            await self._check_log_end(consumer)
            consumer.seek(self._partition, self.applied_offset + 1)

            while True:
                if self.paused:
                    await asyncio.sleep(0.2)
                    continue

                batch = await consumer.getmany(self._partition, timeout_ms=1000)
                records = batch.get(self._partition, [])
                for record in records:
                    await self._apply(record.offset, record.value)

                if records:
                    self._save_snapshot()
        finally:
            await consumer.stop()

    async def _check_log_end(self, consumer: AIOKafkaConsumer) -> None:
        end = (await consumer.end_offsets([self._partition]))[self._partition]
        if self.applied_offset < end:
            return

        log.warning("Snapshot offset %d is beyond the log end %d, starting from scratch",
                    self.applied_offset, end)
        self._storage.clear()
        self.applied_offset = -1

    async def _apply(self, offset: int, event: dict) -> None:
        if await apply_event(self._storage, event):
            log.info("Applied offset %d: %s %s/%s v%d", offset, event["op"], event["table"],
                     event["key"], event["version"])

        self.applied_offset = offset

    def _save_snapshot(self) -> None:
        snapshot = {"applied_offset": self.applied_offset, "state": self._storage.export_state()}
        self._snapshots.save(snapshot)
