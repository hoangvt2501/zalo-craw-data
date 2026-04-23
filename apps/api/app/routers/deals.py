from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import get_db_conn


router = APIRouter(prefix="/deals", tags=["deals"])

REJECT_BUCKET_SQL = """
CASE
  WHEN rd.reason IN (
    'filter_no_hotel_keywords', 'filter_tour_only', 'filter_per_person_only', 
    'filter_no_price', 'filter_too_short', 'extract_no_hotels',
    'no_hotel_keywords', 'tour_only', 'per_person_only', 'no_price', 'too_short'
  )
    THEN 'non_hotel'
  ELSE 'hotel_unmatched'
END
"""


def _deal_filters(q: str | None, location: str | None, sender: str | None, matched: bool | None) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    if q:
        like = f"%{q.lower()}%"
        clauses.append(
            """
            (
              lower(coalesce(hd.hotel_name, '')) LIKE %s OR
              lower(coalesce(hd.property_name, '')) LIKE %s OR
              lower(coalesce(hd.location, '')) LIKE %s OR
              lower(coalesce(rm.sender_name, '')) LIKE %s
            )
            """
        )
        params.extend([like, like, like, like])

    if location:
        params.append(location)
        clauses.append("coalesce(hd.location, '') ILIKE %s")
        params[-1] = f"%{location}%"

    if sender:
        params.append(f"%{sender.lower()}%")
        clauses.append("lower(coalesce(rm.sender_name, '')) LIKE %s")

    if matched is not None:
        clauses.append("hd.matched = %s")
        params.append(matched)

    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


@router.get("")
def list_deals(
    q: str | None = Query(default=None),
    location: str | None = Query(default=None),
    sender: str | None = Query(default=None),
    matched: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    conn=Depends(get_db_conn),
):
    where_sql, params = _deal_filters(q, location, sender, matched)

    total = conn.execute(
        f"""
        SELECT count(*) AS total
        FROM hotel_deals hd
        JOIN raw_messages rm ON rm.id = hd.raw_message_id
        {where_sql}
        """,
        params,
    ).fetchone()["total"]

    items = conn.execute(
        f"""
        SELECT
          hd.id,
          hd.raw_message_id,
          hd.source_msg_index,
          hd.property_id,
          hd.property_name,
          hd.hotel_name,
          hd.stars,
          hd.location,
          hd.location_sub,
          hd.location_raw,
          hd.address,
          hd.checkin_dates,
          hd.checkout_date,
          hd.duration_nights,
          hd.price_min_vnd,
          hd.price_max_vnd,
          hd.commission_vnd,
          hd.commission_pct,
          hd.commission_type,
          hd.includes_breakfast,
          hd.extra_services,
          hd.contact_phone,
          hd.contact_name,
          hd.contact_company,
          hd.match_score,
          hd.matched,
          hd.property_verified,
          hd.verification_method,
          hd.ai_verified,
          hd.ai_verification_reason,
          hd.extracted_payload,
          hd.created_at,
          hd.updated_at,
          rm.source,
          rm.group_name,
          rm.sender_name,
          rm.message_id,
          rm.sent_at,
          rm.captured_at,
          rm.status AS raw_message_status
        FROM hotel_deals hd
        JOIN raw_messages rm ON rm.id = hd.raw_message_id
        {where_sql}
        ORDER BY hd.created_at DESC
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


@router.get("/rejected")
def list_rejected_deals(
    q: str | None = Query(default=None),
    reason: str | None = Query(default=None),
    bucket: str | None = Query(default=None, pattern="^(non_hotel|hotel_unmatched)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    conn=Depends(get_db_conn),
):
    clauses: list[str] = []
    params: list = []

    if q:
        like = f"%{q.lower()}%"
        clauses.append(
            """
            (
              lower(coalesce(rm.sender_name, '')) LIKE %s OR
              lower(coalesce(rd.reason, '')) LIKE %s OR
              lower(coalesce(rd.text_slice, '')) LIKE %s OR
              lower(coalesce(rd.extracted_payload::text, '')) LIKE %s
            )
            """
        )
        params.extend([like, like, like, like])

    if reason:
        clauses.append("rd.reason = %s")
        params.append(reason)

    if bucket:
        clauses.append(f"{REJECT_BUCKET_SQL} = %s")
        params.append(bucket)

    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""

    total = conn.execute(
        f"""
        SELECT count(*) AS total
        FROM rejected_deals rd
        LEFT JOIN raw_messages rm ON rm.id = rd.raw_message_id
        {where_sql}
        """,
        params,
    ).fetchone()["total"]

    items = conn.execute(
        f"""
        SELECT
          rd.id,
          rd.raw_message_id,
          rd.source_msg_index,
          rd.reason,
          {REJECT_BUCKET_SQL} AS reject_bucket,
          rd.text_slice,
          rd.extracted_payload,
          rd.candidate_property,
          rd.verifier_payload,
          rd.created_at,
          rm.source,
          rm.group_name,
          rm.sender_name,
          rm.message_id,
          rm.text AS raw_text,
          rm.sent_at,
          rm.captured_at,
          rm.status AS raw_message_status
        FROM rejected_deals rd
        LEFT JOIN raw_messages rm ON rm.id = rd.raw_message_id
        {where_sql}
        ORDER BY rd.created_at DESC
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


@router.get("/{deal_id}")
def get_deal_detail(deal_id: str, conn=Depends(get_db_conn)):
    deal = conn.execute(
        """
        SELECT
          hd.*,
          rm.source,
          rm.group_name,
          rm.sender_name,
          rm.message_id,
          rm.text AS raw_text,
          rm.sent_at,
          rm.captured_at,
          rm.status AS raw_message_status
        FROM hotel_deals hd
        JOIN raw_messages rm ON rm.id = hd.raw_message_id
        WHERE hd.id = %s
        """,
        (deal_id,),
    ).fetchone()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    rooms = conn.execute(
        """
        SELECT
          id,
          name,
          quantity,
          price_vnd,
          price_per,
          label,
          includes_breakfast,
          raw_payload
        FROM deal_rooms
        WHERE hotel_deal_id = %s
        ORDER BY id
        """,
        (deal_id,),
    ).fetchall()

    return {
        "item": deal,
        "rooms": rooms,
    }
