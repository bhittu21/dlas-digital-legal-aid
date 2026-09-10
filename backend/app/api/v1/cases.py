import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.case import Case, CaseStatus, CasePriority
from app.models.user import User, UserRole
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseVerifyRequest,
    CaseRequestInfoRequest,
    CaseRejectRequest,
    CasePriorityRequest,
    CaseAssignRequest,
    CaseArchiveRequest,
    CaseResponse,
    CaseListResponse,
)
from app.schemas.audit import AuditLogResponse
from app.services.case_workflow import CaseWorkflowService
from app.api.deps import get_current_user, require_dlao, get_client_ip

router = APIRouter()


@router.get("", response_model=CaseListResponse)
def list_cases(
    status: Optional[str] = Query(None, description="Filter by CaseStatus enum"),
    priority: Optional[str] = Query(None, description="Filter by CasePriority enum"),
    district: Optional[str] = Query(None, description="Filter by district"),
    legal_category: Optional[str] = Query(None, description="Filter by legal category"),
    assigned_lawyer_id: Optional[int] = Query(None, description="Filter by assigned panel lawyer ID"),
    search: Optional[str] = Query(None, description="Search tracking ID, title, applicant name, or phone"),
    include_archived: bool = Query(False, description="Include archived cases"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    List legal aid cases with authoritative filtering, search, and pagination.
    """
    query = db.query(Case)

    if not include_archived:
        query = query.filter(Case.archived == False)

    # Role-based case scoping
    if current_user and current_user.role == UserRole.PANEL_LAWYER:
        # Panel lawyers see their assigned cases OR cases waiting in PANEL_LAWYER_QUEUE
        query = query.filter(
            or_(
                Case.assigned_lawyer_id == current_user.id,
                Case.status == CaseStatus.PANEL_LAWYER_QUEUE
            )
        )
    elif current_user and current_user.role == UserRole.APPLICANT:
        # Applicants see only their own cases by phone number
        if current_user.phone_number:
            query = query.filter(Case.applicant_phone == current_user.phone_number)

    if status:
        query = query.filter(Case.status == status)

    if priority:
        query = query.filter(Case.priority == priority)

    if district:
        query = query.filter(Case.district.ilike(f"%{district}%"))

    if legal_category:
        query = query.filter(Case.legal_category == legal_category)

    if assigned_lawyer_id is not None:
        query = query.filter(Case.assigned_lawyer_id == assigned_lawyer_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Case.tracking_id.ilike(s),
                Case.title.ilike(s),
                Case.title_bn.ilike(s),
                Case.applicant_name.ilike(s),
                Case.applicant_phone.ilike(s),
                Case.applicant_nid.ilike(s),
                Case.description.ilike(s),
            )
        )

    total = query.count()
    total_pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    items = query.order_by(Case.created_at.desc()).offset(offset).limit(size).all()

    return CaseListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case_intake(
    case_in: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Intake submission endpoint. Creates case in authoritative database,
    records immutable audit log, and emits realtime WebSocket event.
    """
    ip_address = get_client_ip(request)
    case = await CaseWorkflowService.create_case(
        db=db,
        case_in=case_in,
        actor=current_user,
        ip_address=ip_address,
    )
    return case


@router.get("/{case_id}", response_model=CaseResponse)
def get_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full case details.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_in: CaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update permitted case metadata fields.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.update_details(
        db=db,
        case_id=case_id,
        case_in=case_in,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/verify", response_model=CaseResponse)
async def verify_case(
    case_id: int,
    verify_req: CaseVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    MANDATORY HUMAN GATE:
    Human DLAO officer verifies case eligibility and moves it to VERIFIED / PANEL_LAWYER_QUEUE.
    Automated AI accounts are strictly blocked with 403 Forbidden.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.verify_case(
        db=db,
        case_id=case_id,
        req=verify_req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/request-info", response_model=CaseResponse)
async def request_additional_info(
    case_id: int,
    req: CaseRequestInfoRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    Return case for additional information/documentation from applicant.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.request_information(
        db=db,
        case_id=case_id,
        req=req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/reject", response_model=CaseResponse)
async def reject_case(
    case_id: int,
    req: CaseRejectRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    DLAO statutory rejection of ineligible legal aid request.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.reject_case(
        db=db,
        case_id=case_id,
        req=req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/priority", response_model=CaseResponse)
async def change_case_priority(
    case_id: int,
    req: CasePriorityRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    Modify urgency priority (LOW, MEDIUM, HIGH, EMERGENCY).
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.update_priority(
        db=db,
        case_id=case_id,
        req=req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/assign", response_model=CaseResponse)
async def assign_case_to_lawyer(
    case_id: int,
    req: CaseAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    Assign a verified legal-aid case from PANEL_LAWYER_QUEUE to a panel advocate.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.assign_panel_lawyer(
        db=db,
        case_id=case_id,
        req=req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.post("/{case_id}/archive", response_model=CaseResponse)
async def archive_case(
    case_id: int,
    req: CaseArchiveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dlao),
):
    """
    Archive/delete case with explicit human officer authorization.
    """
    ip_address = get_client_ip(request)
    return await CaseWorkflowService.archive_case(
        db=db,
        case_id=case_id,
        req=req,
        actor=current_user,
        ip_address=ip_address,
    )


@router.get("/{case_id}/audit-logs", response_model=List[AuditLogResponse])
def get_case_audit_logs(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve immutable audit history for a specific case.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.audit_logs
