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
