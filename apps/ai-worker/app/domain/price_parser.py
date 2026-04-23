from __future__ import annotations

import re


PRICE_RE = re.compile(r"^[\s\"']*([\d.,]+)\s*(k|tr|trieu|m|d|vnd)?[\s\"']*$", re.I)


def parse_price(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(value) if value > 0 else None
    if not isinstance(value, str):
        return None

    match = PRICE_RE.match(value.strip())
    if not match:
        return None

    num_str = match.group(1)
    unit = (match.group(2) or "").lower()
    dot_count = num_str.count(".")
    comma_count = num_str.count(",")

    try:
        if dot_count > 1:
            number = float(num_str.replace(".", ""))
        elif comma_count > 1:
            number = float(num_str.replace(",", ""))
        elif dot_count == 1:
            right = num_str.split(".")[1]
            number = float(num_str.replace(".", "")) if len(right) >= 3 else float(num_str)
        elif comma_count == 1:
            right = num_str.split(",")[1]
            number = float(num_str.replace(",", "")) if len(right) >= 3 else float(num_str.replace(",", "."))
        else:
            number = float(num_str)
    except ValueError:
        return None

    if number <= 0:
        return None
    if unit == "k":
        number *= 1000
    if unit in {"tr", "trieu", "m"}:
        number *= 1_000_000

    return round(number)
