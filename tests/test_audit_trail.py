from app.models.case import Case, CaseStatus
from app.models.audit import AuditLog, AuditAction


def test_audit_log_created_on_mutations(client, dlao_headers, db):
    # 1. Create case
    case_payload = {
        "title": "Audit Verification Test Case",
        "description": "Testing immutable audit trail creation.",
        "applicant_name": "Audit Applicant",
        "applicant_phone": "+8801700998877",
        "district": "Dhaka",
        "priority": "LOW",
    }
    create_res = client.post("/api/v1/cases", json=case_payload, headers=dlao_headers)
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # Check case audit logs
    audit_res = client.get(f"/api/v1/cases/{case_id}/audit-logs", headers=dlao_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    assert logs[0]["action"] == AuditAction.CASE_CREATED

    # 2. Change priority
    prio_res = client.post(
        f"/api/v1/cases/{case_id}/priority",
        json={"priority": "HIGH", "reason": "Immediate urgency assessed"},
        headers=dlao_headers
    )
    assert prio_res.status_code == 200

    audit_res2 = client.get(f"/api/v1/cases/{case_id}/audit-logs", headers=dlao_headers)
    actions = [log["action"] for log in audit_res2.json()]
    assert AuditAction.PRIORITY_CHANGED in actions

    # 3. System-wide audit query
    sys_audit = client.get("/api/v1/audit-logs", headers=dlao_headers)
    assert sys_audit.status_code == 200
    assert len(sys_audit.json()) > 0
