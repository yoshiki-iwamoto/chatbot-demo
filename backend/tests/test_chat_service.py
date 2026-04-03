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


from unittest.mock import AsyncMock, patch

from app.services.chat_service import generate_web_reply


class TestGenerateWebReply:
    @pytest.mark.asyncio
    async def test_keyword_match_returns_web_response(self, db_session):
        result = await generate_web_reply("予約したい", "web_test123", db_session)
        assert "https://example.com/reserve" in result["reply"]
        assert result["reply_type"] == "text"
        assert isinstance(result["quick_replies"], list)

    @pytest.mark.asyncio
    async def test_no_keyword_calls_rag(self, db_session):
        with patch(
            "app.services.chat_service.rag_service.generate_answer",
            new_callable=AsyncMock,
            return_value="AIの応答です",
        ):
            result = await generate_web_reply("こんにちは", "web_test123", db_session)
            assert result["reply"] == "AIの応答です"
            assert result["reply_type"] == "text"

    @pytest.mark.asyncio
    async def test_saves_messages_to_db(self, db_session):
        with patch(
            "app.services.chat_service.rag_service.generate_answer",
            new_callable=AsyncMock,
            return_value="テスト応答",
        ):
            await generate_web_reply("テスト", "web_save_test", db_session)

        from sqlalchemy import select
        from app.models.chat_history import ChatHistory

        result = await db_session.execute(
            select(ChatHistory).where(ChatHistory.user_id == "web_save_test")
        )
        records = list(result.scalars().all())
        assert len(records) == 2
        assert records[0].message_type == "user"
        assert records[0].content == "テスト"
        assert records[1].message_type == "bot"
        assert records[1].content == "テスト応答"

    @pytest.mark.asyncio
    async def test_passes_history_to_rag(self, db_session):
        """After multiple exchanges, history should be passed to RAG."""
        with patch(
            "app.services.chat_service.rag_service.generate_answer",
            new_callable=AsyncMock,
            return_value="2回目の応答",
        ) as mock_rag:
            # First message
            await generate_web_reply("最初のメッセージ", "web_hist_test", db_session)
            # Second message — should include first exchange in history
            await generate_web_reply("2回目のメッセージ", "web_hist_test", db_session)

            # Check the second call included history
            second_call = mock_rag.call_args_list[1]
            history = second_call.kwargs.get("history") or second_call.args[1] if len(second_call.args) > 1 else second_call.kwargs.get("history")
            assert history is not None
            assert len(history) >= 2  # at least 1 user + 1 assistant from first exchange
