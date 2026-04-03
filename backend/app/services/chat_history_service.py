import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Singleton service for chat history CRUD operations."""

    async def save(
        self,
        db: AsyncSession,
        user_id: str,
        message_type: str,
        content: str,
    ) -> ChatHistory:
        """Insert a new ChatHistory record and commit."""
        record = ChatHistory(
            user_id=user_id,
            message_type=message_type,
            content=content,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: str,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatHistory]:
        """Get chat history for a specific user with optional date filtering."""
        stmt = select(ChatHistory).where(ChatHistory.user_id == user_id)
        if date_from is not None:
            stmt = stmt.where(ChatHistory.timestamp >= date_from)
        if date_to is not None:
            stmt = stmt.where(ChatHistory.timestamp <= date_to)
        stmt = stmt.order_by(ChatHistory.timestamp.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_unique_users(self, db: AsyncSession) -> list[dict]:
        """Get unique users with their last message, last timestamp, and message count."""
        # Subquery: get the latest message id per user
        latest_msg = (
            select(
                ChatHistory.user_id,
                func.max(ChatHistory.id).label("max_id"),
                func.max(ChatHistory.timestamp).label("last_timestamp"),
                func.count(ChatHistory.id).label("message_count"),
            )
            .group_by(ChatHistory.user_id)
            .subquery()
        )
        stmt = (
            select(
                latest_msg.c.user_id,
                ChatHistory.content.label("last_message"),
                latest_msg.c.last_timestamp,
                latest_msg.c.message_count,
            )
            .join(ChatHistory, ChatHistory.id == latest_msg.c.max_id)
            .order_by(latest_msg.c.last_timestamp.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            {
                "user_id": row.user_id,
                "last_message": row.last_message,
                "last_timestamp": row.last_timestamp,
                "message_count": row.message_count,
            }
            for row in rows
        ]

    async def get_recent(self, db: AsyncSession, limit: int = 20) -> list[ChatHistory]:
        """Get the most recent chat history records."""
        stmt = (
            select(ChatHistory)
            .order_by(ChatHistory.timestamp.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_today_count(self, db: AsyncSession) -> int:
        """Get the total number of messages sent today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.count(ChatHistory.id))
            .where(ChatHistory.timestamp >= today_start)
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_weekly_unique_count(self, db: AsyncSession) -> int:
        """Get the number of unique users in the last 7 days."""
        week_ago = datetime.now() - timedelta(days=7)
        stmt = (
            select(func.count(func.distinct(ChatHistory.user_id)))
            .where(ChatHistory.timestamp >= week_ago)
        )
        result = await db.execute(stmt)
        return result.scalar() or 0


chat_history_service = ChatHistoryService()
