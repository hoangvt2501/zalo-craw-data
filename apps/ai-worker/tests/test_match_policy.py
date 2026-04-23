"""Unit tests for app.domain.property_match_policy — score-based decision policy."""

from app.domain.property_match_policy import MatchPolicy


class TestMatchPolicy:
    def setup_method(self):
        self.policy = MatchPolicy(
            min_score=0.4,
            verifier_min_score=0.4,
            verifier_max_score=0.7,
        )

    def test_high_confidence_accepted(self):
        action = self.policy.action_for_score(0.85)
        assert action == "accept_high_confidence"

    def test_medium_confidence_verify(self):
        action = self.policy.action_for_score(0.55)
        assert action == "verify_with_llm"

    def test_low_score_rejected(self):
        action = self.policy.action_for_score(0.25)
        assert action == "reject"

    def test_exact_boundary_min(self):
        action = self.policy.action_for_score(0.4)
        assert action == "verify_with_llm"

    def test_exact_boundary_max(self):
        action = self.policy.action_for_score(0.7)
        assert action == "verify_with_llm"

    def test_above_max_boundary(self):
        action = self.policy.action_for_score(0.71)
        assert action == "accept_high_confidence"

    def test_none_score(self):
        action = self.policy.action_for_score(None)
        assert action == "reject"
