from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    message_type: str
    content: str
    timestamp: datetime


class UserSummary(BaseModel):
    user_id: str
    last_message: str
    last_timestamp: datetime
    message_count: int
