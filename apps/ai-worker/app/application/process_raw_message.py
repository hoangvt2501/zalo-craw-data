"""Pipeline use case: process a single raw message through all stages.

Stages: Filter → Extract → Match → Verify → Persist

Each stage is a focused function. The orchestrator (`process_raw_message`)
calls them in order and makes the accept/reject decision.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from app.domain.message_filter import pre_filter, FilterResult
from app.domain.property_match_policy import MatchPolicy
from app.domain.property_matcher import PropertyMatcher
from app.ports.llm_gateway import HotelExtractorPort, PropertyVerifierPort
from app.ports.repositories import (
    DealRepository,
    PropertyRepository,
    RawMessageJobRepository,
)


@dataclass
class ProcessingDeps:
    """Typed dependency bag — replaces the untyped dict."""

    settings: Any
    job_repository: RawMessageJobRepository
    deal_repository: DealRepository
    property_repository: PropertyRepository
    extractor: HotelExtractorPort
    verifier: PropertyVerifierPort
    audit_logger: Any = None


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _classify_message(filter_reason: str, *, passed: bool, hotel_count: int | None = None) -> str:
    """Assign a human-readable category to a message based on pipeline stage."""
    if not passed:
        return {
            "tour_only": "tour_or_transport",
            "per_person_only": "tour_or_transport",
            "no_hotel_keywords": "non_hotel",
            "too_short": "too_short",
            "no_price": "hotel_without_price",
        }.get(filter_reason, "filtered_out")

    if hotel_count is None:
        return "hotel_candidate"
    return "hotel_deal" if hotel_count > 0 else "hotel_candidate_no_extract"


def _build_verifier_candidate(index: int, hotel: dict, match: dict) -> dict:
    prop = match.get("property") if match else None
    return {
        "index": index,
        "extracted_hotel": {
            "hotel_name": hotel.get("hotel_name"),
            "stars": hotel.get("stars"),
            "location": hotel.get("location"),
            "location_sub": hotel.get("location_sub"),
            "location_raw": hotel.get("location_raw"),
            "address": hotel.get("address"),
        },
        "candidate_property": {
            "id": prop.get("id"),
            "name": prop.get("name"),
            "address": prop.get("address"),
            "district": prop.get("district"),
            "province": prop.get("province"),
        } if prop else None,
        "rule_match": {
            "matched": bool(match),
            "score": match.get("score") if match else None,
        },
    }


# ---------------------------------------------------------------------------
# Stage: Filter
# ---------------------------------------------------------------------------

def _run_filter(raw_message: dict, deps: ProcessingDeps) -> dict | None:
    """Return early result dict if message should be skipped, else None."""
    filter_result = pre_filter(raw_message["text"])
    category = _classify_message(filter_result.reason, passed=filter_result.passed)

    _log(deps, "INFO", "filter_evaluated",
         f"passed={filter_result.passed} reason={filter_result.reason}",
         raw_message, {"filter_passed": filter_result.passed, "filter_reason": filter_result.reason,
                       "message_category": category, "signals": filter_result.signals})

    if filter_result.passed:
        is_dup = deps.job_repository.is_duplicate(raw_message["text"], raw_message.get("group_id"), raw_message["id"])
        if is_dup:
            filter_result = FilterResult(False, "duplicate", filter_result.signals)
            category = "duplicate"
            _log(deps, "INFO", "filter_duplicate", "message is duplicate", raw_message, {})
        else:
            return None  # continue pipeline

    _export(deps, raw_message=raw_message, stage="filter", category=category,
            filter_result=filter_result, decision="ignored",
            db_target="rejected_deals,raw_messages.ignored",
            extracted_payload={"filter_reason": filter_result.reason})

    deps.deal_repository.save_rejected_deal(raw_message, None, f"filter_{filter_result.reason}")
    deps.job_repository.mark_ignored(raw_message["id"])
    return {"status": "ignored", "reason": filter_result.reason, "accepted": 0, "rejected": 1}


# ---------------------------------------------------------------------------
# Stage: Extract
# ---------------------------------------------------------------------------

def _run_extraction(raw_message: dict, deps: ProcessingDeps) -> tuple[list[dict], FilterResult, str]:
    """Extract hotels via LLM. Returns (hotels, filter_result, category)."""
    filter_result = pre_filter(raw_message["text"])

    t0 = time.perf_counter()
    extraction = deps.extractor.extract_hotels(raw_message["text"])
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    hotels = extraction.get("hotels") if isinstance(extraction, dict) else []
    category = _classify_message(filter_result.reason, passed=True, hotel_count=len(hotels))

    _log(deps, "INFO", "extractor_completed",
         f"hotels={len(hotels)} latency_ms={elapsed_ms}",
         raw_message, {"hotel_count": len(hotels), "latency_ms": elapsed_ms,
                       "message_category": category, "extraction": extraction})

    if not hotels:
        _export(deps, raw_message=raw_message, stage="extractor", category=category,
                filter_result=filter_result, extraction_hotel_count=0,
                extracted_payload=extraction, decision="rejected",
                db_target="rejected_deals,raw_messages.rejected")

        deps.deal_repository.save_rejected_deal(raw_message, None, "extract_no_hotels", extraction)
        deps.job_repository.mark_rejected(raw_message["id"])

    return hotels, filter_result, category


# ---------------------------------------------------------------------------
# Stage: Match + Verify + Persist (per hotel)
# ---------------------------------------------------------------------------

def _process_single_hotel(
    index: int,
    hotel: dict,
    raw_message: dict,
    matcher: PropertyMatcher,
    policy: MatchPolicy,
    filter_result: FilterResult,
    category: str,
    total_hotels: int,
    deps: ProcessingDeps,
) -> bool:
    """Process one extracted hotel. Returns True if accepted, False if rejected."""
    match_info = matcher.inspect(hotel.get("hotel_name"), hotel.get("location"))
    match = match_info.get("match")

    _log(deps, "INFO", "property_match_evaluated",
         f"index={index} hotel={hotel.get('hotel_name')} matched={bool(match)} "
         f"best_score={match_info.get('best_score')}",
         raw_message, {"source_msg_index": index, "hotel_name": hotel.get("hotel_name"),
                       "match_info": match_info})

    # No match at all
    if not match:
        _export(deps, raw_message=raw_message, stage="property_match", category=category,
                filter_result=filter_result, extraction_hotel_count=total_hotels,
                hotel=hotel, source_msg_index=index, match_info=match_info,
                match_action="reject_no_match", decision="rejected", db_target="rejected_deals")
        deps.deal_repository.save_rejected_deal(raw_message, index, "rule_no_property_match", hotel)
        return False

    score = match.get("score")
    action = policy.action_for_score(score)
    if action == "accept_high_confidence" and match_info.get("location_matched") is False:
        action = "verify_with_llm"

    _log(deps, "INFO", "property_match_decided",
         f"index={index} action={action} score={score}",
         raw_message, {"source_msg_index": index, "score": score, "action": action})

    # Score too low even for LLM verification
    if action == "reject":
        _export(deps, raw_message=raw_message, stage="property_match", category=category,
                filter_result=filter_result, extraction_hotel_count=total_hotels,
                hotel=hotel, source_msg_index=index, match_info=match_info,
                match_action=action, decision="rejected", db_target="rejected_deals",
                error="rule_score_below_llm_min")
        deps.deal_repository.save_rejected_deal(
            raw_message, index, "rule_score_below_llm_min", hotel, match.get("property"))
        return False

    # Build verification result
    verification = _run_verification(
        index, hotel, match, match_info, raw_message, action, filter_result,
        category, total_hotels, deps)

    if verification is None:
        return False  # rejected by verifier or error

    # Accept the deal
    _export(deps, raw_message=raw_message, stage="decision", category=category,
            filter_result=filter_result, extraction_hotel_count=total_hotels,
            hotel=hotel, source_msg_index=index, match_info=match_info,
            match_action=action, verification=verification,
            decision="accepted", db_target="hotel_deals")

    deps.deal_repository.save_accepted_deal(raw_message, index, hotel, match, verification)
    return True


def _run_verification(
    index: int,
    hotel: dict,
    match: dict,
    match_info: dict,
    raw_message: dict,
    action: str,
    filter_result: FilterResult,
    category: str,
    total_hotels: int,
    deps: ProcessingDeps,
) -> dict | None:
    """Run verification stage. Returns verification dict or None if rejected."""
    settings = deps.settings

    if action != "verify_with_llm":
        score = match.get("score")
        return {
            "property_verified": True,
            "verification_method": "rule_high_confidence",
            "ai_verified": None,
            "reason": f"score {score} > {settings.llm_verify_max_score}",
        }

    # LLM verification needed
    try:
        t0 = time.perf_counter()
        candidate = _build_verifier_candidate(index, hotel, match)
        verification_map = deps.verifier.verify_matches(raw_message["text"], [candidate])
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        result = verification_map.get(index)

        _log(deps, "INFO", "verifier_completed",
             f"index={index} verified={bool(result and result.get('verified'))} "
             f"latency_ms={elapsed_ms}",
             raw_message, {"source_msg_index": index, "latency_ms": elapsed_ms,
                           "verifier_result": result})
    except Exception as exc:
        return _handle_verifier_error(
            exc, index, hotel, match, match_info, raw_message,
            action, filter_result, category, total_hotels, deps)

    if not settings.ai_verify_fail_open:
        if not result or result.get("verified") is not True:
            _export(deps, raw_message=raw_message, stage="verifier", category=category,
                    filter_result=filter_result, extraction_hotel_count=total_hotels,
                    hotel=hotel, source_msg_index=index, match_info=match_info,
                    match_action=action, verification=result or {},
                    decision="rejected", db_target="rejected_deals",
                    error="llm_property_match_false")
            deps.deal_repository.save_rejected_deal(
                raw_message, index, "llm_property_match_false", hotel,
                match.get("property"), result or {})
            return None

        return {
            "property_verified": True,
            "verification_method": "llm_verified",
            "ai_verified": True,
            "reason": result.get("reason"),
        }

    return {
        "property_verified": True,
        "verification_method": "llm_verified",
        "ai_verified": result.get("verified") if result else None,
        "reason": result.get("reason") if result else None,
    }


def _handle_verifier_error(
    exc: Exception,
    index: int,
    hotel: dict,
    match: dict,
    match_info: dict,
    raw_message: dict,
    action: str,
    filter_result: FilterResult,
    category: str,
    total_hotels: int,
    deps: ProcessingDeps,
) -> dict | None:
    """Handle verifier errors according to fail_open policy."""
    settings = deps.settings

    _log(deps, "ERROR", "verifier_error", f"index={index} error={exc}",
         raw_message, {"source_msg_index": index, "error": str(exc),
                       "fail_open": settings.ai_verify_fail_open})

    if settings.ai_verify_fail_open:
        return {
            "property_verified": None,
            "verification_method": "llm_verifier_error_fail_open",
            "ai_verified": None,
            "reason": f"verifier_error_fail_open: {exc}",
        }

    deps.deal_repository.save_rejected_deal(
        raw_message, index, "verifier_error", hotel,
        match.get("property"), {"error": str(exc), "fail_open": False})

    _export(deps, raw_message=raw_message, stage="verifier", category=category,
            filter_result=filter_result, extraction_hotel_count=total_hotels,
            hotel=hotel, source_msg_index=index, match_info=match_info,
            match_action=action, decision="rejected", db_target="rejected_deals",
            error=str(exc))
    return None


# ---------------------------------------------------------------------------
# Logging / audit helpers
# ---------------------------------------------------------------------------

def _log(deps: ProcessingDeps, level: str, event_type: str, message: str,
         raw_message: dict | None = None, payload: dict | None = None) -> None:
    if deps.audit_logger:
        deps.audit_logger.log_event(
            level=level, event_type=event_type, message=message,
            raw_message=raw_message, payload=payload)


def _export(deps: ProcessingDeps, *, raw_message: dict, stage: str, category: str,
            filter_result: FilterResult, decision: str, db_target: str,
            extraction_hotel_count: int | None = None, hotel: dict | None = None,
            extracted_payload: dict | None = None, source_msg_index: int | None = None,
            match_info: dict | None = None, match_action: str | None = None,
            verification: dict | None = None, error: str | None = None) -> None:
    if not deps.audit_logger:
        return
    deps.audit_logger.export_decision_row(
        raw_message=raw_message, stage=stage, message_category=category,
        filter_passed=filter_result.passed, filter_reason=filter_result.reason,
        filter_signals=filter_result.signals, extraction_hotel_count=extraction_hotel_count,
        hotel=hotel, extracted_payload=extracted_payload or hotel,
        source_msg_index=source_msg_index, match_info=match_info,
        match_action=match_action, verification=verification,
        decision=decision, db_target=db_target, error=error)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def process_raw_message(raw_message: dict, deps: ProcessingDeps) -> dict:
    """Process a single raw message through the full pipeline.

    Returns a dict with 'status', 'accepted', and 'rejected' counts.
    """
    # Stage 1: Filter
    early_result = _run_filter(raw_message, deps)
    if early_result:
        return early_result

    # Stage 2: Extract
    hotels, filter_result, category = _run_extraction(raw_message, deps)
    if not hotels:
        return {"status": "rejected", "reason": "extract_no_hotels", "accepted": 0, "rejected": 1}

    # Stage 3: Load properties + prepare matcher
    t0 = time.perf_counter()
    properties = deps.property_repository.list_properties()
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    _log(deps, "INFO", "property_pool_loaded",
         f"properties={len(properties)} latency_ms={elapsed_ms}",
         raw_message, {"property_count": len(properties), "latency_ms": elapsed_ms})

    if not properties:
        for i, hotel in enumerate(hotels):
            _export(deps, raw_message=raw_message, stage="property_lookup", category=category,
                    filter_result=filter_result, extraction_hotel_count=len(hotels),
                    hotel=hotel, source_msg_index=i, decision="rejected",
                    db_target="rejected_deals,raw_messages.rejected", error="property_db_empty")
            deps.deal_repository.save_rejected_deal(raw_message, i, "property_db_empty", hotel)
        deps.job_repository.mark_rejected(raw_message["id"])
        return {"status": "rejected", "reason": "property_db_empty", "accepted": 0, "rejected": len(hotels)}

    settings = deps.settings
    matcher = PropertyMatcher(properties, settings.match_candidate_min_score)
    policy = MatchPolicy(
        min_score=settings.match_candidate_min_score,
        verifier_min_score=settings.llm_verify_min_score,
        verifier_max_score=settings.llm_verify_max_score,
    )

    # Stage 4: Match + Verify + Persist each hotel
    accepted = 0
    rejected = 0
    for index, hotel in enumerate(hotels):
        if _process_single_hotel(index, hotel, raw_message, matcher, policy,
                                 filter_result, category, len(hotels), deps):
            accepted += 1
        else:
            rejected += 1

    # Stage 5: Final status
    if accepted > 0:
        deps.job_repository.mark_done(raw_message["id"])
        return {"status": "done", "accepted": accepted, "rejected": rejected}

    deps.job_repository.mark_rejected(raw_message["id"])
    return {"status": "rejected", "accepted": 0, "rejected": rejected}
