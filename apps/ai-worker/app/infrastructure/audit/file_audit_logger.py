from __future__ import annotations

import csv
import json
from codecs import BOM_UTF8
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


CSV_COLUMNS = [
    "logged_at",
    "worker_id",
    "stage",
    "raw_message_id",
    "source",
    "group_name",
    "sender_name",
    "message_id",
    "msg_type",
    "message_category",
    "filter_passed",
    "filter_reason",
    "filter_has_price",
    "filter_has_room_type",
    "filter_has_hotel_kw",
    "filter_has_stars",
    "filter_is_per_person",
    "filter_has_tour_kw",
    "filter_has_night_price",
    "source_msg_index",
    "extraction_hotel_count",
    "hotel_name",
    "hotel_stars",
    "extracted_location",
    "extracted_location_sub",
    "extracted_location_raw",
    "extracted_address",
    "checkin_dates",
    "price_min_vnd",
    "price_max_vnd",
    "contact_phone",
    "contact_name",
    "match_found",
    "match_score",
    "match_action",
    "location_matched",
    "province_filter_used",
    "candidate_pool_size",
    "best_candidate_score",
    "location_query_norm",
    "location_province_norm",
    "matched_property_id",
    "matched_property_name",
    "matched_property_district",
    "matched_property_province",
    "verification_method",
    "ai_verified",
    "ai_verification_reason",
    "decision",
    "db_target",
    "error",
    "text_preview",
    "extracted_payload_json",
    "best_candidate_json",
]


