import datetime
from typing import Any, Dict, Optional


class RealtimeEventType:
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_STATUS_CHANGED = "CASE_STATUS_CHANGED"
    CASE_PRIORITY_CHANGED = "CASE_PRIORITY_CHANGED"
    LAWYER_ASSIGNED = "LAWYER_ASSIGNED"
    CASE_ARCHIVED = "CASE_ARCHIVED"
    NOTIFICATION_DISPATCHED = "NOTIFICATION_DISPATCHED"
    HEARTBEAT = "HEARTBEAT"


def build_event_envelope(
    event_type: str,
    payload: Dict[str, Any],
    actor: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a standardized realtime event envelope.
    """
    return {
        "event": event_type,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "actor": actor or {"user_id": None, "name": "System", "role": "system"},
        "payload": payload,
    }
