# Web Chat Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-based web chat demo page and landing page to the Hair Salon BLOOM LINE chatbot, so potential clients can experience the AI chatbot instantly via URL.

**Architecture:** A new `POST /api/web-chat` FastAPI endpoint shares keyword-matching and RAG logic (extracted into `chat_service.py`) with the existing LINE webhook. A standalone static site (`demo-site/`) provides a LINE-style chat UI and a marketing landing page, communicating with the backend via fetch API.

**Tech Stack:** Python/FastAPI (backend), vanilla HTML/CSS/JS (demo site), SQLite/ChromaDB (existing), Sakura AI LLM (existing)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `backend/app/services/chat_service.py` | Shared keyword matching + Web response generation + conversation orchestration |
| `backend/app/schemas/web_chat.py` | Pydantic request/response schemas for web chat API |
| `backend/app/routers/web_chat.py` | `POST /api/web-chat` endpoint with rate limiting |
| `backend/tests/conftest.py` | Pytest fixtures: async DB session, test app client |
| `backend/tests/test_chat_service.py` | Tests for chat_service (keyword matching, web responses) |
| `backend/tests/test_web_chat.py` | Integration tests for web chat API endpoint |
| `demo-site/index.html` | Landing page |
| `demo-site/chat.html` | Web chat demo page |
| `demo-site/css/style.css` | All styles |
| `demo-site/js/api.js` | Backend API communication |
| `demo-site/js/chat.js` | Chat UI control |
| `demo-site/assets/salon-logo.svg` | Salon logo |
| `demo-site/assets/bot-avatar.svg` | Bot icon |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/services/rag_service.py:33` | Add `history` parameter to `generate_answer()` |
| `backend/app/services/line_handler.py:25-35` | Replace `KEYWORD_PATTERNS` with import from `chat_service` |
| `backend/app/main.py:15,40` | Add web_chat router import and registration |
| `backend/pyproject.toml:9` | Add `pytest`, `pytest-asyncio` to dev dependencies |
| `README.md` | Add demo site section |

---

### Task 1: Test infrastructure setup

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Add test dependencies**

In `backend/pyproject.toml`, add after the `dependencies` list:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.25",
]
```

- [ ] **Step 2: Install dev dependencies**

Run: `cd backend && uv sync --group dev`
Expected: Dependencies installed successfully

- [ ] **Step 3: Create test package and conftest**

Create `backend/tests/__init__.py` (empty file).

Create `backend/tests/conftest.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
async def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def client(db_session: AsyncSession):
    """Create an AsyncClient that uses the test DB session."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 4: Verify test setup works**

Create a smoke test at `backend/tests/test_smoke.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_app_starts(client):
    response = await client.get("/docs")
    assert response.status_code == 200
```

Run: `cd backend && uv run pytest tests/test_smoke.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/tests/
git commit -m "chore: add pytest infrastructure for backend tests"
```

---

### Task 2: Extract keyword matching into chat_service.py

**Files:**
- Create: `backend/app/services/chat_service.py`
- Create: `backend/tests/test_chat_service.py`

- [ ] **Step 1: Write failing tests for keyword matching**

Create `backend/tests/test_chat_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_chat_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.chat_service'`

- [ ] **Step 3: Implement chat_service.py**

Create `backend/app/services/chat_service.py`:

```python
import re

KEYWORD_PATTERNS: dict[str, re.Pattern] = {
    "booking": re.compile(r"予約|予約したい|予約する", re.IGNORECASE),
    "menu": re.compile(r"メニュー|料金|価格", re.IGNORECASE),
    "access": re.compile(r"アクセス|場所|行き方", re.IGNORECASE),
}

WEB_KEYWORD_RESPONSES: dict[str, dict] = {
    "booking": {
        "reply": (
            "ご予約ありがとうございます！\n"
            "下記URLからご希望の日時をお選びください。\n"
            "https://example.com/reserve\n"
            "\nお電話でも承っております（03-6789-0123）"
        ),
        "reply_type": "text",
        "quick_replies": ["メニューを見る", "アクセス", "営業時間"],
    },
    "menu": {
        "reply": (
            "当店のメニューと料金はこちらです：\n\n"
            "\U0001F487 カット: ¥5,500〜\n"
            "\U0001F3A8 カラー: ¥11,000〜\n"
            "\U0001F4AB パーマ: ¥13,200〜\n"
            "\u2728 トリートメント: ¥3,300〜\n\n"
            "詳しくはこちら: https://example.com/menu"
        ),
        "reply_type": "text",
        "quick_replies": ["予約する", "アクセス", "営業時間"],
    },
    "access": {
        "reply": (
            "\U0001F4CD Hair Salon BLOOM\n"
            "東京都渋谷区神宮前3-15-8 BLOOMビル2F\n\n"
            "\U0001F6B6 東京メトロ表参道駅 A2出口より徒歩5分\n"
            "\U0001F4DE 03-6789-0123\n\n"
            "\U0001F4CD Google Maps:\n"
            "https://maps.google.com/?q=東京都渋谷区神宮前3-15-8"
        ),
        "reply_type": "text",
        "quick_replies": ["メニューを見る", "予約する", "営業時間"],
    },
}


def match_keyword(text: str) -> str | None:
    """Match text against keyword patterns. Returns keyword key or None."""
    for key, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            return key
    return None


def get_web_keyword_response(keyword: str) -> dict | None:
    """Get a web-friendly response for a keyword. Returns None if keyword unknown."""
    return WEB_KEYWORD_RESPONSES.get(keyword)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_chat_service.py -v`
