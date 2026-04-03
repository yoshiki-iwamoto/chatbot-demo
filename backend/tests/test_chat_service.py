import pytest

from app.services.chat_service import match_keyword, get_web_keyword_response


class TestMatchKeyword:
    def test_booking_keyword(self):
        assert match_keyword("予約したいのですが") == "booking"

    def test_menu_keyword(self):
        assert match_keyword("メニューを見たい") == "menu"

    def test_access_keyword(self):
        assert match_keyword("場所を教えてください") == "access"

    def test_no_match(self):
        assert match_keyword("こんにちは") is None

    def test_booking_variation(self):
        assert match_keyword("予約する方法は？") == "booking"

    def test_menu_price_variation(self):
        assert match_keyword("料金はいくらですか") == "menu"

    def test_access_direction_variation(self):
        assert match_keyword("行き方を教えて") == "access"


class TestGetWebKeywordResponse:
    def test_booking_response_has_required_fields(self):
        result = get_web_keyword_response("booking")
        assert "reply" in result
        assert "reply_type" in result
        assert "quick_replies" in result
        assert result["reply_type"] == "text"

    def test_booking_response_contains_reserve_url(self):
        result = get_web_keyword_response("booking")
        assert "https://example.com/reserve" in result["reply"]
        assert "03-6789-0123" in result["reply"]

    def test_menu_response_contains_prices(self):
        result = get_web_keyword_response("menu")
        assert "カット" in result["reply"]
        assert "カラー" in result["reply"]

    def test_access_response_contains_address(self):
        result = get_web_keyword_response("access")
        assert "渋谷区神宮前" in result["reply"]
        assert "maps.google.com" in result["reply"]

    def test_unknown_keyword_returns_none(self):
        result = get_web_keyword_response("unknown")
        assert result is None
