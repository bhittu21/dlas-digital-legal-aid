from app.models.case import Case, CaseStatus
from app.models.user import User, UserRole


def test_list_lawyers_and_workload(client, dlao_headers):
    res = client.get("/api/v1/lawyers", headers=dlao_headers)
    assert res.status_code == 200
    lawyers = res.json()
    assert len(lawyers) >= 4
    for lawyer in lawyers:
        assert "active_cases_count" in lawyer
        assert "specialization" in lawyer


def test_lawyer_receives_assignment_notification(client, dlao_headers, lawyer_headers, db):
    # Find case in PANEL_LAWYER_QUEUE
    case = db.query(Case).filter(Case.status == CaseStatus.PANEL_LAWYER_QUEUE).first()
    assert case is not None

    lawyer = db.query(User).filter(User.role == UserRole.PANEL_LAWYER).first()
    assert lawyer is not None

    # Assign lawyer
    assign_res = client.post(
        f"/api/v1/cases/{case.id}/assign",
        json={"lawyer_id": lawyer.id, "notes": "Urgent representation required."},
        headers=dlao_headers
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == CaseStatus.LAWYER_REVIEW

    # Check lawyer notifications
    notif_res = client.get("/api/v1/notifications", headers=lawyer_headers)
    assert notif_res.status_code == 200
    notifications = notif_res.json()
    assert len(notifications) >= 1
    recent = notifications[0]
    assert case.tracking_id in recent["title"]
    assert recent["is_read"] is False

    # Mark as read
    read_res = client.patch(f"/api/v1/notifications/{recent['id']}/read", headers=lawyer_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