Expected: All 11 tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/chat_service.py backend/tests/test_chat_service.py
git commit -m "feat: extract keyword matching into chat_service.py with web responses"
```

---

### Task 3: Add conversation history support to rag_service.py

**Files:**
- Modify: `backend/app/services/rag_service.py:33-54`
- Create: `backend/tests/test_rag_service.py`

- [ ] **Step 1: Write failing test for history parameter**

Create `backend/tests/test_rag_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_rag_service.py -v`
Expected: FAIL — `TypeError: generate_answer() got an unexpected keyword argument 'history'`

- [ ] **Step 3: Modify rag_service.py to accept history**

Replace the `generate_answer` method in `backend/app/services/rag_service.py` (lines 33-54):

```python
    async def generate_answer(
        self, user_message: str, history: list[dict] | None = None
    ) -> str:
        """Generate an answer by retrieving relevant FAQ context and calling OpenAI."""
        try:
            results = chroma_service.query(user_message, n_results=3)

            if results:
                context = "\n\n".join(result["document"] for result in results)
            else:
                context = "参考情報はありません。"

            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            response = await self._client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content

        except Exception:
            logger.exception("Error generating RAG answer for message: %s", user_message)
            return FALLBACK_MESSAGE
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_rag_service.py -v`
Expected: All 2 tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/test_rag_service.py
git commit -m "feat: add conversation history support to rag_service.generate_answer()"
```

---

### Task 4: Add generate_web_reply() to chat_service.py

**Files:**
- Modify: `backend/app/services/chat_service.py`
- Modify: `backend/tests/test_chat_service.py`

- [ ] **Step 1: Write failing tests for generate_web_reply**

Append to `backend/tests/test_chat_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_chat_service.py::TestGenerateWebReply -v`
Expected: FAIL — `ImportError: cannot import name 'generate_web_reply'`

- [ ] **Step 3: Implement generate_web_reply**

Add to the bottom of `backend/app/services/chat_service.py`:

```python
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory
from app.services.chat_history_service import chat_history_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 5
DEFAULT_QUICK_REPLIES = ["メニューを見る", "予約する", "アクセス", "営業時間"]


async def generate_web_reply(
    message: str, session_id: str, db: AsyncSession
) -> dict:
    """Generate a reply for the web chat interface.

    1. Check keyword match -> return web keyword response
    2. Fetch recent conversation history from DB
    3. Call RAG with history for contextual answer
    4. Save user message and bot reply to DB
    5. Return formatted response dict
    """
    # Save user message
    await chat_history_service.save(db, session_id, "user", message)

    # 1. Keyword match
    keyword = match_keyword(message)
    if keyword:
        response = get_web_keyword_response(keyword)
        await chat_history_service.save(db, session_id, "bot", response["reply"])
        return response

    # 2. Fetch recent history (last N turns)
    history_records = await _get_recent_history(db, session_id)

    # 3. RAG with history
    answer = await rag_service.generate_answer(message, history=history_records)

    # 4. Save bot reply
    await chat_history_service.save(db, session_id, "bot", answer)

    # 5. Return
    return {
        "reply": answer,
        "reply_type": "text",
        "quick_replies": DEFAULT_QUICK_REPLIES,
    }


async def _get_recent_history(
    db: AsyncSession, session_id: str
) -> list[dict] | None:
    """Fetch the most recent conversation turns for context.

    Returns a list of {"role": "user"|"assistant", "content": str} dicts,
    excluding the current (just-saved) user message.
    """
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == session_id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(MAX_HISTORY_TURNS * 2 + 1)  # +1 for the just-saved user msg
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    if len(records) <= 1:
        return None

    # Drop the first record (the just-saved current user message)
    records = records[1:]
    # Reverse to chronological order
    records.reverse()

    history = []
    for record in records:
        role = "user" if record.message_type == "user" else "assistant"
        history.append({"role": role, "content": record.content})
    return history if history else None
```

Note: The `import` statements (`logging`, `select`, `AsyncSession`, `ChatHistory`, `chat_history_service`, `rag_service`) should be placed at the top of the file alongside the existing `import re`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_chat_service.py -v`
Expected: All 15 tests pass (11 from Task 2 + 4 new)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/chat_service.py backend/tests/test_chat_service.py
git commit -m "feat: add generate_web_reply() with conversation history to chat_service"
```

---

### Task 5: Create web chat API endpoint

**Files:**
- Create: `backend/app/schemas/web_chat.py`
- Create: `backend/app/routers/web_chat.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_web_chat.py`

- [ ] **Step 1: Write failing integration test**

