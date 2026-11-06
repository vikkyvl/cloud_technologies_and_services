import asyncio
import logging

import httpx

from ..core.config import COORDINATOR_URL, REGISTER_INTERVAL, REPLICA_ID, SHARD_ID, SHARD_URL
from ..core.constants import REGISTER_PATH, STATUS_REGISTERED
from ..dependencies import replica_state

log = logging.getLogger("uvicorn.error")


async def register_once(client: httpx.AsyncClient) -> None:
    payload = {"shard_id": SHARD_ID, "replica_id": REPLICA_ID, "url": SHARD_URL}
    response = await client.post(f"{COORDINATOR_URL}{REGISTER_PATH}", json=payload)
    response.raise_for_status()

    body = response.json()
    previous_role = replica_state.role
    replica_state.update(body["shard"])

    if body["status"] == STATUS_REGISTERED:
        log.info("%s of %s registered at coordinator %s", REPLICA_ID, SHARD_ID, COORDINATOR_URL)

    if replica_state.role != previous_role:
        log.info("%s is now %s", REPLICA_ID, replica_state.role)


async def registration_loop() -> None:
    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            try:
                await register_once(client)
            except httpx.HTTPError as error:
                log.warning("Coordinator is not available yet: %s", error)

            await asyncio.sleep(REGISTER_INTERVAL)
