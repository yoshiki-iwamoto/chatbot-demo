from pydantic import BaseModel

from app.schemas.chat_history import ChatHistoryResponse


class DashboardStats(BaseModel):
    today_messages: int
    weekly_unique_users: int
    total_faqs: int
    recent_chats: list[ChatHistoryResponse]
