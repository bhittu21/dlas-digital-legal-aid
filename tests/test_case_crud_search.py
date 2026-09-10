from app.models.case import Case, CaseStatus, CasePriority


def test_list_cases_and_filters(client, dlao_headers):
    # List all
    res = client.get("/api/v1/cases", headers=dlao_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 12
    assert len(data["items"]) > 0

    # Filter by status: PENDING_HUMAN_REVIEW
    res_pending = client.get("/api/v1/cases?status=PENDING_HUMAN_REVIEW", headers=dlao_headers)
    assert res_pending.status_code == 200
    for item in res_pending.json()["items"]:
        assert item["status"] == "PENDING_HUMAN_REVIEW"

    # Filter by priority: EMERGENCY
    res_urg = client.get("/api/v1/cases?priority=EMERGENCY", headers=dlao_headers)
    assert res_urg.status_code == 200
    for item in res_urg.json()["items"]:
        assert item["priority"] == "EMERGENCY"


def test_case_search(client, dlao_headers):
    # Search by known applicant name: "Shahnaz"
    res = client.get("/api/v1/cases?search=Shahnaz", headers=dlao_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1
    assert "Shahnaz" in items[0]["applicant_name"]

    # Search by tracking ID
    res_track = client.get("/api/v1/cases?search=DLAS-2026-0001", headers=dlao_headers)
    assert res_track.status_code == 200
    assert len(res_track.json()["items"]) == 1
    assert res_track.json()["items"][0]["tracking_id"] == "DLAS-2026-0001"


def test_case_detail_and_update(client, dlao_headers, db):
    case = db.query(Case).first()
    res = client.get(f"/api/v1/cases/{case.id}", headers=dlao_headers)
    assert res.status_code == 200
    assert res.json()["tracking_id"] == case.tracking_id

    # Update metadata
    update_payload = {"upazila": "Updated Upazila Name"}
    patch_res = client.patch(f"/api/v1/cases/{case.id}", json=update_payload, headers=dlao_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["upazila"] == "Updated Upazila Name"


def test_case_archive_authorization(client, dlao_headers, db):
    case = db.query(Case).first()

    # Rejection without authorization flag
    fail_res = client.post(
        f"/api/v1/cases/{case.id}/archive",
        json={"authorization": False, "reason": "Test without authorization"},
        headers=dlao_headers
    )
    assert fail_res.status_code == 400

    # Successful archive with explicit human authorization
    success_res = client.post(
        f"/api/v1/cases/{case.id}/archive",
        json={"authorization": True, "reason": "Authorized legal archival upon matter resolution"},
        headers=dlao_headers
    )
    assert success_res.status_code == 200
    assert success_res.json()["archived"] is True
    assert success_res.json()["status"] == CaseStatus.ARCHIVED
