"""Entry point of the shard service."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import debug, items
from .core.config import SHARD_ID
from .core.constants import API_TITLE, API_VERSION
from .services.registration import registration_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(registration_loop())  # register at the coordinator on startup
    yield
    task.cancel()


app = FastAPI(title=f"{API_TITLE} {SHARD_ID}", version=API_VERSION, lifespan=lifespan)
app.include_router(items.router)
app.include_router(debug.router)
