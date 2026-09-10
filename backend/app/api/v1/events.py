from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models.user import User
from app.realtime.connection_manager import manager

router = APIRouter()


@router.get("/since")
def get_events_since(
    since_seq: int = Query(0, ge=0, description="Last sequence ID received by the client"),
    current_user: User = Depends(get_current_user),
):
    """
    Missed-event recovery endpoint for reconnecting clients.
    Returns buffered events occurred strictly after `since_seq`.
    If the requested sequence has been purged from the circular buffer,
    returns reset_required: True, instructing the client to perform a full server state refresh.
    """
    events, reset_required, latest_seq = manager.get_events_since(since_seq)
    return {
        "since_seq": since_seq,
        "latest_seq": latest_seq,
        "reset_required": reset_required,
        "count": len(events),
        "events": events,
    }
