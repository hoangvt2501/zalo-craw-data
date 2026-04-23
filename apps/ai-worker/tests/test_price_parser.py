"""Unit tests for app.domain.price_parser — Vietnamese price parsing."""

from app.domain.price_parser import parse_price


class TestParsePrice:
    def test_vnd_suffix(self):
        result = parse_price("2.400.000 VND")
        assert result == 2_400_000

    def test_k_suffix(self):
        result = parse_price("2400k")
        assert result == 2_400_000

    def test_tr_suffix(self):
        result = parse_price("2.4tr")
        assert result == 2_400_000

    def test_trieu_suffix(self):
        result = parse_price("2.4 trieu")
        assert result == 2_400_000

    def test_none_input(self):
        result = parse_price(None)
        assert result is None

    def test_empty_string(self):
        result = parse_price("")
        assert result is None

    def test_no_match(self):
        result = parse_price("hello world")
        assert result is None

    def test_integer(self):
        result = parse_price(2400000)
        assert result == 2_400_000

    def test_float_passthrough(self):
        result = parse_price(2_400_000.0)
        assert result == 2_400_000
