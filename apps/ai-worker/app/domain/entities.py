from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawMessage:
    id: str
    source: str
    text: str
    group_id: str | None
    group_name: str | None
    sender_id: str | None
    sender_name: str | None
    message_id: str | None
    sent_at: datetime | None


@dataclass(frozen=True)
class PropertyCandidate:
    property_id: str
    name: str
    province: str | None
    district: str | None
    score: float
    payload: dict[str, Any]


@dataclass(frozen=True)
class VerificationDecision:
    accepted: bool
    method: str
    reason: str | None = None
    ai_verified: bool | None = None