Create `backend/tests/test_web_chat.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_web_chat.py -v`
Expected: FAIL — 404 (endpoint doesn't exist yet)

- [ ] **Step 3: Create Pydantic schemas**

Create `backend/app/schemas/web_chat.py`:

```python
from pydantic import BaseModel, Field, field_validator


class WebChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: str = Field(..., max_length=20)

    @field_validator("session_id")
    @classmethod
    def session_id_must_start_with_web(cls, v: str) -> str:
        if not v.startswith("web_"):
            raise ValueError("session_id must start with 'web_'")
        return v


class WebChatResponse(BaseModel):
    reply: str
    reply_type: str
    quick_replies: list[str]
```

- [ ] **Step 4: Create web_chat router**

Create `backend/app/routers/web_chat.py`:

```python
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.web_chat import WebChatRequest, WebChatResponse
from app.services.chat_service import generate_web_reply

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory rate limiter: {session_id: [timestamp, ...]}
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(session_id: str) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.time()
    if session_id not in _rate_limit_store:
        _rate_limit_store[session_id] = []

    # Remove timestamps older than the window
    _rate_limit_store[session_id] = [
        ts for ts in _rate_limit_store[session_id] if now - ts < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[session_id]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[session_id].append(now)
    return True


@router.post("/web-chat", response_model=WebChatResponse)
async def web_chat(
    request: WebChatRequest,
    db: AsyncSession = Depends(get_db),
) -> WebChatResponse:
    """Handle a web chat message and return an AI-generated reply."""
    if not _check_rate_limit(request.session_id):
        raise HTTPException(
            status_code=429,
            detail="リクエストが多すぎます。しばらくお待ちください。",
        )

    result = await generate_web_reply(request.message, request.session_id, db)
    return WebChatResponse(**result)
```

- [ ] **Step 5: Register router in main.py**

In `backend/app/main.py`, add the import after line 15:

```python
from app.routers.web_chat import router as web_chat_router
```

Add the router registration after line 40:

```python
app.include_router(web_chat_router, prefix="/api")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_web_chat.py -v`
Expected: All 5 tests pass

- [ ] **Step 7: Run all backend tests**

Run: `cd backend && uv run pytest tests/ -v`
Expected: All tests pass (smoke + chat_service + rag_service + web_chat)

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/web_chat.py backend/app/routers/web_chat.py backend/app/main.py backend/tests/test_web_chat.py
git commit -m "feat: add POST /api/web-chat endpoint with rate limiting"
```

---

### Task 6: Refactor line_handler.py to use shared keyword matching

**Files:**
- Modify: `backend/app/services/line_handler.py`

- [ ] **Step 1: Refactor line_handler.py**

Replace the contents of `backend/app/services/line_handler.py`:

```python
import logging

from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.chat_history_service import chat_history_service
from app.services.chat_service import match_keyword
from app.services.line_message_builder import (
    build_access_message,
    build_booking_message,
    build_menu_carousel,
)
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

KEYWORD_BUILDERS: dict[str, object] = {
    "booking": build_booking_message,
    "menu": build_menu_carousel,
    "access": build_access_message,
}


async def handle_text_message(event: MessageEvent, db: AsyncSession) -> None:
    """Handle an incoming LINE text message event."""
    user_id = event.source.user_id
    user_text = event.message.text
    reply_token = event.reply_token

    # Save the user's incoming message
    await chat_history_service.save(db, user_id, "user", user_text)

    # Check keyword patterns for rich message responses
    reply_messages = None
    bot_response_content = None

    keyword = match_keyword(user_text)
    if keyword and keyword in KEYWORD_BUILDERS:
        reply_messages = KEYWORD_BUILDERS[keyword]()
        bot_response_content = f"[{keyword}] keyword matched"

    # If no keyword match, use RAG to generate an answer
    if reply_messages is None:
        answer = await rag_service.generate_answer(user_text)
        reply_messages = [TextMessage(text=answer)]
        bot_response_content = answer

    # Save the bot response to chat history
    await chat_history_service.save(db, user_id, "bot", bot_response_content)

    # Send the reply via LINE Messaging API
    try:
        configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
        async with AsyncApiClient(configuration) as api_client:
            messaging_api = AsyncMessagingApi(api_client)
            await messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=reply_messages,
                )
            )
    except Exception:
        logger.exception("Failed to send LINE reply for user %s", user_id)
```

- [ ] **Step 2: Run all tests to verify nothing broke**

Run: `cd backend && uv run pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/line_handler.py
git commit -m "refactor: use shared match_keyword() from chat_service in line_handler"
```

---

### Task 7: Create demo-site JavaScript modules

**Files:**
- Create: `demo-site/js/api.js`
- Create: `demo-site/js/chat.js`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p demo-site/js demo-site/css demo-site/assets
```

- [ ] **Step 2: Create api.js**

Create `demo-site/js/api.js`:

```javascript
const API_BASE_URL = '';

async function sendChatMessage(message, sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/web-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (response.status === 429) {
    throw new Error('RATE_LIMITED');
  }
  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }
  return response.json();
}
```

- [ ] **Step 3: Create chat.js**

Create `demo-site/js/chat.js`:

