"""Unit tests for app.domain.text_utils — Vietnamese text normalization."""

from app.domain.text_utils import (
    bigrams,
    normalize_for_matching,
    normalize_text,
    strip_diacritics,
    tokenize,
)


class TestStripDiacritics:
    def test_basic_vietnamese(self):
        assert strip_diacritics("Hà Nội") == "Ha Noi"

    def test_d_bar(self):
        assert strip_diacritics("đường Đồng") == "duong Dong"

    def test_ascii_passthrough(self):
        assert strip_diacritics("hello world") == "hello world"


class TestNormalizeText:
    def test_lowercases_and_strips_diacritics(self):
        assert normalize_text("HÀ NỘI") == "ha noi"

    def test_none_returns_empty(self):
        assert normalize_text(None) == ""

    def test_empty_string(self):
        assert normalize_text("") == ""


class TestNormalizeForMatching:
    def test_removes_special_chars(self):
        result = normalize_for_matching("D'Lioro Hotel & Resort")
        assert result == "d lioro hotel resort"

    def test_collapses_whitespace(self):
        result = normalize_for_matching("  Muong   Thanh   ")
        assert result == "muong thanh"


class TestTokenize:
    def test_splits_tokens(self):
        tokens = tokenize("muong thanh ha long", stop_words=set())
        assert tokens == {"muong", "thanh", "ha", "long"}

    def test_excludes_short(self):
        tokens = tokenize("a bb ccc", stop_words=set())
        assert "a" not in tokens
        assert "bb" in tokens

    def test_excludes_stop_words(self):
        tokens = tokenize("muong thanh hotel spa", stop_words={"hotel", "spa"})
        assert tokens == {"muong", "thanh"}


class TestBigrams:
    def test_basic(self):
        result = bigrams("ab cd")
        # compact = "abcd", bigrams = {ab, bc, cd}
        assert result == {"ab", "bc", "cd"}

    def test_single_char(self):
        assert bigrams("a") == set()

    def test_empty(self):
        assert bigrams("") == set()
