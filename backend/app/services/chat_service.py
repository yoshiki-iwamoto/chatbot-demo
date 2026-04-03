import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory
from app.services.chat_history_service import chat_history_service
from app.services.rag_service import rag_service

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
