"""AI Worker entry point.

Composition root that wires infrastructure implementations to ports,
then runs the polling loop with automatic DB reconnection.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.application.process_raw_message import ProcessingDeps, process_raw_message
from app.config.settings import load_settings
from app.infrastructure.audit import FileAuditLogger
from app.infrastructure.llm.clipproxy_client import ClipProxyClient
from app.infrastructure.llm.hotel_extractor_gateway import HotelExtractorGateway
from app.infrastructure.llm.property_verifier_gateway import PropertyVerifierGateway
from app.infrastructure.postgres.deal_repository import PostgresDealRepository
from app.infrastructure.postgres.event_repository import PostgresProcessingEventRepository
from app.infrastructure.postgres.job_repository import PostgresRawMessageJobRepository
from app.infrastructure.postgres.property_repository import PostgresPropertyRepository

MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_BASE_DELAY_S = 2.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hotel Intel AI Worker")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit")
    parser.add_argument("--limit", type=int, default=None, help="Override batch size")
    parser.add_argument("--sleep", type=float, default=3.0, help="Sleep seconds when no jobs")
    return parser.parse_args()


def create_connection(database_url: str) -> psycopg.Connection:
    """Create a new database connection with dict rows and autocommit."""
    return psycopg.connect(database_url, row_factory=dict_row, autocommit=True)


def build_deps(conn, settings, project_root: Path) -> ProcessingDeps:
    """Wire all concrete implementations to the typed dependency bag."""
    job_repo = PostgresRawMessageJobRepository(conn, settings.worker_id)
    deal_repo = PostgresDealRepository(conn)
    property_repo = PostgresPropertyRepository(conn)
    event_repo = PostgresProcessingEventRepository(conn)
    audit_logger = FileAuditLogger(settings.worker_id, project_root, event_repo)

    llm_client = ClipProxyClient(
        settings.clipproxyapi_base_url,
        settings.clipproxyapi_api_key,
        retry_max=settings.ai_retry_max,
        retry_delay_ms=settings.ai_retry_delay_ms,
    )
    extractor = HotelExtractorGateway(llm_client, settings.extractor_model, settings.ai_temperature)
    verifier = PropertyVerifierGateway(llm_client, settings.verifier_model, settings.ai_temperature)

    return ProcessingDeps(
        settings=settings,
        job_repository=job_repo,
        deal_repository=deal_repo,
        property_repository=property_repo,
        extractor=extractor,
        verifier=verifier,
        audit_logger=audit_logger,
    )


def main() -> None:
    args = parse_args()
    settings = load_settings()
    batch_size = args.limit or settings.ai_worker_batch_size
    project_root = Path(__file__).resolve().parents[3]

    print("=" * 60)
    print("Hotel Intel - AI Worker")
    print("=" * 60)
    print(f"Worker   : {settings.worker_id}")
    print(f"Batch    : {batch_size}")
    print(f"Extractor: {settings.extractor_model}")
    print(f"Verifier : {settings.verifier_model}")
    print("-" * 60)

    conn = create_connection(settings.database_url)
    deps = build_deps(conn, settings, project_root)
    reconnect_failures = 0

    deps.audit_logger.log_event(
        level="INFO",
        event_type="worker_started",
        message=(
            f"worker={settings.worker_id} batch={batch_size} "
            f"extractor={settings.extractor_model} verifier={settings.verifier_model}"
        ),
    )

    try:
        while True:
            try:
                jobs = deps.job_repository.claim_pending(batch_size)
                reconnect_failures = 0  # reset on success
            except psycopg.OperationalError as exc:
                reconnect_failures += 1
                if reconnect_failures > MAX_RECONNECT_ATTEMPTS:
                    print(f"[WORKER FATAL] {MAX_RECONNECT_ATTEMPTS} reconnect attempts exhausted: {exc}")
                    raise

                delay = RECONNECT_BASE_DELAY_S * reconnect_failures
                print(f"[WORKER] DB connection lost, reconnecting in {delay:.0f}s (attempt {reconnect_failures})...")
                time.sleep(delay)

                try:
                    conn.close()
                except Exception:
                    pass

                conn = create_connection(settings.database_url)
                deps = build_deps(conn, settings, project_root)
                continue

            if not jobs:
                if args.once:
                    deps.audit_logger.log_event(
                        level="INFO", event_type="worker_idle", message="no pending jobs")
                    print("[WORKER] no pending jobs")
                    return
                time.sleep(args.sleep)
                continue

            for raw_message in jobs:
                try:
                    result = process_raw_message(raw_message, deps)
                    deps.audit_logger.log_event(
                        level="INFO",
                        event_type="raw_message_completed",
                        raw_message=raw_message,
                        message=(
                            f"status={result['status']} accepted={result.get('accepted', 0)} "
                            f"rejected={result.get('rejected', 0)}"
                        ),
                        payload=result,
                    )
                    print(
                        f"[WORKER] raw={raw_message['id']} status={result['status']} "
                        f"accepted={result.get('accepted', 0)} rejected={result.get('rejected', 0)}"
                    )
                except Exception as exc:
                    deps.job_repository.mark_error(raw_message["id"], str(exc))
                    deps.audit_logger.log_event(
                        level="ERROR",
                        event_type="raw_message_error",
                        raw_message=raw_message,
                        message=str(exc),
                        payload={"error": str(exc)},
                    )
                    print(f"[WORKER ERR] raw={raw_message['id']} {exc}")

            if args.once:
                return
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
