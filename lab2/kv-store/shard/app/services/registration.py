"""Registration of the shard in the coordinator."""
import asyncio
import logging

import httpx

from ..core.config import COORDINATOR_URL, REGISTER_INTERVAL, SHARD_ID, SHARD_URL
from ..core.constants import REGISTER_PATH, STATUS_REGISTERED

log = logging.getLogger("uvicorn.error")


async def register_once(client: httpx.AsyncClient) -> None:
    r = await client.post(f"{COORDINATOR_URL}{REGISTER_PATH}",
                          json={"id": SHARD_ID, "url": SHARD_URL})
    r.raise_for_status()
    if r.json()["status"] == STATUS_REGISTERED:
        log.info("%s registered at coordinator %s", SHARD_ID, COORDINATOR_URL)


async def registration_loop() -> None:
    """Register on startup and repeat periodically.
    If the coordinator is not up yet or was restarted, the shard registers again."""
    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            try:
                await register_once(client)
            except httpx.HTTPError as e:
                log.warning("Coordinator is not available yet: %s", e)
            await asyncio.sleep(REGISTER_INTERVAL)
