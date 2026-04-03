from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables

# Import all models so Base.metadata sees them
from app.models import ChatHistory, FAQ  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.chat_history import router as chat_history_router
from app.routers.dashboard import router as dashboard_router
from app.routers.faq import router as faq_router
from app.routers.webhook import router as webhook_router
from app.services.chroma_service import chroma_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    chroma_service.initialize()
    yield


app = FastAPI(title="Hair Salon BLOOM Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/webhook")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(faq_router, prefix="/api/faqs")
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(chat_history_router, prefix="/api/chat-history")