```javascript
(function () {
  'use strict';

  const SESSION_KEY = 'bloom_session_id';
  const SESSION_TS_KEY = 'bloom_session_ts';
  const SESSION_TTL = 24 * 60 * 60 * 1000; // 24h

  let sessionId = null;
  let isSending = false;

  // --- Session management ---

  function getOrCreateSession() {
    const stored = localStorage.getItem(SESSION_KEY);
    const storedTs = localStorage.getItem(SESSION_TS_KEY);

    if (stored && storedTs && Date.now() - Number(storedTs) < SESSION_TTL) {
      return stored;
    }
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let rand = '';
    for (let i = 0; i < 16; i++) {
      rand += chars[Math.floor(Math.random() * chars.length)];
    }
    const id = 'web_' + rand;
    localStorage.setItem(SESSION_KEY, id);
    localStorage.setItem(SESSION_TS_KEY, String(Date.now()));
    return id;
  }

  // --- Time formatting ---

  function formatTime(date) {
    return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  }

  // --- DOM helpers ---

  function getEl(id) {
    return document.getElementById(id);
  }

  function scrollToBottom() {
    const area = getEl('chat-messages');
    area.scrollTop = area.scrollHeight;
  }

  // --- Bubble rendering ---

  function addBubble(type, text) {
    const area = getEl('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = `message-row ${type}`;

    let html = '';
    if (type === 'bot') {
      html += '<img src="assets/bot-avatar.svg" class="bot-avatar" alt="bot">';
    }
    html += '<div class="bubble-group">';
    html += `<div class="bubble ${type}-bubble">`;

    // Convert newlines to <br> and auto-link URLs
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    const linked = escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
    html += linked.replace(/\n/g, '<br>');

    html += '</div>';
    html += `<span class="timestamp">${formatTime(new Date())}</span>`;
    html += '</div>';

    wrapper.innerHTML = html;
    area.appendChild(wrapper);

    // Trigger animation
    requestAnimationFrame(() => wrapper.classList.add('visible'));
    scrollToBottom();
  }

  // --- Typing indicator ---

  function showTyping() {
    const area = getEl('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'message-row bot visible';
    wrapper.id = 'typing-indicator';
    wrapper.innerHTML = `
      <img src="assets/bot-avatar.svg" class="bot-avatar" alt="bot">
      <div class="bubble-group">
        <div class="bubble bot-bubble typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    `;
    area.appendChild(wrapper);
    scrollToBottom();
  }

  function hideTyping() {
    const el = getEl('typing-indicator');
    if (el) el.remove();
  }

  // --- Quick replies ---

  function addQuickReplies(replies) {
    // Remove existing quick replies
    const existing = getEl('chat-messages').querySelector('.quick-replies');
    if (existing) existing.remove();

    if (!replies || replies.length === 0) return;

    const container = document.createElement('div');
    container.className = 'quick-replies';
    replies.forEach((text) => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply-btn';
      btn.textContent = text;
      btn.addEventListener('click', () => {
        container.remove();
        sendMessage(text);
      });
      container.appendChild(btn);
    });
    getEl('chat-messages').appendChild(container);
    scrollToBottom();
  }

  // --- Send message ---

  async function sendMessage(text) {
    if (isSending || !text.trim()) return;
    isSending = true;

    const input = getEl('chat-input');
    const sendBtn = getEl('send-btn');
    input.disabled = true;
    sendBtn.disabled = true;

    // Remove existing quick replies
    const existing = getEl('chat-messages').querySelector('.quick-replies');
    if (existing) existing.remove();

    addBubble('user', text.trim());
    input.value = '';

    showTyping();

    try {
      const data = await sendChatMessage(text.trim(), sessionId);
      hideTyping();
      addBubble('bot', data.reply);
      if (data.quick_replies && data.quick_replies.length > 0) {
        addQuickReplies(data.quick_replies);
      }
    } catch (err) {
      hideTyping();
      if (err.message === 'RATE_LIMITED') {
        addBubble('bot', 'メッセージの送信回数が上限に達しました。\nしばらくお待ちいただいてから再度お試しください。');
      } else {
        addBubble('bot', '通信エラーが発生しました。\n再度お試しください。');
      }
    } finally {
      isSending = false;
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // --- Initialization ---

  function init() {
    sessionId = getOrCreateSession();

    const input = getEl('chat-input');
    const sendBtn = getEl('send-btn');

    // Send button click
    sendBtn.addEventListener('click', () => sendMessage(input.value));

    // Enter to send, Shift+Enter for newline
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input.value);
      }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    });

    // Initial bot message (no API call)
    setTimeout(() => {
      addBubble(
        'bot',
        'こんにちは！Hair Salon BLOOMです\uD83D\uDC90\nカット、カラー、パーマなどのメニューや、ご予約についてお気軽にお聞きください！'
      );
      addQuickReplies(['メニューを見る', '予約する', 'アクセス', '営業時間']);
    }, 300);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
```

- [ ] **Step 4: Commit**

```bash
git add demo-site/js/
git commit -m "feat: add chat.js and api.js for web chat demo"
```

---

### Task 8: Create SVG assets

**Files:**
- Create: `demo-site/assets/salon-logo.svg`
- Create: `demo-site/assets/bot-avatar.svg`

- [ ] **Step 1: Create salon logo SVG**

Create `demo-site/assets/salon-logo.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60" fill="none">
  <circle cx="30" cy="30" r="22" fill="#C9A96E" opacity="0.2"/>
  <path d="M30 12c-4 0-7 3-7 7 0 3 2 5 4 6-3 1-6 4-6 8 0 5 4 9 9 9s9-4 9-9c0-4-3-7-6-8 2-1 4-3 4-6 0-4-3-7-7-7z" fill="#8B7355"/>
  <path d="M22 24c-2 2-3 5-3 8 0 3 1 6 3 8" stroke="#C9A96E" stroke-width="1.5" fill="none"/>
  <path d="M38 24c2 2 3 5 3 8 0 3-1 6-3 8" stroke="#C9A96E" stroke-width="1.5" fill="none"/>
  <text x="62" y="28" font-family="serif" font-size="18" font-weight="600" fill="#8B7355">Hair Salon</text>
  <text x="62" y="48" font-family="serif" font-size="20" font-weight="700" fill="#C9A96E">BLOOM</text>
</svg>
```

- [ ] **Step 2: Create bot avatar SVG**

Create `demo-site/assets/bot-avatar.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="#8B7355"/>
  <rect x="12" y="13" width="16" height="14" rx="3" fill="#FAFAF5"/>
  <circle cx="16" cy="19" r="1.5" fill="#8B7355"/>
  <circle cx="24" cy="19" r="1.5" fill="#8B7355"/>
  <path d="M16 23c0 0 2 2 4 2s4-2 4-2" stroke="#8B7355" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <rect x="18" y="9" width="4" height="4" rx="2" fill="#C9A96E"/>
</svg>
```

- [ ] **Step 3: Commit**

```bash
git add demo-site/assets/
git commit -m "feat: add salon logo and bot avatar SVG assets"
```

---

### Task 9: Create chat.html

**Files:**
- Create: `demo-site/chat.html`

- [ ] **Step 1: Create chat.html**

Create `demo-site/chat.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AIチャットデモ | Hair Salon BLOOM</title>
  <meta property="og:title" content="LINE AIチャットボット デモ | Hair Salon BLOOM">
  <meta property="og:description" content="AIがお客様の質問に24時間自動応答。LINEに届いたメッセージにAIが回答するチャットボットのデモです。">
  <meta property="og:image" content="assets/og-image.png">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
