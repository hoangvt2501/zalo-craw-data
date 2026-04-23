"""Database connection management using a connection pool.

Uses psycopg_pool for efficient connection reuse instead of creating
a new TCP connection for every request.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the global connection pool (lazy init)."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row, "autocommit": True},
        )
    return _pool


def close_pool() -> None:
    """Close the pool. Called on app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def open_db_conn():
    """Get a connection from the pool, automatically returned on exit."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def get_db_conn() -> Generator:
    """FastAPI dependency that yields a pooled DB connection."""
    with open_db_conn() as conn:
        yield conn
