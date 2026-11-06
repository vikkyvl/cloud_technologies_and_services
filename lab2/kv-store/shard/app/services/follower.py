import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.errors import KafkaError

from ..storage.memory import InMemoryStorage
from .replication import apply_event

log = logging.getLogger("uvicorn.error")


def deserialize(raw: bytes) -> dict:
    return json.loads(raw.decode())


class LogFollower:
    def __init__(self, storage: InMemoryStorage, bootstrap: str, topic: str, retry_interval: float):
        self._storage = storage
        self._bootstrap = bootstrap
        self._partition = TopicPartition(topic, 0)
        self._retry_interval = retry_interval
        self._task: asyncio.Task | None = None
        self.applied_offset = -1

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
            consumer.seek(self._partition, self.applied_offset + 1)

            while True:
                batch = await consumer.getmany(self._partition, timeout_ms=1000)
                for record in batch.get(self._partition, []):
                    await self._apply(record.offset, record.value)
        finally:
            await consumer.stop()

    async def _apply(self, offset: int, event: dict) -> None:
        if await apply_event(self._storage, event):
            log.info("Applied offset %d: %s %s/%s v%d", offset, event["op"], event["table"],
                     event["key"], event["version"])

        self.applied_offset = offset
