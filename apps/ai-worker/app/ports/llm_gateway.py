"""LLM gateway port definitions.

Port names use the suffix 'Port' to avoid collision with the concrete
infrastructure classes that share similar naming.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class HotelExtractorPort(ABC):
    """Extracts structured hotel deal data from raw message text."""

    @abstractmethod
    def extract_hotels(self, text: str) -> dict:
        ...


class PropertyVerifierPort(ABC):
    """Verifies whether extracted hotels match proposed property candidates."""

    @abstractmethod
    def verify_matches(self, raw_text: str, candidates: list[dict]) -> dict[int, dict]:
        ...
