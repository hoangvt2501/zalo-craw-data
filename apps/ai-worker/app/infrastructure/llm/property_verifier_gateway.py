from __future__ import annotations

import json

from app.ports.llm_gateway import PropertyVerifierPort


VERIFY_SYSTEM_PROMPT = """
You are a strict hotel identity verifier for a travel deal ingestion pipeline.

Task:
Decide whether each extracted hotel mention from a Zalo message refers to the proposed property database candidate.

Return only valid JSON:
{
  "verifications": [
    { "index": 0, "verified": true, "reason": "short reason" }
  ]
}

Rules:
1. verified=true ONLY when the extracted hotel and candidate property are undeniably the exact same real-world hotel.
2. ACCEPT obvious abbreviations (e.g., "Mường Thanh" = "MT"), missing accents, and colloquial names IF the location also strictly aligns.
3. REJECT generic keyword matches (e.g., "Grand", "Boutique", "Luxury") if the distinctive proper noun is missing.
4. STRICT CHAIN RULE: For major hotel chains (Vinpearl, Mường Thanh, FLC, Novotel, etc.), REJECT if the message does not provide enough specific details (branch, tower, or exact street) to distinguish it from other branches in the SAME city.
5. LOCATION RULE: Reject if the extracted location explicitly conflicts with the candidate's province. If the message omits the location but the hotel name is highly unique, you may accept it.
6. Do not invent facts or guess. If ambiguous, return verified=false.
7. Keep one output item for every input candidate index.
""".strip()


class PropertyVerifierGateway(PropertyVerifierPort):
    def __init__(self, client, model: str, temperature: float = 0):
        self.client = client
        self.model = model
        self.temperature = temperature

    def verify_matches(self, raw_text: str, candidates: list[dict]) -> dict[int, dict]:
        if not candidates:
            return {}

        payload = {"raw_message_text": raw_text, "candidates": candidates}
        parsed = self.client.chat_json(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )

        items = parsed if isinstance(parsed, list) else parsed.get("verifications", [])
        result = {}
        for item in items:
            try:
                index = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            result[index] = {
                "index": index,
                "verified": item.get("verified") is True,
                "reason": str(item.get("reason") or "")[:300],
            }
        return result
