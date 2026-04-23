from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("\"'")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env: {name}")
    return value


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_host: str
    api_port: int
    dashboard_origin: str
    dashboard_origins: tuple[str, ...]


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


def _build_dashboard_origins() -> tuple[str, ...]:
    explicit = os.environ.get("DASHBOARD_ORIGINS", "")
    origins: list[str] = []

    if explicit:
        origins.extend(
            _normalize_origin(origin)
            for origin in explicit.split(",")
            if origin.strip()
        )

    configured_origin = os.environ.get("DASHBOARD_ORIGIN")
    dashboard_port = _int_env("DASHBOARD_PORT", 3000)

    defaults = [
        configured_origin or f"http://localhost:{dashboard_port}",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    origins.extend(_normalize_origin(origin) for origin in defaults if origin)

    deduped: list[str] = []
    for origin in origins:
        if origin and origin not in deduped:
            deduped.append(origin)
    return tuple(deduped)


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[3]
    _load_dotenv(root / ".env")
    _load_dotenv(Path.cwd() / ".env")

    dashboard_origins = _build_dashboard_origins()
    return Settings(
        database_url=_required_env("DATABASE_URL"),
        api_host=os.environ.get("API_HOST", "0.0.0.0"),
        api_port=_int_env("API_PORT", 8000),
        dashboard_origin=dashboard_origins[0],
        dashboard_origins=dashboard_origins,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
