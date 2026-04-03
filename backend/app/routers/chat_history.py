from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.schemas.chat_history import ChatHistoryResponse, UserSummary
from app.services.chat_history_service import chat_history_service

router = APIRouter()


@router.get("/users", response_model=list[UserSummary])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return await chat_history_service.get_unique_users(db)


@router.get("/users/{user_id}", response_model=list[ChatHistoryResponse])
async def get_user_history(
    user_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return await chat_history_service.get_by_user(
        db,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
