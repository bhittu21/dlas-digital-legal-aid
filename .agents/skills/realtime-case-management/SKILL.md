---
name: realtime-case-management
description: Realtime synchronization, WebSocket architecture, case event schemas, DLAO live queue dispatch, and reconnect convergence.
---

# Realtime Case Management & WebSocket Architecture

## 1. Realtime Topology & Purpose
The DLAO (District Legal Aid Officer) and Panel Lawyer dashboards rely on low-latency bidirectional WebSocket communication (`/ws`) to maintain live situational awareness:
- Instant notification when an AI intake completes and arrives in `PENDING_HUMAN_REVIEW`.
- Immediate queue reflection when a case is verified and moves into `PANEL_LAWYER_QUEUE`.
- Live lock/claim status when a panel lawyer accepts or is assigned a matter.
- Live priority escalations (e.g. domestic violence emergency cases marked `EMERGENCY`).

## 2. Event Payload Schema Standards
All events broadcast over `/ws` must conform to the standard DLAS event envelope:
```json
{
  "event": "CASE_STATUS_CHANGED",
  "timestamp": "2026-09-10T10:30:00.000Z",
  "actor": {
    "user_id": 1,
    "name": "Mahmudur Rahman (DLAO)",
    "role": "dlao_officer"
  },
  "payload": {
    "case_id": "DLAS-2026-0012",
    "case_numeric_id": 12,
    "previous_status": "PENDING_HUMAN_REVIEW",
    "new_status": "VERIFIED",
    "priority": "HIGH",
    "assigned_lawyer_id": null,
    "updated_at": "2026-09-10T10:30:00.000Z"
  }
}
```

Standard Event Catalog:
- `CASE_CREATED`: Fresh intake ingested via Web/IVR.
- `CASE_STATUS_CHANGED`: Case state machine transition.
- `CASE_PRIORITY_CHANGED`: Urgency level adjusted by human officer.
- `LAWYER_ASSIGNED`: Case assigned to a verified panel advocate.
- `NOTIFICATION_DISPATCHED`: User notification created.
- `SYSTEM_HEARTBEAT`: Ping/pong connection keepalive.

## 3. Reconnection & Drift Convergence Protocol
1. **Heartbeat**: The server or client emits a `{"type": "ping"}` every 30 seconds; client responds with `{"type": "pong"}`.
2. **Exponential Backoff**: If WebSocket connection terminates, client attempts reconnection with jitter (1s, 2s, 5s, 10s, max 30s).
3. **Reconvergence Hydration**: Upon successful reconnection, the client must trigger a background REST query (`GET /api/v1/cases?status=...`) to reconcile any events missed during downtime. Never rely solely on queued WebSockets across network partitions.

## 4. Concurrency & Optimistic Lock Protection
- To prevent two DLAO officers simultaneously reviewing and assigning conflicting panel advocates to the same case, the backend enforces optimistic concurrency via an entity `version` or strict atomic state transition conditions (`UPDATE cases SET status='VERIFIED', version=version+1 WHERE id=:id AND status='PENDING_HUMAN_REVIEW' AND version=:expected_version`).
- If an update conflicts, the API returns `409 Conflict`, and the client fetches the latest authoritative state.
