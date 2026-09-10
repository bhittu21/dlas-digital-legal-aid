from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus
from app.schemas.auth import LawyerResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[LawyerResponse])
def list_panel_lawyers(
    district: Optional[str] = Query(None, description="Filter by district"),
    specialization: Optional[str] = Query(None, description="Filter by legal specialization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List active panel lawyers for assignment, including current active case workloads.
    """
    query = db.query(User).filter(
        User.role == UserRole.PANEL_LAWYER,
        User.is_active == True
    )

    if district:
        query = query.filter(User.district.ilike(f"%{district}%"))

    if specialization:
        query = query.filter(User.specialization.ilike(f"%{specialization}%"))

    lawyers = query.all()
    results = []

    for lawyer in lawyers:
        active_count = db.query(func.count(Case.id)).filter(
            Case.assigned_lawyer_id == lawyer.id,
            Case.status.in_([CaseStatus.LAWYER_REVIEW, CaseStatus.VERIFIED]),
            Case.archived == False
        ).scalar() or 0

        results.append(
            LawyerResponse(
                id=lawyer.id,
                full_name=lawyer.full_name,
                full_name_bn=lawyer.full_name_bn,
                district=lawyer.district,
                specialization=lawyer.specialization,
                phone_number=lawyer.phone_number,
                active_cases_count=active_count,
            )
        )

    return results
