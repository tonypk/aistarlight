from fastapi import APIRouter

from backend.api.audit import router as audit_router
from backend.api.dashboard import router as dashboard_router
from backend.api.auth import router as auth_router
from backend.api.bank_recon import router as bank_recon_router
from backend.api.chat import router as chat_router
from backend.api.compliance import router as compliance_router
from backend.api.corrections import router as corrections_router
from backend.api.receipts import router as receipts_router
from backend.api.data import router as data_router
from backend.api.forms import router as forms_router
from backend.api.knowledge import router as knowledge_router
from backend.api.reconciliation import router as reconciliation_router
from backend.api.memory import router as memory_router
from backend.api.reports import router as reports_router
from backend.api.settings import router as settings_router
from backend.api.withholding import router as withholding_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(data_router)
api_router.include_router(reports_router)
api_router.include_router(memory_router)
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(settings_router)
api_router.include_router(audit_router)
api_router.include_router(forms_router)
api_router.include_router(reconciliation_router)
api_router.include_router(withholding_router)
api_router.include_router(corrections_router)
api_router.include_router(compliance_router)
api_router.include_router(receipts_router)
api_router.include_router(bank_recon_router)
api_router.include_router(dashboard_router)