</head>
<body class="chat-page">
  <div class="chat-layout">

    <!-- Side panel (PC only) -->
    <aside class="chat-sidebar">
      <a href="index.html" class="sidebar-logo">
        <img src="assets/salon-logo.svg" alt="Hair Salon BLOOM" width="160">
      </a>
      <h2>このデモについて</h2>
      <p>Hair Salon BLOOMの架空のLINEチャットボットです。AIがFAQデータをもとに自動応答します。</p>

      <div class="sidebar-links">
        <div class="sidebar-link-item">
          <span class="sidebar-label">実際のLINEでも試せます</span>
          <div class="qr-placeholder">QRコード（準備中）</div>
        </div>
        <div class="sidebar-link-item">
          <span class="sidebar-label">管理画面はこちら</span>
          <a href="#" class="sidebar-url">管理画面を開く &rarr;</a>
        </div>
        <div class="sidebar-link-item">
          <span class="sidebar-label">導入についてのご相談</span>
          <a href="#" class="sidebar-url">お問い合わせ &rarr;</a>
        </div>
      </div>

      <a href="index.html" class="back-link">&larr; トップページに戻る</a>
    </aside>

    <!-- Chat area -->
    <main class="chat-main">
      <div class="chat-container">
        <!-- Header -->
        <div class="chat-header">
          <a href="index.html" class="chat-back-btn" aria-label="戻る">&larr;</a>
          <img src="assets/bot-avatar.svg" class="chat-header-avatar" alt="" width="32" height="32">
          <div class="chat-header-info">
            <span class="chat-header-name">Hair Salon BLOOM</span>
            <span class="chat-header-badge">AI Chat</span>
          </div>
        </div>

        <!-- Messages -->
        <div class="chat-messages" id="chat-messages"></div>

        <!-- Input -->
        <div class="chat-input-area">
          <textarea id="chat-input" class="chat-input" placeholder="メッセージを入力..." rows="1"></textarea>
          <button id="send-btn" class="send-btn" aria-label="送信">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile description (collapsible) -->
      <details class="mobile-info">
        <summary>このデモについて</summary>
        <p>Hair Salon BLOOMの架空のLINEチャットボットです。AIがFAQデータをもとに自動応答します。</p>
        <a href="index.html">トップページに戻る</a>
      </details>
    </main>
  </div>

  <script src="js/api.js"></script>
  <script src="js/chat.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify file renders in browser**

Open `demo-site/chat.html` in a browser. It won't have styles yet, but the structure (header, message area, input) should be visible.

- [ ] **Step 3: Commit**

```bash
git add demo-site/chat.html
git commit -m "feat: add chat.html web chat demo page"
```

---

### Task 10: Create style.css

**Files:**
- Create: `demo-site/css/style.css`

- [ ] **Step 1: Create the complete stylesheet**

Create `demo-site/css/style.css`:

