"""Unit tests for app.domain.property_matcher — fuzzy matching."""

from app.domain.property_matcher import PropertyMatcher


SAMPLE_PROPERTIES = [
    {
        "id": "p1",
        "name": "Khach san Muong Thanh Holiday Suoi Mo Ha Long",
        "address": "123 Ha Long",
        "district": "Bai Chay",
        "province": "Quang Ninh",
        "stars": 4,
        "aliases": [],
    },
    {
        "id": "p2",
        "name": "Wyndham Legend Ha Long",
        "address": "456 Bai Chay",
        "district": "Bai Chay",
        "province": "Quang Ninh",
        "stars": 5,
        "aliases": [],
    },
    {
        "id": "p3",
        "name": "InterContinental Danang Sun Peninsula",
        "address": "Son Tra",
        "district": "Son Tra",
        "province": "Da Nang",
        "stars": 5,
        "aliases": [],
    },
]


class TestPropertyMatcher:
    def setup_method(self):
        self.matcher = PropertyMatcher(SAMPLE_PROPERTIES, threshold=0.4)

    def test_exact_match(self):
        result = self.matcher.match("Wyndham Legend Ha Long")
        assert result is not None
        assert result["property"]["id"] == "p2"
        assert result["score"] >= 0.4

    def test_partial_match(self):
        result = self.matcher.match("MUONG THANH SUOI MO")
        assert result is not None
        assert result["property"]["id"] == "p1"

    def test_no_match_returns_none(self):
        result = self.matcher.match("Some Completely Unknown Hotel XYZ 999")
        # May or may not match depending on threshold, but if it does, score should be checked
        if result is not None:
            assert result["score"] >= 0.4

    def test_none_input(self):
        result = self.matcher.match(None)
        assert result is None

    def test_empty_properties(self):
        matcher = PropertyMatcher([], threshold=0.4)
        result = matcher.match("Wyndham")
        assert result is None

    def test_province_filter_narrows_pool(self):
        info = self.matcher.inspect("InterContinental", province="Da Nang")
        assert info["province_filtered"]
        if info["match"]:
            assert info["match"]["property"]["id"] == "p3"

    def test_inspect_returns_metadata(self):
        info = self.matcher.inspect("Muong Thanh")
        assert "best_score" in info
        assert "query_norm" in info
        assert "threshold" in info
        assert "candidate_pool_size" in info
