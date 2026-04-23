"""Shared Vietnamese text normalization utilities.

Used by message_filter, property_matcher, and any future domain module
that needs accent-stripped, lowercased Vietnamese text.
"""

from __future__ import annotations

import re
import unicodedata


def strip_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics and normalize đ/Đ."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def normalize_text(value: str | None) -> str:
    """Normalize Vietnamese text: strip diacritics, lowercase, collapse whitespace."""
    return strip_diacritics(value or "").lower()


def normalize_for_matching(value: str | None) -> str:
    """Normalize for fuzzy matching: also replace non-alnum with spaces and collapse."""
    text = normalize_text(value)
    cleaned = (ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    return " ".join("".join(cleaned).split())


def tokenize(value: str, stop_words: set[str] | None = None) -> set[str]:
    """Split normalized text into meaningful tokens, excluding short and stop words."""
    stops = stop_words or set()
    return {token for token in value.split() if len(token) > 1 and token not in stops}


def bigrams(value: str) -> set[str]:
    """Character bigrams from whitespace-stripped text."""
    compact = value.replace(" ", "")
    return {compact[i : i + 2] for i in range(max(0, len(compact) - 1))}
