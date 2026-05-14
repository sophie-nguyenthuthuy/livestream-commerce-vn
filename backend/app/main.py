from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.redis import close_redis
from app.schemas.common import HealthResponse

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

REQ_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQ_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", env=settings.app_env, version=__version__)
    yield
    await close_redis()
    logger.info("shutdown")


app = FastAPI(
    title="Livestream Commerce VN",
    version=__version__,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    method = request.method
    path = request.url.path
    with REQ_LATENCY.labels(method, path).time():
        response = await call_next(request)
    REQ_COUNT.labels(method, path, response.status_code).inc()
    return response


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"},
    )


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(version=__version__, env=settings.app_env)


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(api_router, prefix=settings.api_prefix)


# Quick orjson sanity check (catches breakage early in container boot)
assert orjson.dumps({"ok": True}) == b'{"ok":true}'