class FileAuditLogger:
    def __init__(self, worker_id: str, project_root: Path, event_repository=None):
        self.worker_id = worker_id
        self.project_root = Path(project_root)
        self.event_repository = event_repository
        self.log_dir = self.project_root / "var" / "logs"
        self.export_dir = self.project_root / "var" / "exports"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.human_log_path = self.log_dir / "ai-worker-audit.log"
        self.jsonl_log_path = self.log_dir / "ai-worker-events.jsonl"
        self.csv_path = self.export_dir / "ai-worker-decisions.csv"
        self._lock = Lock()

    def log_event(
        self,
        *,
        level: str,
        event_type: str,
        message: str,
        raw_message: dict | None = None,
        payload: dict | None = None,
    ) -> None:
        event = {
            "logged_at": self._now_iso(),
            "worker_id": self.worker_id,
            "level": level.upper(),
            "event_type": event_type,
            "raw_message_id": raw_message.get("id") if raw_message else None,
            "sender_name": raw_message.get("sender_name") if raw_message else None,
            "group_name": raw_message.get("group_name") if raw_message else None,
            "message": message,
            "payload": payload or {},
        }

        human_line = self._format_human_line(event)
        jsonl_line = json.dumps(event, ensure_ascii=False, default=str)

        with self._lock:
            with self.human_log_path.open("a", encoding="utf-8") as file:
                file.write(human_line + "\n")
            with self.jsonl_log_path.open("a", encoding="utf-8") as file:
                file.write(jsonl_line + "\n")

        if raw_message and self.event_repository:
            try:
                self.event_repository.save_event(
                    raw_message["id"],
                    event_type,
                    message,
                    payload or {},
                )
            except Exception as exc:
                fallback = (
                    f"{self._now_iso()} [WARN] processing_event_write_failed "
                    f"raw={raw_message.get('id')} error={exc}"
                )
                with self._lock:
                    with self.human_log_path.open("a", encoding="utf-8") as file:
                        file.write(fallback + "\n")

    def export_decision_row(
        self,
        *,
        raw_message: dict,
        stage: str,
        message_category: str,
        filter_passed: bool,
        filter_reason: str,
        filter_signals: dict | None = None,
        extraction_hotel_count: int | None = None,
        hotel: dict | None = None,
        extracted_payload: dict | None = None,
        source_msg_index: int | None = None,
        match_info: dict | None = None,
        match_action: str | None = None,
        verification: dict | None = None,
        decision: str,
        db_target: str,
        error: str | None = None,
    ) -> None:
        best_candidate = (match_info or {}).get("best_property") or {}
        match = (match_info or {}).get("match") or {}
        row = {
            "logged_at": self._now_iso(),
            "worker_id": self.worker_id,
            "stage": stage,
            "raw_message_id": raw_message.get("id"),
            "source": raw_message.get("source"),
            "group_name": raw_message.get("group_name"),
            "sender_name": raw_message.get("sender_name"),
            "message_id": raw_message.get("message_id"),
            "msg_type": raw_message.get("msg_type"),
            "message_category": message_category,
            "filter_passed": filter_passed,
            "filter_reason": filter_reason,
            "filter_has_price": (filter_signals or {}).get("has_price"),
            "filter_has_room_type": (filter_signals or {}).get("has_room_type"),
            "filter_has_hotel_kw": (filter_signals or {}).get("has_hotel_kw"),
            "filter_has_stars": (filter_signals or {}).get("has_stars"),
            "filter_is_per_person": (filter_signals or {}).get("is_per_person"),
            "filter_has_tour_kw": (filter_signals or {}).get("has_tour_kw"),
            "filter_has_night_price": (filter_signals or {}).get("has_night_price"),
            "source_msg_index": source_msg_index,
            "extraction_hotel_count": extraction_hotel_count,
            "hotel_name": (hotel or {}).get("hotel_name"),
            "hotel_stars": (hotel or {}).get("stars"),
            "extracted_location": (hotel or {}).get("location"),
            "extracted_location_sub": (hotel or {}).get("location_sub"),
            "extracted_location_raw": (hotel or {}).get("location_raw"),
            "extracted_address": (hotel or {}).get("address"),
            "checkin_dates": self._json((hotel or {}).get("checkin_dates") or []),
            "price_min_vnd": (hotel or {}).get("price_min_vnd"),
            "price_max_vnd": (hotel or {}).get("price_max_vnd"),
            "contact_phone": (hotel or {}).get("contact_phone"),
            "contact_name": (hotel or {}).get("contact_name"),
            "match_found": bool(match),
            "match_score": match.get("score"),
            "match_action": match_action,
            "location_matched": (match_info or {}).get("location_matched"),
            "province_filter_used": (match_info or {}).get("province_filtered"),
            "candidate_pool_size": (match_info or {}).get("candidate_pool_size"),
            "best_candidate_score": (match_info or {}).get("best_score"),
            "location_query_norm": (match_info or {}).get("query_norm"),
            "location_province_norm": (match_info or {}).get("province_norm"),
            "matched_property_id": best_candidate.get("id"),
            "matched_property_name": best_candidate.get("name"),
            "matched_property_district": best_candidate.get("district"),
            "matched_property_province": best_candidate.get("province"),
            "verification_method": (verification or {}).get("verification_method"),
            "ai_verified": (verification or {}).get("ai_verified"),
            "ai_verification_reason": (verification or {}).get("reason"),
            "decision": decision,
            "db_target": db_target,
            "error": error or "",
            "text_preview": self._preview(raw_message.get("text")),
            "extracted_payload_json": self._json(extracted_payload if extracted_payload is not None else (hotel or {})),
            "best_candidate_json": self._json(best_candidate),
        }

        with self._lock:
            self._ensure_excel_utf8_bom()
            write_header = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
            with self.csv_path.open("a", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)

    def _format_human_line(self, event: dict) -> str:
        parts = [
            event["logged_at"],
            f"[{event['level']}]",
            event["event_type"],
        ]
        if event.get("raw_message_id"):
            parts.append(f"raw={event['raw_message_id']}")
        if event.get("sender_name"):
            parts.append(f"sender={event['sender_name']}")
        parts.append(event["message"])
        return " ".join(str(part) for part in parts if part not in {None, ""})

    def _json(self, value) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    def _preview(self, text: str | None, limit: int = 160) -> str:
        clean = " ".join(str(text or "").split())
        return clean[:limit]

    def _ensure_excel_utf8_bom(self) -> None:
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            return
        with self.csv_path.open("rb") as file:
            prefix = file.read(3)
        if prefix == BOM_UTF8:
            return
        content = self.csv_path.read_text(encoding="utf-8")
        self.csv_path.write_text(content, encoding="utf-8-sig")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
