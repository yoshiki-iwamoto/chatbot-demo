from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.faq import FAQ
from app.schemas.dashboard import DashboardStats
from app.services.chat_history_service import chat_history_service

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    today_messages = await chat_history_service.get_today_count(db)
    weekly_unique_users = await chat_history_service.get_weekly_unique_count(db)

    result = await db.execute(select(func.count(FAQ.id)))
    total_faqs = result.scalar() or 0

    recent_chats = await chat_history_service.get_recent(db, limit=5)

    return DashboardStats(
        today_messages=today_messages,
        weekly_unique_users=weekly_unique_users,
        total_faqs=total_faqs,
        recent_chats=recent_chats,
    )
