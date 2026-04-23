"""Unit tests for app.domain.message_filter — pre_filter heuristics."""

from app.domain.message_filter import pre_filter


class TestPreFilter:
    def test_too_short_rejected(self):
        result = pre_filter("hi")
        assert not result.passed
        assert result.reason == "too_short"

    def test_hotel_with_price_passes(self):
        text = "Mường Thanh Hạ Long - 2.400.000 VND/đêm, Standard room"
        result = pre_filter(text)
        assert result.passed

    def test_tour_only_rejected(self):
        text = "Tour Hạ Long 3 ngày 2 đêm 4.500.000 VND"
        result = pre_filter(text)
        # Should either be rejected for tour_only or per_person_only
        assert not result.passed or result.reason in ("tour_only", "per_person_only")

    def test_no_price_rejected(self):
        text = "Khách sạn Mường Thanh Luxury Hạ Long view đẹp, phòng rộng, tiện nghi đầy đủ"
        result = pre_filter(text)
        assert not result.passed
        assert result.reason == "no_price"

    def test_signals_populated(self):
        text = "Khách sạn Mường Thanh Luxury 2.400k/đêm"
        result = pre_filter(text)
        assert isinstance(result.signals, dict)
        assert "has_hotel_kw" in result.signals
        assert "has_price" in result.signals

    def test_sticker_like_message(self):
        result = pre_filter("")
        assert not result.passed
