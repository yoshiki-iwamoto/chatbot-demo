from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.faq import FAQ
from app.schemas.faq import FAQCreate, FAQResponse, FAQUpdate
from app.services.chroma_service import chroma_service

router = APIRouter()


@router.get("", response_model=list[FAQResponse])
async def list_faqs(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FAQ)
    if category is not None:
        stmt = stmt.where(FAQ.category == category)
    stmt = stmt.order_by(FAQ.updated_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    data: FAQCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    faq = FAQ(category=data.category, question=data.question, answer=data.answer)
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    chroma_service.add_faq(faq.id, faq.question, faq.answer, faq.category)
    return faq


@router.put("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    data: FAQUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if faq is None:
        raise HTTPException(status_code=404, detail="FAQ not found")
    if data.category is not None:
        faq.category = data.category
    if data.question is not None:
        faq.question = data.question
    if data.answer is not None:
        faq.answer = data.answer
    await db.commit()
    await db.refresh(faq)
    chroma_service.add_faq(faq.id, faq.question, faq.answer, faq.category)
    return faq


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if faq is None:
        raise HTTPException(status_code=404, detail="FAQ not found")
    await db.delete(faq)
    await db.commit()
    chroma_service.delete_faq(faq_id)
