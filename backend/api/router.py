from fastapi import APIRouter

from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.data import router as data_router
from backend.api.memory import router as memory_router
from backend.api.reports import router as reports_router
from backend.api.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(data_router)
api_router.include_router(reports_router)
api_router.include_router(memory_router)
api_router.include_router(chat_router)
api_router.include_router(settings_router)
