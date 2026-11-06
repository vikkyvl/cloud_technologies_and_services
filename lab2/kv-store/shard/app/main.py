import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import composite, debug, items, log
from .core.config import REPLICA_ID
from .core.constants import API_TITLE, API_VERSION
from .dependencies import log_follower, replication_log
from .exceptions import DomainError
from .services.registration import registration_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_follower.restore()
    await replication_log.start()
    log_follower.start()
    task = asyncio.create_task(registration_loop())
    yield
    task.cancel()
    await log_follower.stop()
    await replication_log.stop()


app = FastAPI(title=f"{API_TITLE} {REPLICA_ID}", version=API_VERSION, lifespan=lifespan)

app.include_router(items.router)
app.include_router(composite.router)
app.include_router(log.router)
app.include_router(debug.router)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
