import logging
import re

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
from app.services.line_message_builder import (
    build_access_message,
    build_booking_message,
    build_menu_carousel,
)
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

KEYWORD_PATTERNS: dict[str, re.Pattern] = {
    "booking": re.compile(r"予約|予約したい|予約する", re.IGNORECASE),
    "menu": re.compile(r"メニュー|料金|価格", re.IGNORECASE),
    "access": re.compile(r"アクセス|場所|行き方", re.IGNORECASE),
}

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

    for key, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(user_text):
            reply_messages = KEYWORD_BUILDERS[key]()
            bot_response_content = f"[{key}] keyword matched"
            break

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
