from __future__ import annotations

from psycopg.types.json import Jsonb

from app.ports.repositories import ProcessingEventRepository


class PostgresProcessingEventRepository(ProcessingEventRepository):
    def __init__(self, conn):
        self.conn = conn

    def save_event(self, raw_message_id: str, event_type: str, message: str | None = None, payload: dict | None = None):
        with self.conn.transaction():
            self.conn.execute(
                """
                INSERT INTO processing_events (raw_message_id, event_type, message, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    raw_message_id,
                    event_type[:100],
                    (message or "")[:500],
                    Jsonb(payload or {}),
                ),
            )
