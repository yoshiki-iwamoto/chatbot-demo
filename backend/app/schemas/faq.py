from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FAQCreate(BaseModel):
    category: str
    question: str
    answer: str


class FAQUpdate(BaseModel):
    category: str | None = None
    question: str | None = None
    answer: str | None = None


class FAQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime
