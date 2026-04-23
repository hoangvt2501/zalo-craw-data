"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import close_pool, open_db_conn
from app.routers.deals import router as deals_router
from app.routers.messages import router as messages_router
from app.routers.metrics import router as metrics_router


settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage startup/shutdown lifecycle."""
    # Startup
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_asyncio_exception_handler)
    yield
    # Shutdown
    close_pool()


app = FastAPI(title="Hotel Intel API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.dashboard_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals_router)
app.include_router(messages_router)
app.include_router(metrics_router)


def _asyncio_exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    exception = context.get("exception")
    handle = context.get("handle")

    if isinstance(exception, ConnectionResetError) and getattr(exception, "winerror", None) == 10054:
        if "_ProactorBasePipeTransport._call_connection_lost" in repr(handle):
            return

    loop.default_exception_handler(context)


@app.get("/health")
def health():
    with open_db_conn() as conn:
        db_ok = conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1

    return {
        "status": "ok",
        "database": "ok" if db_ok else "error",
        "dashboard_origin": settings.dashboard_origin,
        "dashboard_origins": list(settings.dashboard_origins),
    }