```css
/* ===== Reset & Base ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --primary: #8B7355;
  --accent: #C9A96E;
  --bg: #FAFAF5;
  --text: #333333;
  --text-light: #888888;
  --chat-bg: #E8E4DC;
  --bot-bubble: #FFFFFF;
  --user-bubble: #8CE28C;
  --white: #FFFFFF;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.10);
  --radius: 16px;
  --font: 'Noto Sans JP', sans-serif;
}

html { font-size: 16px; scroll-behavior: smooth; }
body { font-family: var(--font); color: var(--text); background: var(--bg); line-height: 1.7; -webkit-font-smoothing: antialiased; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; }
button { cursor: pointer; font-family: var(--font); }

/* ===== Chat Page ===== */
.chat-page { background: linear-gradient(135deg, #f5f0e8 0%, #FAFAF5 100%); min-height: 100vh; }

.chat-layout {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 48px;
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
}

/* --- Sidebar --- */
.chat-sidebar {
  flex: 0 0 280px;
  padding-top: 60px;
}
.chat-sidebar h2 {
  font-size: 1rem;
  font-weight: 700;
  margin: 24px 0 8px;
  color: var(--primary);
}
.chat-sidebar p {
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.6;
}
.sidebar-logo { display: block; margin-bottom: 8px; }
.sidebar-links { margin-top: 24px; display: flex; flex-direction: column; gap: 16px; }
.sidebar-link-item { display: flex; flex-direction: column; gap: 4px; }
.sidebar-label { font-size: 0.8rem; color: var(--text-light); }
.sidebar-url { font-size: 0.85rem; font-weight: 500; color: var(--primary); }
.qr-placeholder {
  width: 120px; height: 120px; background: var(--white);
  border: 2px dashed #ccc; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; color: #aaa;
}
.back-link { display: block; margin-top: 32px; font-size: 0.85rem; color: var(--primary); }

/* --- Chat Container --- */
.chat-main { flex: 0 1 420px; }

.chat-container {
  width: 100%;
  max-width: 420px;
  height: 80vh;
  max-height: 700px;
  background: var(--chat-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* --- Chat Header --- */
.chat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--primary);
  color: var(--white);
}
.chat-back-btn {
  color: var(--white);
  font-size: 1.2rem;
  text-decoration: none;
  display: none;
}
.chat-header-avatar { border-radius: 50%; }
.chat-header-info { display: flex; flex-direction: column; }
.chat-header-name { font-size: 0.9rem; font-weight: 700; }
.chat-header-badge {
  display: inline-block;
  font-size: 0.6rem;
  background: var(--accent);
  color: var(--white);
  padding: 1px 6px;
  border-radius: 8px;
  width: fit-content;
  margin-top: 2px;
}

/* --- Messages Area --- */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* --- Message Bubbles --- */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.message-row.visible {
  opacity: 1;
  transform: translateY(0);
}
.message-row.bot { justify-content: flex-start; }
.message-row.user { justify-content: flex-end; }

.bot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bubble-group {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}
.message-row.user .bubble-group {
  align-items: flex-end;
}

.bubble {
  padding: 10px 14px;
  font-size: 0.88rem;
  line-height: 1.6;
  word-break: break-word;
}
.bot-bubble {
  background: var(--bot-bubble);
  border-radius: 2px 12px 12px 12px;
  color: var(--text);
}
.user-bubble {
  background: var(--user-bubble);
  border-radius: 12px 2px 12px 12px;
  color: #1a3a1a;
}
.bubble a { color: #2b6cb0; text-decoration: underline; }
.bubble a:hover { color: #1a4d8f; }

.timestamp {
  font-size: 0.65rem;
  color: var(--text-light);
  margin-top: 2px;
  padding: 0 4px;
}

/* --- Typing indicator --- */
.bubble.typing {
  display: flex;
  gap: 4px;
  padding: 12px 18px;
}
.bubble.typing .dot {
  width: 8px; height: 8px;
  background: #bbb;
  border-radius: 50%;
  animation: typing 1.2s infinite;
}
.bubble.typing .dot:nth-child(2) { animation-delay: 0.2s; }
.bubble.typing .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

/* --- Quick Replies --- */
.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0 8px 40px;
}
.quick-reply-btn {
  background: var(--white);
  border: 1.5px solid var(--primary);
  color: var(--primary);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.2s, color 0.2s;
}
.quick-reply-btn:hover {
  background: var(--primary);
  color: var(--white);
}

/* --- Input Area --- */
.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px;
  background: var(--white);
  border-top: 1px solid #e0dcd5;
}
.chat-input {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 0.88rem;
  font-family: var(--font);
  resize: none;
  max-height: 100px;
  line-height: 1.5;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input:focus { border-color: var(--primary); }
.send-btn {
  width: 40px; height: 40px;
  border: none;
  border-radius: 50%;
  background: var(--user-bubble);
  color: #1a5a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.1s;
}
.send-btn:hover { background: #6fcf6f; }
.send-btn:active { transform: scale(0.95); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* --- Mobile info --- */
.mobile-info {
  display: none;
  margin-top: 16px;
  background: var(--white);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.85rem;
}
.mobile-info summary {
  cursor: pointer;
  font-weight: 500;
  color: var(--primary);
}
.mobile-info p { margin: 8px 0; color: var(--text-light); }
.mobile-info a { display: block; margin-top: 8px; }

/* ===== Landing Page ===== */
.landing-page { overflow-x: hidden; }

/* --- Header / Nav --- */
.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  max-width: 1100px;
  margin: 0 auto;
}
.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-badge {
  background: var(--accent);
  color: var(--white);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}
.header-nav {
  display: flex;
  gap: 24px;
  list-style: none;
}
.header-nav a {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text);
}
.header-nav a:hover { color: var(--primary); }

/* --- Hero --- */
.hero {
  text-align: center;
  padding: 80px 24px 60px;
  max-width: 760px;
  margin: 0 auto;
}
.hero h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.5;
  margin-bottom: 16px;
}
.hero .subtitle {
  font-size: 1.05rem;
  color: var(--text-light);
  margin-bottom: 36px;
}
.cta-group { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary);
  color: var(--white);
  font-size: 1rem;
  font-weight: 700;
  padding: 14px 32px;
  border-radius: 50px;
  border: none;
  transition: background 0.2s, transform 0.1s;
  text-decoration: none;
}
.btn-primary:hover { background: #76614a; text-decoration: none; }
.btn-primary:active { transform: scale(0.98); }
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: var(--primary);
  font-size: 0.95rem;
  font-weight: 600;
  padding: 14px 28px;
  border-radius: 50px;
  border: 2px solid var(--primary);
  transition: background 0.2s;
  text-decoration: none;
}
.btn-secondary:hover { background: rgba(139, 115, 85, 0.08); text-decoration: none; }

/* --- Section base --- */
.section {
  padding: 64px 24px;
  max-width: 1100px;
  margin: 0 auto;
}
.section-title {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 40px;
}

/* --- Features --- */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.feature-card {
  background: var(--white);
  border-radius: 12px;
  padding: 32px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  text-align: center;
}
.feature-icon {
  font-size: 2.2rem;
  margin-bottom: 16px;
}
.feature-card h3 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--primary);
}
.feature-card p {
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.6;
}

/* --- Screenshots --- */
.screenshots-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: center;
}
.screenshot-box {
  background: var(--white);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  text-align: center;
}
.screenshot-placeholder {
  width: 100%;
  height: 300px;
  background: #eee;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-size: 0.85rem;
}
.screenshot-box h3 {
  margin-top: 12px;
  font-size: 0.9rem;
  color: var(--primary);
}

/* --- Steps --- */
.steps-list {
  max-width: 600px;
  margin: 0 auto;
  list-style: none;
  counter-reset: step;
}
.steps-list li {
  counter-increment: step;
  position: relative;
  padding: 16px 0 16px 60px;
  border-left: 2px solid #e0dcd5;
  margin-left: 20px;
}
.steps-list li::before {
  content: counter(step);
  position: absolute;
  left: -15px;
  width: 28px;
  height: 28px;
  background: var(--primary);
  color: var(--white);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
}
.steps-list li:last-child { border-left-color: transparent; }
.steps-note {
  text-align: center;
  margin-top: 24px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent);
}

/* --- Pricing --- */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.pricing-card {
  background: var(--white);
  border-radius: 12px;
  padding: 32px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  text-align: center;
  border-top: 4px solid transparent;
  transition: transform 0.2s;
}
.pricing-card:hover { transform: translateY(-4px); }
.pricing-card.featured { border-top-color: var(--accent); }
.pricing-card h3 {
  font-size: 1.1rem;
  color: var(--primary);
  margin-bottom: 8px;
}
.pricing-price {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 16px;
}
.pricing-price small { font-size: 0.5em; font-weight: 400; color: var(--text-light); }
.pricing-features {
  list-style: none;
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 2;
  text-align: left;
}
.pricing-features li::before { content: "\2713  "; color: var(--accent); font-weight: 700; }
.pricing-note {
  text-align: center;
  margin-top: 16px;
  font-size: 0.8rem;
  color: var(--text-light);
}

/* --- Bottom CTA --- */
.bottom-cta {
  text-align: center;
  padding: 64px 24px;
  background: var(--primary);
  color: var(--white);
}
.bottom-cta h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 16px;
}
.bottom-cta p {
  font-size: 0.95rem;
  opacity: 0.85;
  margin-bottom: 24px;
}
.bottom-cta .btn-primary {
  background: var(--accent);
  color: var(--white);
}
.bottom-cta .btn-primary:hover { background: #b89a5e; }

/* --- Footer --- */
.site-footer {
  text-align: center;
  padding: 24px;
  font-size: 0.8rem;
  color: var(--text-light);
}
.site-footer a { color: var(--primary); }

/* ===== Scroll Animation ===== */
.fade-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  /* Chat page */
  .chat-layout { padding: 0; gap: 0; }
  .chat-sidebar { display: none; }
  .chat-main { flex: 1; width: 100%; }
  .chat-container {
    max-width: 100%;
    height: 100vh;
    max-height: none;
    border-radius: 0;
    box-shadow: none;
  }
  .chat-back-btn { display: block; }
  .mobile-info { display: block; }

  /* Landing page */
  .site-header { padding: 12px 16px; }
  .header-nav { display: none; }
  .hero { padding: 48px 20px 40px; }
  .hero h1 { font-size: 1.4rem; }
  .hero .subtitle { font-size: 0.9rem; }
  .cta-group { flex-direction: column; align-items: center; }
  .features-grid { grid-template-columns: 1fr; }
  .screenshots-grid { grid-template-columns: 1fr; }
  .pricing-grid { grid-template-columns: 1fr; }
  .section { padding: 40px 16px; }
  .section-title { font-size: 1.2rem; }
}
```

