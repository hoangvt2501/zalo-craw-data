from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db import get_db_conn


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def get_metrics_summary(conn=Depends(get_db_conn)):
    summary = conn.execute(
        """
        SELECT
          (SELECT count(*) FROM hotel_deals) AS hotel_deals,
          (SELECT count(*) FROM rejected_deals) AS rejected_deals,
          (SELECT count(*) FROM processing_events) AS processing_events,
          (SELECT count(*) FROM raw_messages) AS raw_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'pending') AS pending_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'processing') AS processing_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'done') AS done_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'ignored') AS ignored_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'rejected') AS rejected_messages,
          (SELECT count(*) FROM raw_messages WHERE status = 'error') AS error_messages,
          (SELECT max(captured_at) FROM raw_messages) AS latest_capture_at,
          (SELECT max(processed_at) FROM raw_messages) AS latest_processed_at,
          (SELECT max(created_at) FROM hotel_deals) AS latest_deal_at
        """
    ).fetchone()

    top_locations = conn.execute(
        """
        SELECT
          location,
          count(*) AS deals,
          min(price_min_vnd) AS best_price_vnd,
          max(price_max_vnd) AS worst_price_vnd
        FROM hotel_deals
        WHERE location IS NOT NULL AND location <> ''
        GROUP BY location
        ORDER BY deals DESC, location
        LIMIT 8
        """
    ).fetchall()

    top_senders = conn.execute(
        """
        SELECT
          sender_name,
          count(*) AS messages,
          max(captured_at) AS latest_seen_at
        FROM raw_messages
        WHERE sender_name IS NOT NULL AND sender_name <> ''
        GROUP BY sender_name
        ORDER BY messages DESC, sender_name
        LIMIT 8
        """
    ).fetchall()

    return {
        "summary": summary,
        "top_locations": top_locations,
        "top_senders": top_senders,
    }
