from fastapi import APIRouter
from app.api.v1 import health, auth, cases, lawyers, notifications, audit, nid, events, intake

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Diagnostics"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Identity"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Management & Workflow"])
api_router.include_router(lawyers.router, prefix="/lawyers", tags=["Panel Lawyers Directory"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit Trails"])
api_router.include_router(nid.router, prefix="/mock-nid", tags=["Demo Identity Adapter"])
api_router.include_router(events.router, prefix="/events", tags=["Realtime Event Streams"])
api_router.include_router(intake.router, prefix="/intake", tags=["Legal Aid Intake & DBLA Form"])


