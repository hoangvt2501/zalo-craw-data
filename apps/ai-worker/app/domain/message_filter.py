from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.text_utils import normalize_text


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    reason: str
    signals: dict[str, bool]


RE_PRICE_ANY = re.compile(r"\d[\d.,]*\s*(?:k|tr|trieu|d|vnd)", re.I)
RE_PRICE_PER_PERSON = re.compile(r"\d[\d.,]*\s*(?:k|tr|trieu)\s*[/／]\s*(?:nguoi|ng\b|pax|person|khach\b)", re.I)
RE_ROOM_TYPE = re.compile(
    r"\b(?:deluxe|superior|standard|twin|double|single|triple|suite|villa|"
    r"bungalow|roh|family|connecting|studio|ocean\s*view|sea\s*view|"
    r"garden\s*view|pool\s*view|king|queen|premier|classic|executive|"
    r"junior|phong\s+\w+)\b",
    re.I,
)
RE_HOTEL_KW = re.compile(
    r"\b(?:khach\s*san|resort|hotel|homestay|lodge|inn|ks\b|villa\b|residence|apartment|condotel|bungalow|retreat|boutique)\b",
    re.I,
)
RE_STARS = re.compile(r"[★*]\s*\d|\d\s*(?:★|\*|sao)", re.I)
RE_TOUR_ONLY = re.compile(
    r"\b(?:tour\s+tron\s+goi|ve\s+may\s+bay|ve\s+tau|ve\s+xe\s+lua|team.?building|combo\s+tour|du\s+lich|lich\s+trinh|khoi\s+hanh|gia\s+ve)\b",
    re.I,
)
RE_PRICE_PER_NIGHT = re.compile(r"\d[\d.,]*\s*(?:k|tr|trieu)\s*[/／]?\s*(?:dem|night|room|phong)\b", re.I)


def pre_filter(text: str) -> FilterResult:
    if not text or len(text) < 25:
        return FilterResult(
            False,
            "too_short",
            {
                "has_price": False,
                "has_room_type": False,
                "has_hotel_kw": False,
                "has_stars": False,
                "is_per_person": False,
                "has_tour_kw": False,
                "has_night_price": False,
            },
        )

    normalized = normalize_text(text)
    has_price = bool(RE_PRICE_ANY.search(normalized))
    has_room_type = bool(RE_ROOM_TYPE.search(normalized))
    has_hotel_kw = bool(RE_HOTEL_KW.search(normalized))
    has_stars = bool(RE_STARS.search(normalized))
    is_per_person = bool(RE_PRICE_PER_PERSON.search(normalized))
    has_tour_kw = bool(RE_TOUR_ONLY.search(normalized))
    has_night_price = bool(RE_PRICE_PER_NIGHT.search(normalized))
    signals = {
        "has_price": has_price,
        "has_room_type": has_room_type,
        "has_hotel_kw": has_hotel_kw,
        "has_stars": has_stars,
        "is_per_person": is_per_person,
        "has_tour_kw": has_tour_kw,
        "has_night_price": has_night_price,
    }

    if not has_price:
        return FilterResult(False, "no_price", signals)
    if not has_hotel_kw and not has_room_type and not has_stars:
        return FilterResult(False, "no_hotel_keywords", signals)
    if has_tour_kw and not has_room_type:
        return FilterResult(False, "tour_only", signals)
    if is_per_person and not has_room_type and not has_night_price:
        return FilterResult(False, "per_person_only", signals)

    return FilterResult(True, "ok", signals)
