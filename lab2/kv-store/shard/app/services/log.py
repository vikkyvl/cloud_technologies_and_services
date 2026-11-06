import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, TopicPartition
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError, TopicAlreadyExistsError

from ..exceptions import LogUnavailable

log = logging.getLogger("uvicorn.error")


def serialize(event: dict) -> bytes:
    return json.dumps(event).encode()


def deserialize(raw: bytes) -> dict:
    return json.loads(raw.decode())


class ReplicationLog:
    def __init__(self, bootstrap: str, topic: str, retry_interval: float):
        self._bootstrap = bootstrap
        self._topic = topic
        self._retry_interval = retry_interval
        self._partition = TopicPartition(topic, 0)
        self._producer: AIOKafkaProducer | None = None

    @property
    def topic(self) -> str:
        return self._topic

    async def start(self) -> None:
        while True:
            try:
                await self._create_topic()
                producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap, acks="all",
                                            enable_idempotence=True, value_serializer=serialize)
                await producer.start()
                self._producer = producer
                log.info("Connected to Kafka %s, topic %s", self._bootstrap, self._topic)
                return
            except KafkaError as error:
                log.warning("Kafka is not available yet: %s", error)
                await asyncio.sleep(self._retry_interval)

    async def _create_topic(self) -> None:
        admin = AIOKafkaAdminClient(bootstrap_servers=self._bootstrap)
        await admin.start()
        try:
            await admin.create_topics([NewTopic(name=self._topic, num_partitions=1,
                                                replication_factor=1)])
        except TopicAlreadyExistsError:
            pass
        finally:
            await admin.close()

    async def append(self, event: dict) -> int:
        if self._producer is None:
            raise LogUnavailable()

        try:
            metadata = await self._producer.send_and_wait(self._topic, event,
                                                          key=event["key"].encode())
        except KafkaError:
            raise LogUnavailable()

        return metadata.offset

    async def read(self, from_offset: int, limit: int) -> list[dict]:
        consumer = AIOKafkaConsumer(bootstrap_servers=self._bootstrap, enable_auto_commit=False,
                                    value_deserializer=deserialize)
        try:
            await consumer.start()
            consumer.assign([self._partition])
            end = (await consumer.end_offsets([self._partition]))[self._partition]
            consumer.seek(self._partition, from_offset)

            events = []
            while len(events) < limit and await consumer.position(self._partition) < end:
                batch = await consumer.getmany(self._partition, timeout_ms=1000)
                for record in batch.get(self._partition, []):
                    events.append({"offset": record.offset, **record.value})

            return events[:limit]
        except KafkaError:
            raise LogUnavailable()
        finally:
            await consumer.stop()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
