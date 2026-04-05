from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_generate_answer_with_history():
    service = RAGService()

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(content="テスト回答")]
    mock_completion.choices[0].message.content = "テスト回答"

    with (
        patch.object(service._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_completion),
        patch("app.services.rag_service.chroma_service") as mock_chroma,
    ):
        mock_chroma.query.return_value = [{"document": "Q: 営業時間\nA: 10時〜20時"}]

        result = await service.generate_answer(
            "何時まで？",
            history=[
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "いらっしゃいませ！"},
            ],
        )
        assert result == "テスト回答"

        # Verify history was included in the messages
        call_args = service._client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 4  # system + 2 history + 1 user
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "こんにちは"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "いらっしゃいませ！"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "何時まで？"


@pytest.mark.asyncio
async def test_generate_answer_without_history_backward_compatible():
    service = RAGService()

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(content="テスト回答")]
    mock_completion.choices[0].message.content = "テスト回答"

    with (
        patch.object(service._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_completion),
        patch("app.services.rag_service.chroma_service") as mock_chroma,
    ):
        mock_chroma.query.return_value = [{"document": "Q: test\nA: test"}]

        result = await service.generate_answer("テスト")
        assert result == "テスト回答"

        call_args = service._client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2  # system + user only
