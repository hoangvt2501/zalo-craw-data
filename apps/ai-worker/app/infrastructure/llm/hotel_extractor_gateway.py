from __future__ import annotations

from app.domain.price_parser import parse_price
from app.ports.llm_gateway import HotelExtractorPort


SYSTEM_PROMPT = """
You extract structured hotel room deals from Vietnamese Zalo travel-group messages.

Return only valid JSON:
{
  "hotels": [
    {
      "hotel_name": "name as written in the message",
      "stars": 4,
      "location": "Ha Long",
      "address": null,
      "room_types": [
        {
          "name": "Deluxe",
          "quantity": null,
          "price_vnd": 2000000,
          "price_per": "night",
          "includes_breakfast": true,
          "checkin_dates": ["30/04"]
        }
      ],
      "contact_phone": null,
      "contact_name": null
    }
  ]
}

Rules:
- Extract every hotel/resort/homestay with a concrete room price.
- IMPORTANT: If a message offers multiple dates, room types, or prices for the SAME hotel, extract ONLY ONE hotel object, and put all variations into the `room_types` array. Do NOT create multiple hotel objects for the same hotel name.
- Add `checkin_dates` specifically for each room option if stated.
- Ignore tour package prices per person unless there is a specific room price.
- Ignore transport tickets, flights, trains, team-building, and generic ads without concrete room prices.
- Convert all VND prices to integer VND. Examples: 1750k=1750000, 1.75tr=1750000, 2tr5=2500000.
- If no valid hotel deal exists, return { "hotels": [] }.
""".strip()


class HotelExtractorGateway(HotelExtractorPort):
    def __init__(self, client, model: str, temperature: float = 0):
        self.client = client
        self.model = model
        self.temperature = temperature

    def extract_hotels(self, text: str) -> dict:
        parsed = self.client.chat_json(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        return self._post_process(parsed)

    def _post_process(self, parsed: dict) -> dict:
        hotels = parsed.get("hotels") if isinstance(parsed, dict) else []
        if not isinstance(hotels, list):
            return {"hotels": []}

        clean_hotels = []
        for hotel in hotels:
            if not isinstance(hotel, dict):
                continue
            room_types = hotel.get("room_types")
            if not isinstance(room_types, list):
                room_types = []

            all_dates = set()
            normalized_rooms = []
            for room in room_types:
                if isinstance(room, dict):
                    normalized_rooms.append({**room, "price_vnd": parse_price(room.get("price_vnd"))})
                    dates = room.get("checkin_dates")
                    if isinstance(dates, list):
                        for d in dates:
                            if d and isinstance(d, str):
                                all_dates.add(d.strip())

            hotel = {
                **hotel,
                "room_types": normalized_rooms,
                "checkin_dates": list(all_dates),
                "commission_vnd": parse_price(hotel.get("commission_vnd")),
            }

            room_prices = [room["price_vnd"] for room in normalized_rooms if room.get("price_vnd")]
            if room_prices:
                hotel["price_min_vnd"] = min(room_prices)
                hotel["price_max_vnd"] = max(room_prices)
            else:
                hotel["price_min_vnd"] = None
                hotel["price_max_vnd"] = None

            try:
                stars = int(hotel["stars"]) if hotel.get("stars") is not None else None
                hotel["stars"] = stars if stars and 1 <= stars <= 5 else None
            except (TypeError, ValueError):
                hotel["stars"] = None

            clean_hotels.append(hotel)

        return {"hotels": clean_hotels}
