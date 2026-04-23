"""Property matching engine.

Matches extracted hotel names against the canonical property database
using token overlap, bigram Dice coefficient, and containment scoring.
"""

from __future__ import annotations

from app.domain.text_utils import bigrams, normalize_for_matching, tokenize
from app.domain.location_aliases import resolve_location


STOP_WORDS: set[str] = {
    "hotel", "resort", "khach", "san", "spa", "villa", "villas", "beach",
    "bay", "luxury", "boutique", "grand", "premium", "the", "and", "de",
    "du", "la", "le", "an", "inn", "lodge", "retreat", "eco", "club",
    "international", "collection", "suites", "suite", "rooms",
}


def token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def bigram_dice(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return (2 * len(left & right)) / (len(left) + len(right))


class PropertyMatcher:
    """Fuzzy matcher for hotel names against the property catalog."""

    def __init__(self, properties: list[dict], threshold: float = 0.4):
        self.threshold = threshold
        self.properties = [self._prepare(prop) for prop in properties if prop.get("name")]

    def match(self, hotel_name: str | None, province: str | None = None) -> dict | None:
        return self.inspect(hotel_name, province).get("match")

    def inspect(self, hotel_name: str | None, province: str | None = None) -> dict:
        if not hotel_name or not self.properties:
            return {
                "match": None,
                "best_property": None,
                "best_score": None,
                "location_matched": None,
                "province_filtered": False,
                "candidate_pool_size": 0,
                "query_norm": normalize_for_matching(hotel_name),
                "province_norm": normalize_for_matching(province),
                "threshold": self.threshold,
            }

        query_norm = normalize_for_matching(hotel_name)
        query_tokens = tokenize(query_norm, STOP_WORDS)
        query_bigrams = bigrams(query_norm)
        province_norm = normalize_for_matching(province)

        pool = self.properties
        province_filtered = False
        location_matched = None
        if province_norm:
            filtered = [prop for prop in self.properties if self._location_match(province_norm, prop)]
            if filtered:
                pool = filtered
                province_filtered = True
                location_matched = True

        best_prop = None
        best_score = -1.0
        for prop in pool:
            score = self._score(query_norm, query_tokens, query_bigrams, prop)
            if score > best_score:
                best_score = score
                best_prop = prop

        clean = {k: v for k, v in best_prop.items() if not k.startswith("_")} if best_prop else None
        matched = clean is not None and best_score >= self.threshold
        if province_norm and best_prop and location_matched is None:
            location_matched = self._location_match(province_norm, best_prop)
        return {
            "match": {"property": clean, "score": round(best_score, 2)} if matched else None,
            "best_property": clean,
            "best_score": round(best_score, 2) if clean is not None else None,
            "location_matched": location_matched,
            "province_filtered": province_filtered,
            "candidate_pool_size": len(pool),
            "query_norm": query_norm,
            "province_norm": province_norm,
            "threshold": self.threshold,
        }

    # -- Private helpers --------------------------------------------------

    def _prepare(self, prop: dict) -> dict:
        name_norm = normalize_for_matching(prop.get("name"))
        combined_norm = normalize_for_matching(
            f"{prop.get('name') or ''} {prop.get('district') or ''} {prop.get('province') or ''}"
        )
        return {
            **prop,
            "_name_norm": name_norm,
            "_province_norm": normalize_for_matching(prop.get("province")),
            "_location_text": normalize_for_matching(
                f"{prop.get('address') or ''} {prop.get('district') or ''} {prop.get('province') or ''}"
            ),
            "_tokens": tokenize(combined_norm, STOP_WORDS),
            "_bigrams": bigrams(name_norm),
        }

    def _location_match(self, location_norm: str, prop: dict) -> bool:
        if not location_norm:
            return False
        location_text = prop.get("_location_text") or ""
        compact_text = location_text.replace(" ", "")
        
        query_variants = resolve_location(location_norm)
        for variant in query_variants:
            if variant in location_text or variant.replace(" ", "") in compact_text:
                return True
        return False

    def _containment_score(self, query_norm: str, prop: dict) -> float:
        if query_norm and query_norm in prop["_name_norm"]:
            return 1.0
        query_tokens = tokenize(query_norm, STOP_WORDS)
        if not query_tokens:
            return 0.0
        hits = sum(1 for t in query_tokens if t in prop["_tokens"])
        return hits / len(query_tokens)

    def _score(self, query_norm: str, query_tokens: set[str], query_bigrams: set[str], prop: dict) -> float:
        contain = self._containment_score(query_norm, prop)
        tok = token_overlap(query_tokens, prop["_tokens"])
        bg = bigram_dice(query_bigrams, prop["_bigrams"])
        query_len = len(query_norm.replace(" ", ""))
        if query_len <= 6 and contain > 0:
            return 0.15 * tok + 0.10 * bg + 0.75 * contain
        return 0.35 * tok + 0.40 * bg + 0.25 * contain
