from __future__ import annotations

from psycopg.types.json import Jsonb

from app.ports.repositories import DealRepository


class PostgresDealRepository(DealRepository):
    def __init__(self, conn):
        self.conn = conn

    def save_rejected_deal(
        self,
        raw_message: dict,
        source_msg_index: int | None,
        reason: str,
        extracted_payload: dict | None = None,
        candidate_property: dict | None = None,
        verifier_payload: dict | None = None,
    ):
        with self.conn.transaction():
            self.conn.execute(
                """
                INSERT INTO rejected_deals (
                  raw_message_id,
                  source_msg_index,
                  reason,
                  text_slice,
                  extracted_payload,
                  candidate_property,
                  verifier_payload
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    raw_message["id"],
                    source_msg_index,
                    reason,
                    (raw_message.get("text") or "")[:500],
                    Jsonb(extracted_payload or {}),
                    Jsonb(candidate_property) if candidate_property else None,
                    Jsonb(verifier_payload) if verifier_payload else None,
                ),
            )

    def save_accepted_deal(self, raw_message: dict, source_msg_index: int, hotel: dict, match: dict, verification: dict):
        prop = match.get("property") if match else {}
        score = match.get("score") if match else None

        with self.conn.transaction():
            row = self.conn.execute(
                """
                INSERT INTO hotel_deals (
                  raw_message_id, source_msg_index, property_id, property_name,
                  hotel_name, stars, location, location_sub, location_raw, address,
                  checkin_dates, checkout_date, duration_nights,
                  price_min_vnd, price_max_vnd, commission_vnd, commission_pct, commission_type,
                  includes_breakfast, extra_services,
                  contact_phone, contact_name, contact_company,
                  match_score, matched, property_verified, verification_method,
                  ai_verified, ai_verification_reason, extracted_payload
                )
                VALUES (
                  %(raw_message_id)s, %(source_msg_index)s, %(property_id)s, %(property_name)s,
                  %(hotel_name)s, %(stars)s, %(location)s, %(location_sub)s, %(location_raw)s, %(address)s,
                  %(checkin_dates)s, %(checkout_date)s, %(duration_nights)s,
                  %(price_min_vnd)s, %(price_max_vnd)s, %(commission_vnd)s, %(commission_pct)s, %(commission_type)s,
                  %(includes_breakfast)s, %(extra_services)s,
                  %(contact_phone)s, %(contact_name)s, %(contact_company)s,
                  %(match_score)s, %(matched)s, %(property_verified)s, %(verification_method)s,
                  %(ai_verified)s, %(ai_verification_reason)s, %(extracted_payload)s
                )
                ON CONFLICT (raw_message_id, source_msg_index) DO UPDATE SET
                  property_id = EXCLUDED.property_id,
                  property_name = EXCLUDED.property_name,
                  hotel_name = EXCLUDED.hotel_name,
                  match_score = EXCLUDED.match_score,
                  property_verified = EXCLUDED.property_verified,
                  verification_method = EXCLUDED.verification_method,
                  ai_verified = EXCLUDED.ai_verified,
                  ai_verification_reason = EXCLUDED.ai_verification_reason,
                  extracted_payload = EXCLUDED.extracted_payload,
                  updated_at = now()
                RETURNING id
                """,
                {
                    "raw_message_id": raw_message["id"],
                    "source_msg_index": source_msg_index,
                    "property_id": prop.get("id"),
                    "property_name": prop.get("name"),
                    "hotel_name": hotel.get("hotel_name"),
                    "stars": hotel.get("stars"),
                    "location": hotel.get("location"),
                    "location_sub": hotel.get("location_sub"),
                    "location_raw": hotel.get("location_raw"),
                    "address": hotel.get("address"),
                    "checkin_dates": Jsonb(hotel.get("checkin_dates") or []),
                    "checkout_date": hotel.get("checkout_date"),
                    "duration_nights": hotel.get("duration_nights"),
                    "price_min_vnd": hotel.get("price_min_vnd"),
                    "price_max_vnd": hotel.get("price_max_vnd"),
                    "commission_vnd": hotel.get("commission_vnd"),
                    "commission_pct": hotel.get("commission_pct"),
                    "commission_type": hotel.get("commission_type"),
                    "includes_breakfast": hotel.get("includes_breakfast"),
                    "extra_services": Jsonb(hotel.get("extra_services") or []),
                    "contact_phone": hotel.get("contact_phone"),
                    "contact_name": hotel.get("contact_name"),
                    "contact_company": hotel.get("contact_company"),
                    "match_score": score,
                    "matched": bool(match),
                    "property_verified": verification.get("property_verified"),
                    "verification_method": verification.get("verification_method"),
                    "ai_verified": verification.get("ai_verified"),
                    "ai_verification_reason": verification.get("reason"),
                    "extracted_payload": Jsonb(hotel),
                },
            ).fetchone()

            deal_id = row["id"]
            self.conn.execute("DELETE FROM deal_rooms WHERE hotel_deal_id = %s", (deal_id,))
            for room in hotel.get("room_types") or []:
                self.conn.execute(
                    """
                    INSERT INTO deal_rooms (
                      hotel_deal_id, name, quantity, price_vnd, price_per, label, includes_breakfast, raw_payload
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        deal_id,
                        room.get("name"),
                        room.get("quantity"),
                        room.get("price_vnd"),
                        room.get("price_per"),
                        room.get("label"),
                        room.get("includes_breakfast"),
                        Jsonb(room),
                    ),
                )

        return deal_id
