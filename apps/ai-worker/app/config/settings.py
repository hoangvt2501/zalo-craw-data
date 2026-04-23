from __future__ import annotations

import os
from dataclasses import dataclass
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


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    clipproxyapi_base_url: str
    clipproxyapi_api_key: str
    extractor_model: str
    verifier_model: str
    ai_temperature: float
    ai_retry_max: int
    ai_retry_delay_ms: int
    ai_worker_batch_size: int
    match_candidate_min_score: float
    llm_verify_min_score: float
    llm_verify_max_score: float
    ai_verify_fail_open: bool
    worker_id: str


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[4]
    _load_dotenv(root / ".env")
    _load_dotenv(Path.cwd() / ".env")

    return Settings(
        database_url=_required_env("DATABASE_URL"),
        clipproxyapi_base_url=_required_env("CLIPPROXYAPI_BASE_URL"),
        clipproxyapi_api_key=_required_env("CLIPPROXYAPI_API_KEY"),
        extractor_model=os.environ.get("EXTRACTOR_MODEL", "gemini-3-flash-preview"),
        verifier_model=os.environ.get("VERIFIER_MODEL", "gemini-3-flash-preview"),
        ai_temperature=_float_env("AI_TEMPERATURE", 0),
        ai_retry_max=_int_env("AI_RETRY_MAX", 3),
        ai_retry_delay_ms=_int_env("AI_RETRY_DELAY_MS", 10000),
        ai_worker_batch_size=_int_env("AI_WORKER_BATCH_SIZE", 10),
        match_candidate_min_score=_float_env("MATCH_CANDIDATE_MIN_SCORE", 0.4),
        llm_verify_min_score=_float_env("LLM_VERIFY_MIN_SCORE", 0.4),
        llm_verify_max_score=_float_env("LLM_VERIFY_MAX_SCORE", 0.7),
        ai_verify_fail_open=_bool_env("AI_VERIFY_FAIL_OPEN", False),
        worker_id=os.environ.get("AI_WORKER_ID", "local-ai-worker-01"),
    )