- [ ] **Step 2: Open chat.html in browser and verify styling**

Open `demo-site/chat.html` in a browser. Verify:
- Chat container is centered, has rounded corners, shadow
- Header shows salon name with brown background
- Message area has beige background
- Input area is at the bottom with green send button

- [ ] **Step 3: Commit**

```bash
git add demo-site/css/style.css
git commit -m "feat: add complete CSS for chat demo and landing page"
```

---

### Task 11: Create index.html landing page

**Files:**
- Create: `demo-site/index.html`

- [ ] **Step 1: Create index.html**

Create `demo-site/index.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LINE AIチャットボット デモ | Hair Salon BLOOM</title>
  <meta property="og:title" content="LINE AIチャットボット デモ | Hair Salon BLOOM">
  <meta property="og:description" content="AIがお客様の質問に24時間自動応答。LINEに届いたメッセージにAIが回答するチャットボットのデモです。">
  <meta property="og:image" content="assets/og-image.png">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
</head>
<body class="landing-page">

  <!-- Header -->
  <header class="site-header">
    <div class="header-brand">
      <img src="assets/salon-logo.svg" alt="Hair Salon BLOOM" height="40">
      <span class="header-badge">AI Chat Demo</span>
    </div>
    <nav>
      <ul class="header-nav">
        <li><a href="chat.html">チャットを試す</a></li>
        <li><a href="#">管理画面を見る</a></li>
        <li><a href="#pricing">導入について</a></li>
      </ul>
    </nav>
  </header>

  <!-- Hero -->
  <section class="hero">
    <h1>LINEに届いたお客様の質問に、<br>AIが24時間お答えします</h1>
    <p class="subtitle">FAQ登録だけで導入完了。プログラミング知識は不要です。</p>
    <div class="cta-group">
      <a href="chat.html" class="btn-primary">今すぐチャットを試す &rarr;</a>
      <a href="#" class="btn-secondary">管理画面を見る</a>
    </div>
  </section>

  <!-- Features -->
  <section class="section fade-in">
    <h2 class="section-title">3つの特徴</h2>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">&#x1F4AC;</div>
        <h3>AIが自然文で回答</h3>
        <p>定型文ではなく、登録されたFAQ情報をもとにAIが文脈を理解して回答します</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#x1F4F1;</div>
        <h3>LINE公式アカウントに対応</h3>
        <p>お客様は普段使っているLINEからそのまま質問できます</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#x2699;</div>
        <h3>管理画面からFAQ編集</h3>
        <p>質問と回答を追加・編集するだけ。技術的な作業は一切不要です</p>
      </div>
    </div>
  </section>

  <!-- Screenshots -->
  <section class="section fade-in">
    <h2 class="section-title">実際の画面</h2>
    <div class="screenshots-grid">
      <div class="screenshot-box">
        <div class="screenshot-placeholder">LINE実機スクリーンショット（準備中）</div>
        <h3>LINEトーク画面</h3>
      </div>
      <div class="screenshot-box">
        <div class="screenshot-placeholder">管理画面スクリーンショット（準備中）</div>
        <h3>FAQ管理画面</h3>
      </div>
    </div>
  </section>

  <!-- Steps -->
  <section class="section fade-in">
    <h2 class="section-title">導入ステップ</h2>
    <ol class="steps-list">
      <li>LINE公式アカウントの作成（無料）</li>
      <li>チャットボットの初期設定（こちらで対応）</li>
      <li>FAQ情報のご提供</li>
      <li>テスト・調整</li>
      <li>本番稼働開始</li>
    </ol>
    <p class="steps-note">最短3日で導入可能</p>
  </section>

  <!-- Pricing -->
  <section class="section fade-in" id="pricing">
    <h2 class="section-title">料金プラン</h2>
    <div class="pricing-grid">
      <div class="pricing-card">
        <h3>ライト</h3>
        <div class="pricing-price">&yen;50,000<small>〜</small></div>
        <ul class="pricing-features">
          <li>FAQ 30件まで</li>
          <li>Web埋め込みチャット</li>
          <li>メールサポート</li>
        </ul>
      </div>
      <div class="pricing-card featured">
        <h3>スタンダード</h3>
        <div class="pricing-price">&yen;150,000<small>〜</small></div>
        <ul class="pricing-features">
          <li>FAQ無制限</li>
          <li>LINE連携</li>
          <li>管理画面付き</li>
          <li>チャットサポート</li>
        </ul>
      </div>
      <div class="pricing-card">
        <h3>プレミアム</h3>
        <div class="pricing-price">&yen;300,000<small>〜</small></div>
        <ul class="pricing-features">
          <li>全機能</li>
          <li>カスタム機能開発</li>
          <li>保守サポート1ヶ月</li>
          <li>専任担当者</li>
        </ul>
      </div>
    </div>
    <p class="pricing-note">※デモ用の参考価格です</p>
  </section>

  <!-- Bottom CTA -->
  <section class="bottom-cta">
    <h2>導入のご相談・お見積もりはこちら</h2>
    <p>まずはお気軽にお問い合わせください</p>
    <div class="cta-group">
      <a href="chat.html" class="btn-primary">まずはチャットをお試しください &rarr;</a>
    </div>
  </section>

  <!-- Footer -->
  <footer class="site-footer">
    <p>This is a demo application built by Yoshi |
      <a href="#">GitHub</a>
    </p>
  </footer>

  <!-- Scroll animation -->
  <script>
    document.addEventListener('DOMContentLoaded', function () {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      }, { threshold: 0.1 });

      document.querySelectorAll('.fade-in').forEach(function (el) {
        observer.observe(el);
      });
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Open index.html in browser and verify**

Open `demo-site/index.html` in a browser. Verify:
- Header with logo and navigation
- Hero section with CTA buttons
- 3 feature cards
- Screenshot placeholders
- 5-step process
- 3 pricing cards (middle one highlighted)
- Bottom CTA section
- Footer
- Scroll fade-in animations trigger as you scroll

- [ ] **Step 3: Commit**

```bash
git add demo-site/index.html
git commit -m "feat: add landing page with hero, features, pricing, and scroll animations"
```

---

### Task 12: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add demo site section to README**

Append before the `## 環境変数` section in `README.md`:

