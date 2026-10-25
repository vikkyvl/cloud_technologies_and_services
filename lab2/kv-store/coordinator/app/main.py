"""Entry point: builds the FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import internal, items, tables
from app.core.constants import API_DESCRIPTION, API_TITLE, API_VERSION
from app.dependencies import storage
from app.exceptions import DomainError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await storage.close()  # close HTTP connections to shards on shutdown


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

app.include_router(tables.router)
app.include_router(items.router)
app.include_router(internal.router)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """Convert a domain error into an HTTP response {"detail": "..."}."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
