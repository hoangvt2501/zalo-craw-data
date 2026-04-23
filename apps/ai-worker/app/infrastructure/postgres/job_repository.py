from app.ports.repositories import RawMessageJobRepository


class PostgresRawMessageJobRepository(RawMessageJobRepository):
    def __init__(self, conn, worker_id: str):
        self.conn = conn
        self.worker_id = worker_id

    def claim_pending(self, limit: int):
        with self.conn.transaction():
            return self.conn.execute(
                """
                WITH picked AS (
                  SELECT id
                  FROM raw_messages
                  WHERE status = 'pending'
                  ORDER BY captured_at
                  FOR UPDATE SKIP LOCKED
                  LIMIT %s
                )
                UPDATE raw_messages rm
                SET
                  status = 'processing',
                  processing_attempts = processing_attempts + 1,
                  locked_by = %s,
                  locked_at = now(),
                  last_error = NULL
                WHERE rm.id IN (SELECT id FROM picked)
                RETURNING
                  rm.id,
                  rm.source,
                  rm.group_id,
                  rm.group_name,
                  rm.sender_id,
                  rm.sender_name,
                  rm.message_id,
                  rm.msg_type,
                  rm.text,
                  rm.sent_at,
                  rm.captured_at,
                  rm.processing_attempts
                """,
                (limit, self.worker_id),
            ).fetchall()

    def mark_done(self, raw_message_id: str):
        self._mark(raw_message_id, "done")

    def mark_rejected(self, raw_message_id: str):
        self._mark(raw_message_id, "rejected")

    def mark_ignored(self, raw_message_id: str):
        self._mark(raw_message_id, "ignored")

    def mark_error(self, raw_message_id: str, error: str):
        with self.conn.transaction():
            self.conn.execute(
                """
                UPDATE raw_messages
                SET status = 'error', last_error = %s, processed_at = now(), locked_by = NULL, locked_at = NULL
                WHERE id = %s
                """,
                (error[:1000], raw_message_id),
            )

    def _mark(self, raw_message_id: str, status: str):
        with self.conn.transaction():
            self.conn.execute(
                """
                UPDATE raw_messages
                SET status = %s, processed_at = now(), locked_by = NULL, locked_at = NULL
                WHERE id = %s
                """,
                (status, raw_message_id),
            )

    def is_duplicate(self, text: str, group_id: str | None, exclude_id: str, within_hours: int = 1) -> bool:
        if not text:
            return False
        
        row = self.conn.execute(
            """
            SELECT 1 FROM raw_messages 
            WHERE text = %s 
              AND id != %s
              AND (group_id = %s OR (%s::text IS NULL AND group_id IS NULL))
              AND captured_at >= now() - interval '1 hour' * %s
            LIMIT 1
            """,
            (text, exclude_id, group_id, group_id, within_hours)
        ).fetchone()
        
        return bool(row)