```markdown
## デモサイト

ブラウザで AI チャットを体験できるデモサイトです。

### 構成

- `demo-site/index.html` — ランディングページ（機能紹介・料金プラン）
- `demo-site/chat.html` — Web チャットデモ（LINE 風 UI で AI と会話）

### ローカルで確認

バックエンドを起動した状態で、`demo-site/` 内の HTML を直接ブラウザで開くか、簡易サーバーで配信します。

```bash
# バックエンドが http://localhost:8000 で起動中
cd demo-site
python -m http.server 5500
# http://localhost:5500 でアクセス
```

API 通信はデフォルトで相対パス（`/api/web-chat`）を使用します。
ローカル開発ではプロキシまたは CORS 設定で `http://localhost:5500` を許可してください。

### デプロイ

静的サイトとして Vercel / Cloudflare Pages / Netlify にデプロイ可能です。

```bash
# Vercel の場合
cd demo-site
vercel --prod
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add demo site section to README"
```

---

### Task 13: Delete smoke test and clean up

**Files:**
- Delete: `backend/tests/test_smoke.py`

- [ ] **Step 1: Remove smoke test**

Delete `backend/tests/test_smoke.py` (it was only for verifying test setup).

- [ ] **Step 2: Run all backend tests one final time**

Run: `cd backend && uv run pytest tests/ -v`
Expected: All tests pass (test_chat_service: 15, test_rag_service: 2, test_web_chat: 5 = 22 total)

- [ ] **Step 3: Commit**

```bash
git rm backend/tests/test_smoke.py
git commit -m "chore: remove temporary smoke test"
```

---

## Summary

| Task | Description | Files | Tests |
|------|-------------|-------|-------|
| 1 | Test infrastructure | pyproject.toml, conftest.py | 1 smoke |
| 2 | Keyword matching extraction | chat_service.py | 11 |
| 3 | RAG history support | rag_service.py | 2 |
| 4 | generate_web_reply() | chat_service.py | 4 |
| 5 | Web chat API endpoint | web_chat.py, schemas, main.py | 5 |
| 6 | line_handler.py refactor | line_handler.py | - (run existing) |
| 7 | JS modules | api.js, chat.js | - (manual browser) |
| 8 | SVG assets | salon-logo.svg, bot-avatar.svg | - |
| 9 | chat.html | chat.html | - (manual browser) |
| 10 | CSS | style.css | - (manual browser) |
| 11 | Landing page | index.html | - (manual browser) |
| 12 | README | README.md | - |
| 13 | Cleanup | test_smoke.py | 22 total |
