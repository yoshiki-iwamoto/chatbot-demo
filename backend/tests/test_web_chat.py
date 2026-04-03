from unittest.mock import AsyncMock, patch

import pytest


class TestWebChatEndpoint:
    @pytest.mark.asyncio
    async def test_valid_message_returns_reply(self, client):
        with patch(
            "app.routers.web_chat.generate_web_reply",
            new_callable=AsyncMock,
            return_value={
                "reply": "テスト応答",
                "reply_type": "text",
                "quick_replies": ["メニューを見る"],
            },
        ):
            response = await client.post(
                "/api/web-chat",
                json={"message": "こんにちは", "session_id": "web_abc123def456gh"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["reply"] == "テスト応答"
            assert data["reply_type"] == "text"
            assert data["quick_replies"] == ["メニューを見る"]

    @pytest.mark.asyncio
    async def test_empty_message_returns_422(self, client):
        response = await client.post(
            "/api/web-chat",
            json={"message": "", "session_id": "web_abc123def456gh"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_session_id_returns_422(self, client):
        response = await client.post(
            "/api/web-chat",
            json={"message": "hello", "session_id": "invalid_no_prefix"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_message_too_long_returns_422(self, client):
        response = await client.post(
            "/api/web-chat",
            json={"message": "あ" * 501, "session_id": "web_abc123def456gh"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self, client):
        with patch(
            "app.routers.web_chat.generate_web_reply",
            new_callable=AsyncMock,
            return_value={"reply": "ok", "reply_type": "text", "quick_replies": []},
        ):
            # Send 11 requests (limit is 10/min)
            for i in range(11):
                response = await client.post(
                    "/api/web-chat",
                    json={"message": f"msg{i}", "session_id": "web_ratelimit_test1"},
                )
                if i < 10:
                    assert response.status_code == 200
                else:
                    assert response.status_code == 429
