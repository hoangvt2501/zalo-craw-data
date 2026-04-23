"""Repository port definitions for the AI worker.

All repository contracts use abc.ABC to enforce that concrete
implementations in infrastructure/ actually implement every method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RawMessageJobRepository(ABC):
    """Manages the raw_messages job queue lifecycle."""

    @abstractmethod
    def claim_pending(self, limit: int) -> list[dict]:
        ...

    @abstractmethod
    def mark_done(self, raw_message_id: str) -> None:
        ...

    @abstractmethod
    def mark_rejected(self, raw_message_id: str) -> None:
        ...

    @abstractmethod
    def mark_ignored(self, raw_message_id: str) -> None:
        ...

    @abstractmethod
    def mark_error(self, raw_message_id: str, error: str) -> None:
        ...

    @abstractmethod
    def is_duplicate(self, text: str, group_id: str | None, exclude_id: str, within_hours: int = 1) -> bool:
        ...


class DealRepository(ABC):
    """Persists accepted and rejected hotel deals."""

    @abstractmethod
    def save_accepted_deal(
        self,
        raw_message: dict,
        source_msg_index: int,
        hotel: dict,
        match: dict,
        verification: dict,
    ) -> Any:
        ...

    @abstractmethod
    def save_rejected_deal(
        self,
        raw_message: dict,
        source_msg_index: int | None,
        reason: str,
        extracted_payload: dict | None = None,
        candidate_property: dict | None = None,
        verifier_payload: dict | None = None,
    ) -> None:
        ...


class PropertyRepository(ABC):
    """Read-only access to the canonical property catalog."""

    @abstractmethod
    def list_properties(self) -> list[dict]:
        ...


class ProcessingEventRepository(ABC):
    """Persists processing pipeline events for observability."""

    @abstractmethod
    def save_event(
        self,
        raw_message_id: str,
        event_type: str,
        message: str | None = None,
        payload: dict | None = None,
    ) -> None:
        ...
