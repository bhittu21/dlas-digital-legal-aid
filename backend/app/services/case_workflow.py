import datetime
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.case import Case, CaseStatus, CasePriority, LegalCategory
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditAction
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseVerifyRequest,
    CaseRequestInfoRequest,
    CaseRejectRequest,
    CasePriorityRequest,
    CaseAssignRequest,
    CaseArchiveRequest,
)
from app.services.audit_service import record_audit_log
from app.services.notification_service import create_notification
from app.realtime.connection_manager import manager
from app.realtime.events import RealtimeEventType


def generate_tracking_id(db: Session) -> str:
    """
    Generate sequential DLAS tracking identifier: DLAS-YYYY-XXXX
    """
    year = datetime.datetime.utcnow().year
    prefix = f"DLAS-{year}-"
    # Count existing cases this year to determine next sequence
    count = db.query(func.count(Case.id)).filter(Case.tracking_id.like(f"{prefix}%")).scalar() or 0
    next_seq = count + 1
    return f"{prefix}{next_seq:04d}"


class CaseWorkflowService:

    @staticmethod
    async def create_case(
        db: Session,
        case_in: CaseCreate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> Case:
        actor_name = actor.full_name if actor else case_in.applicant_name
        actor_role = actor.role if actor else UserRole.APPLICANT
        actor_id = actor.id if actor else None

        tracking_id = generate_tracking_id(db)

        # Initial intake status
        initial_status = CaseStatus.PENDING_HUMAN_REVIEW if case_in.ai_summary else CaseStatus.NEW

        case = Case(
            tracking_id=tracking_id,
            title=case_in.title,
            title_bn=case_in.title_bn,
            description=case_in.description,
            description_bn=case_in.description_bn,
            legal_category=case_in.legal_category,
            status=initial_status,
            priority=case_in.priority,
            applicant_name=case_in.applicant_name,
            applicant_phone=case_in.applicant_phone,
            applicant_nid=case_in.applicant_nid,
            applicant_nid_verified=False,
            applicant_income_bdt=case_in.applicant_income_bdt,
            applicant_gender=case_in.applicant_gender,
            district=case_in.district,
            upazila=case_in.upazila,
            intake_channel=case_in.intake_channel,
            audio_recording_url=case_in.audio_recording_url,
            ai_summary=case_in.ai_summary,
            ai_urgency_score=case_in.ai_urgency_score,
            version=1,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Audit log in database transaction
        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            action=AuditAction.CASE_CREATED,
            previous_state=None,
            new_state=case.status,
            notes=f"Initial intake via {case.intake_channel}",
            ip_address=ip_address,
            commit=True,
        )

        # Broadcast realtime event to DLAO dashboard
        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_CREATED,
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "title": case.title,
                "status": case.status,
                "priority": case.priority,
                "district": case.district,
                "legal_category": case.legal_category,
            },
            actor={"user_id": actor_id, "name": actor_name, "role": actor_role},
        )

        return case

    @staticmethod
    async def transition_to_ai_intake(
        db: Session,
        case_id: int,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.status != CaseStatus.NEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition to AI_INTAKE from status: {case.status}"
            )

        prev = case.status
        case.status = CaseStatus.AI_INTAKE
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.SUBMITTED_FOR_REVIEW,
            previous_state=prev,
            new_state=case.status,
            notes="AI intake parsing initiated",
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_STATUS_CHANGED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "status": case.status},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def complete_ai_intake(
        db: Session,
        case_id: int,
        ai_summary: str,
        urgency_score: str,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        AI agent completes intake. Status must transition ONLY to PENDING_HUMAN_REVIEW.
        Gemini is NEVER permitted to transition directly to VERIFIED or PANEL_LAWYER_QUEUE.
        """
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.status not in [CaseStatus.NEW, CaseStatus.AI_INTAKE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete AI intake from current status: {case.status}"
            )

        prev = case.status
        case.status = CaseStatus.PENDING_HUMAN_REVIEW
        case.ai_summary = ai_summary
        case.ai_urgency_score = urgency_score
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.AI_INTAKE_COMPLETED,
            previous_state=prev,
            new_state=case.status,
            notes=f"AI intake completed. Advisory urgency: {urgency_score}",
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_STATUS_CHANGED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "status": case.status},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def verify_case(
        db: Session,
        case_id: int,
        req: CaseVerifyRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        MANDATORY HUMAN GATE:
        Only an authorized human DLAO or Admin may verify a case.
        Gemini / system_ai is strictly blocked with 403 Forbidden.
        """
        if actor.role == UserRole.SYSTEM_AI:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Constraint: Automated AI is strictly prohibited from verifying cases."
            )

        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only human District Legal Aid Officers (DLAO) or Admins may verify cases."
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.archived:
            raise HTTPException(status_code=400, detail="Cannot verify an archived case.")

        # Route alternate actions if submitted to verify endpoint
        if getattr(req, "action", None) == "NEEDS_INFORMATION":
            return await CaseWorkflowService.request_information(
                db=db,
                case_id=case_id,
                req=CaseRequestInfoRequest(info_needed=req.notes or "Additional information requested"),
                actor=actor,
                ip_address=ip_address,
            )
        elif getattr(req, "action", None) == "REJECTED":
            return await CaseWorkflowService.reject_case(
                db=db,
                case_id=case_id,
                req=CaseRejectRequest(reason=req.notes or "Rejected upon judicial review"),
                actor=actor,
                ip_address=ip_address,
            )

        if case.status not in [CaseStatus.PENDING_HUMAN_REVIEW, CaseStatus.NEEDS_INFORMATION, CaseStatus.VERIFIED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot verify case from current status: {case.status}. Expected PENDING_HUMAN_REVIEW."
            )

        prev_status = case.status
        # Transition target
        target_status = CaseStatus.PANEL_LAWYER_QUEUE if req.route_to_panel_queue else CaseStatus.VERIFIED

        case.status = target_status
        case.verification_notes = req.notes
        case.verified_by_id = actor.id
        case.verified_at = datetime.datetime.utcnow()
        if req.priority:
            case.priority = req.priority
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.CASE_VERIFIED,
            previous_state=prev_status,
            new_state=case.status,
            notes=f"Verified by DLAO. Notes: {req.notes}",
            ip_address=ip_address,
            commit=True,
        )

        # Primary Case State Transition Event Broadcast
        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_VERIFIED,
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "status": case.status,
                "verified_by": actor.full_name,
                "verification_notes": req.notes,
            },
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )

        # Notify panel lawyer when case enters panel lawyer queue
        if target_status == CaseStatus.PANEL_LAWYER_QUEUE:
            lawyer = db.query(User).filter(User.role == UserRole.PANEL_LAWYER).first()
            if lawyer:
                existing_notif = db.query(Notification).filter(
                    Notification.case_id == case.id,
                    Notification.user_id == lawyer.id,
                ).first()
                if not existing_notif:
                    create_notification(
                        db=db,
                        user_id=lawyer.id,
                        case_id=case.id,
                        title=f"New Case Verified & Added to Panel Queue: {case.tracking_id}",
                        title_bn=f"নতুন মামলা যাচাই সম্পন্ন ও প্যানেল আইনজীবী কিউতে যুক্ত: {case.tracking_id}",
                        message=f"Case {case.tracking_id} ({case.applicant_name}) is now verified and available in the panel lawyer queue.",
                        message_bn=f"মামলা {case.tracking_id} ({case.applicant_name}) এখন প্যানেল আইনজীবী কিউতে পর্যালোচনার জন্য প্রস্তুত।",
                        notification_type=NotificationType.STATUS_CHANGED,
                        commit=True,
                    )
                    await manager.broadcast_event(
                        event_type=RealtimeEventType.LAWYER_NOTIFICATION_CREATED,
                        payload={
                            "case_id": case.id,
                            "tracking_id": case.tracking_id,
                            "lawyer_id": lawyer.id,
                        },
                    )

        return case

    @staticmethod
    async def request_information(
        db: Session,
        case_id: int,
        req: CaseRequestInfoRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        DLAO returns case to applicant requesting additional documents/information.
        """
        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only human DLAO officers may request additional information."
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.status not in [CaseStatus.PENDING_HUMAN_REVIEW, CaseStatus.AI_INTAKE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request info from status: {case.status}"
            )

        prev = case.status
        case.status = CaseStatus.NEEDS_INFORMATION
        case.verification_notes = f"Additional Information Needed: {req.info_needed}"
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.REQUESTED_INFORMATION,
            previous_state=prev,
            new_state=case.status,
            notes=req.info_needed,
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_RETURNED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "status": case.status, "notes": req.info_needed},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def reject_case(
        db: Session,
        case_id: int,
        req: CaseRejectRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        DLAO rejects case as legally ineligible.
        AI systems are strictly prohibited from rejecting cases.
        """
        if actor.role == UserRole.SYSTEM_AI:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Constraint: Automated AI cannot reject cases."
            )

        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only human DLAO officers may reject cases."
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.status not in [CaseStatus.PENDING_HUMAN_REVIEW, CaseStatus.NEEDS_INFORMATION]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject case from current status: {case.status}"
            )

        prev = case.status
        case.status = CaseStatus.REJECTED
        case.verification_notes = f"Rejection Reason: {req.reason}"
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.CASE_REJECTED,
            previous_state=prev,
            new_state=case.status,
            notes=req.reason,
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_STATUS_CHANGED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "status": case.status},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def update_priority(
        db: Session,
        case_id: int,
        req: CasePriorityRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only DLAO officers or Admins may modify case priority."
            )

        if req.priority not in CasePriority.ALL_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {req.priority}")

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        prev_priority = case.priority
        case.priority = req.priority
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.PRIORITY_CHANGED,
            previous_state=prev_priority,
            new_state=case.priority,
            notes=req.reason,
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_PRIORITY_CHANGED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "priority": case.priority},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def assign_panel_lawyer(
        db: Session,
        case_id: int,
        req: CaseAssignRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        Assign a verified case in PANEL_LAWYER_QUEUE to an active panel lawyer.
        Transitions case to LAWYER_REVIEW.
        """
        if actor.role == UserRole.SYSTEM_AI:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Constraint: Automated AI cannot assign panel lawyers."
            )

        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only human DLAO officers may assign panel lawyers."
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.status not in [CaseStatus.PANEL_LAWYER_QUEUE, CaseStatus.VERIFIED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case must be in PANEL_LAWYER_QUEUE or VERIFIED to assign a lawyer. Current status: {case.status}"
            )

        # Validate lawyer
        lawyer = db.query(User).filter(User.id == req.lawyer_id).first()
        if not lawyer or lawyer.role != UserRole.PANEL_LAWYER:
            raise HTTPException(status_code=400, detail="Target user is not an active panel lawyer.")

        prev_status = case.status
        case.status = CaseStatus.LAWYER_REVIEW
        case.assigned_lawyer_id = lawyer.id
        case.assigned_at = datetime.datetime.utcnow()
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        # Audit log
        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.LAWYER_ASSIGNED,
            previous_state=prev_status,
            new_state=case.status,
            notes=f"Assigned to {lawyer.full_name}. Notes: {req.notes or 'None'}",
            ip_address=ip_address,
            commit=True,
        )

        # Notify lawyer
        create_notification(
            db=db,
            user_id=lawyer.id,
            case_id=case.id,
            title=f"New Legal Aid Matter Assigned: {case.tracking_id}",
            title_bn=f"নতুন মামলা অর্পণ করা হয়েছে: {case.tracking_id}",
            message=f"You have been appointed to represent {case.applicant_name} ({case.legal_category}).",
            message_bn=f"আপনাকে {case.applicant_name} এর আইনগত প্রতিনিধিত্বের জন্য নিযুক্ত করা হয়েছে।",
            commit=True,
        )

        # Realtime broadcast: CASE_ASSIGNED and LAWYER_NOTIFICATION_CREATED
        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_ASSIGNED,
            payload={
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "assigned_lawyer_id": lawyer.id,
                "assigned_lawyer_name": lawyer.full_name,
                "status": case.status,
            },
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        await manager.broadcast_event(
            event_type=RealtimeEventType.LAWYER_NOTIFICATION_CREATED,
            payload={
                "user_id": lawyer.id,
                "case_id": case.id,
                "tracking_id": case.tracking_id,
                "title": f"New Legal Aid Matter Assigned: {case.tracking_id}",
            },
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def archive_case(
        db: Session,
        case_id: int,
        req: CaseArchiveRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        """
        Archive/delete case with explicit human authorization.
        """
        if actor.role == UserRole.SYSTEM_AI:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Constraint: Automated AI cannot archive or delete cases."
            )

        if actor.role not in UserRole.VERIFIER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only human DLAO officers or Admins may archive cases."
            )

        if not req.authorization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit human authorization is required to archive/delete a case."
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        prev_status = case.status
        case.archived = True
        case.status = CaseStatus.ARCHIVED
        case.archived_at = datetime.datetime.utcnow()
        case.archived_by_id = actor.id
        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.CASE_ARCHIVED,
            previous_state=prev_status,
            new_state=case.status,
            notes=f"Archived with human authorization. Reason: {req.reason}",
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_ARCHIVED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id, "status": case.status},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case

    @staticmethod
    async def update_details(
        db: Session,
        case_id: int,
        case_in: CaseUpdate,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Case:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = case_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(case, key, value)

        case.version += 1
        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        record_audit_log(
            db=db,
            case_id=case.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.role,
            action=AuditAction.CASE_UPDATED,
            previous_state=None,
            new_state=case.status,
            notes="Case metadata updated",
            ip_address=ip_address,
            commit=True,
        )

        await manager.broadcast_event(
            event_type=RealtimeEventType.CASE_UPDATED,
            payload={"case_id": case.id, "tracking_id": case.tracking_id},
            actor={"user_id": actor.id, "name": actor.full_name, "role": actor.role},
        )
        return case
