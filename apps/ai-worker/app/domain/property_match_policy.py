from dataclasses import dataclass


@dataclass(frozen=True)
class MatchPolicy:
    min_score: float = 0.4
    verifier_min_score: float = 0.4
    verifier_max_score: float = 0.7

    def action_for_score(self, score: float | None) -> str:
        if score is None:
            return "reject"
        if score < self.verifier_min_score:
            return "reject"
        if score > self.verifier_max_score:
            return "accept_high_confidence"
        return "verify_with_llm"

