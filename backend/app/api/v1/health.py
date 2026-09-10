import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.utils import now_utc

router = APIRouter()


@router.get("/health", summary="System Health & Diagnostic Check")
def check_health(db: Session = Depends(get_db)):
    """
    Diagnostic health check validating API responsiveness and persistent database connectivity.
    Essential for Render health check monitoring.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": now_utc().isoformat(),
    }
