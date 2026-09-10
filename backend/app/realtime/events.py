import itertools
import threading
from typing import Dict, Any, Optional
from app.utils import now_utc


class RealtimeEventType:
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_VERIFIED = "CASE_VERIFIED"
    CASE_RETURNED = "CASE_RETURNED"
    CASE_PRIORITY_CHANGED = "CASE_PRIORITY_CHANGED"
    LAWYER_NOTIFICATION_CREATED = "LAWYER_NOTIFICATION_CREATED"
    CASE_ASSIGNED = "CASE_ASSIGNED"
    CASE_ARCHIVED = "CASE_ARCHIVED"

    # Backward compatibility alias
    CASE_STATUS_CHANGED = "CASE_UPDATED"
    NOTIFICATION_DISPATCHED = "LAWYER_NOTIFICATION_CREATED"
    HEARTBEAT = "HEARTBEAT"


# Thread-safe global sequence counter
_seq_lock = threading.Lock()
_seq_counter = itertools.count(1)


def next_event_sequence() -> int:
    with _seq_lock:
        return next(_seq_counter)


def build_event_envelope(
    event_type: str,
    payload: Dict[str, Any],
    actor: Optional[Dict[str, Any]] = None,
    seq: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a standardized, monotonic DLAS realtime event envelope.
    Includes sequential sequence number (seq) and unique event ID for deduplication and ordering.
    """
    now = now_utc()
    sequence_num = seq if seq is not None else next_event_sequence()
    timestamp_epoch_ms = int(now.timestamp() * 1000)
    event_id = f"evt_{sequence_num}_{timestamp_epoch_ms}"

    return {
        "event_id": event_id,
        "seq": sequence_num,
        "event": event_type,
        "timestamp": now.isoformat(),
        "actor": actor or {"user_id": None, "name": "System", "role": "system"},
        "payload": payload,
    }
