from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import get_db_conn


router = APIRouter(prefix="/messages", tags=["messages"])


def _message_filters(q: str | None, status: str | None) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    if q:
        like = f"%{q.lower()}%"
        clauses.append(
            """
            (
              lower(coalesce(rm.sender_name, '')) LIKE %s OR
              lower(coalesce(rm.group_name, '')) LIKE %s OR
              lower(coalesce(rm.text, '')) LIKE %s
            )
            """
        )
        params.extend([like, like, like])

    if status:
        clauses.append("rm.status = %s")
        params.append(status)

    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


@router.get("")
def list_messages(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    conn=Depends(get_db_conn),
):
    where_sql, params = _message_filters(q, status)

    total = conn.execute(
        f"""
        SELECT count(*) AS total
        FROM raw_messages rm
        {where_sql}
        """,
        params,
    ).fetchone()["total"]

    items = conn.execute(
        f"""
        SELECT
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
          rm.status,
          rm.processing_attempts,
          rm.locked_by,
          rm.locked_at,
          rm.processed_at,
          rm.last_error,
          count(DISTINCT hd.id) AS accepted_count,
          count(DISTINCT rd.id) AS rejected_count,
          count(DISTINCT pe.id) AS event_count
        FROM raw_messages rm
        LEFT JOIN hotel_deals hd ON hd.raw_message_id = rm.id
        LEFT JOIN rejected_deals rd ON rd.raw_message_id = rm.id
        LEFT JOIN processing_events pe ON pe.raw_message_id = rm.id
        {where_sql}
        GROUP BY rm.id
        ORDER BY rm.captured_at DESC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/{raw_message_id}")
def get_message_detail(raw_message_id: str, conn=Depends(get_db_conn)):
    message = conn.execute(
        """
        SELECT
          rm.*,
          count(DISTINCT hd.id) AS accepted_count,
          count(DISTINCT rd.id) AS rejected_count,
          count(DISTINCT pe.id) AS event_count
        FROM raw_messages rm
        LEFT JOIN hotel_deals hd ON hd.raw_message_id = rm.id
        LEFT JOIN rejected_deals rd ON rd.raw_message_id = rm.id
        LEFT JOIN processing_events pe ON pe.raw_message_id = rm.id
        WHERE rm.id = %s
        GROUP BY rm.id
        """,
        (raw_message_id,),
    ).fetchone()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    accepted_deals = conn.execute(
        """
        SELECT
          id,
          source_msg_index,
          property_id,
          property_name,
          hotel_name,
          stars,
          location,
          location_sub,
          price_min_vnd,
          price_max_vnd,
          commission_vnd,
          match_score,
          matched,
          property_verified,
          verification_method,
          ai_verified,
          ai_verification_reason,
          extracted_payload,
          created_at
        FROM hotel_deals
        WHERE raw_message_id = %s
        ORDER BY source_msg_index NULLS FIRST, created_at
        """,
        (raw_message_id,),
    ).fetchall()

    rejected_deals = conn.execute(
        """
        SELECT
          id,
          source_msg_index,
          reason,
          text_slice,
          extracted_payload,
          candidate_property,
          verifier_payload,
          created_at
        FROM rejected_deals
        WHERE raw_message_id = %s
        ORDER BY source_msg_index NULLS FIRST, created_at
        """,
        (raw_message_id,),
    ).fetchall()

    return {
        "message": message,
        "accepted_deals": accepted_deals,
        "rejected_deals": rejected_deals,
    }


@router.get("/{raw_message_id}/events")
def list_message_events(raw_message_id: str, conn=Depends(get_db_conn)):
    exists = conn.execute("SELECT 1 AS ok FROM raw_messages WHERE id = %s", (raw_message_id,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Message not found")

    items = conn.execute(
        """
        SELECT
          id,
          raw_message_id,
          event_type,
          message,
          payload,
          created_at
        FROM processing_events
        WHERE raw_message_id = %s
        ORDER BY created_at
        """,
        (raw_message_id,),
    ).fetchall()

    return {"items": items}
