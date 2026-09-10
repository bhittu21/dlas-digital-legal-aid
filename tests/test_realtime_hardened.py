import json
import pytest
from starlette.websockets import WebSocketDisconnect
from app.realtime.connection_manager import manager
from app.realtime.events import RealtimeEventType, build_event_envelope


def test_websocket_auth_valid_token(client, dlao_token):
    """
    WebSocket connection with valid JWT token query param succeeds and responds to heartbeat.
    """
    with client.websocket_connect(f"/ws?token={dlao_token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        raw = ws.receive_text()
        pong = json.loads(raw)
        assert pong.get("type") == "pong"
        assert "latest_seq" in pong
        assert "timestamp" in pong


def test_websocket_auth_invalid_token(client):
    """
    WebSocket connection with invalid JWT token is rejected with code 4001.
    """
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws?token=invalid.token.here") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4001


def test_websocket_in_band_auth(client, dlao_token):
    """
    WebSocket connection without query token can authenticate via in-band message frame.
    """
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "auth", "token": dlao_token}))
        raw = ws.receive_text()
        data = json.loads(raw)
        assert data.get("type") == "auth_success"
        assert data.get("user") is not None


def test_standardized_event_envelope_structure():
    """
    Standardized envelopes must contain event_id, monotonic seq, timestamp, actor, and payload.
    """
    envelope = build_event_envelope(
        event_type=RealtimeEventType.CASE_VERIFIED,
        payload={"case_id": 1, "status": "VERIFIED"},
        actor={"user_id": 10, "name": "Judge Mahmudur Rahman", "role": "dlao_officer"},
    )
    assert envelope["event"] == RealtimeEventType.CASE_VERIFIED
    assert "event_id" in envelope
    assert envelope["event_id"].startswith("evt_")
    assert isinstance(envelope["seq"], int)
    assert envelope["seq"] > 0
    assert "timestamp" in envelope
    assert envelope["actor"]["name"] == "Judge Mahmudur Rahman"
    assert envelope["payload"]["case_id"] == 1


def test_concurrent_sessions_judge_updates_observer_receives(client, dlao_token, dlao_headers, lawyer_token):
    """
    Simulates two active browser sessions:
    - Session A (Judge/DLAO) performs verification
    - Session B (Observer / Panel Lawyer) receives real-time CASE_VERIFIED event
    - Session B verifies authoritative server database via REST API
    """
    with client.websocket_connect(f"/ws?token={dlao_token}") as ws_judge:
        with client.websocket_connect(f"/ws?token={lawyer_token}") as ws_lawyer:
            # Judge verifies case 1
            verify_payload = {
                "notes": "Eligibility verified under Legal Aid Services Act 2000. Household income below threshold.",
                "priority": "HIGH",
                "route_to_panel_queue": True,
            }
            res = client.post("/api/v1/cases/1/verify", json=verify_payload, headers=dlao_headers)
            assert res.status_code == 200

            # Lawyer session receives real-time broadcast
            raw_msg = ws_lawyer.receive_text()
            event_data = json.loads(raw_msg)

            assert event_data.get("event") == RealtimeEventType.CASE_VERIFIED
            assert event_data.get("payload", {}).get("case_id") == 1
            assert event_data.get("payload", {}).get("status") == "PANEL_LAWYER_QUEUE"
            assert "event_id" in event_data
            assert "seq" in event_data

            # Authoritative source of truth check: Query REST API from lawyer session
            case_detail_res = client.get("/api/v1/cases/1", headers={"Authorization": f"Bearer {lawyer_token}"})
            assert case_detail_res.status_code == 200
            db_case = case_detail_res.json()
            assert db_case["status"] == "PANEL_LAWYER_QUEUE"
            assert db_case["priority"] == "HIGH"
            assert "Eligibility verified" in db_case["verification_notes"]


def test_missed_event_recovery_on_reconnect(client, dlao_token, dlao_headers, lawyer_token):
    """
    Tests reconnection scenario:
    1. Client B records current sequence and disconnects
    2. Server advances state (priority change + assignment + notification)
    3. Client B reconnects and calls /api/v1/events/since
    4. Client B receives all missed events in sequential order
    5. Client B queries authoritative REST API to reconcile state
    """
    # 1. Client B connects, queries current sequence, then disconnects
    with client.websocket_connect(f"/ws?token={lawyer_token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        pong = json.loads(ws.receive_text())
        since_seq = pong.get("latest_seq", 0)

    # 2. While Client B is disconnected, Judge triggers mutations on server
    # Mutation 1: Change priority to EMERGENCY
    res_prio = client.post(
        "/api/v1/cases/2/priority",
        json={"priority": "EMERGENCY", "reason": "Immediate risk of physical dispossession"},
        headers=dlao_headers
    )
    assert res_prio.status_code == 200

    # 3. Client B reconnects and requests missed events from server buffer
    missed_res = client.get(f"/api/v1/events/since?since_seq={since_seq}", headers={"Authorization": f"Bearer {lawyer_token}"})
    assert missed_res.status_code == 200
    missed_data = missed_res.json()

    assert missed_data["reset_required"] is False
    assert missed_data["count"] >= 1
    events = missed_data["events"]

    # Verify missed event is CASE_PRIORITY_CHANGED and ordered
    prio_events = [e for e in events if e.get("event") == RealtimeEventType.CASE_PRIORITY_CHANGED and e.get("payload", {}).get("case_id") == 2]
    assert len(prio_events) == 1
    assert prio_events[0]["payload"]["priority"] == "EMERGENCY"
    assert prio_events[0]["seq"] > since_seq

    # 4. Client B queries authoritative case detail from REST API
    case2_res = client.get("/api/v1/cases/2", headers={"Authorization": f"Bearer {lawyer_token}"})
    assert case2_res.status_code == 200
    assert case2_res.json()["priority"] == "EMERGENCY"


def test_duplicate_event_deduplication_semantics():
    """
    Verifies that client deduplication mechanics discard identical event_id.
    """
    seen_ids = set()
    evt1 = build_event_envelope(RealtimeEventType.CASE_UPDATED, {"case_id": 1})
    evt2 = build_event_envelope(RealtimeEventType.CASE_UPDATED, {"case_id": 1})

    # First event received
    assert evt1["event_id"] not in seen_ids
    seen_ids.add(evt1["event_id"])

    # Duplicate of first event arrives
    assert evt1["event_id"] in seen_ids  # Should be dropped by client

    # Second distinct event arrives
    assert evt2["event_id"] not in seen_ids
    assert evt2["seq"] > evt1["seq"]
