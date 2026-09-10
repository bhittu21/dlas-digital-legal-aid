def test_mock_nid_smart_card_verification(client):
    payload = {
        "nid_number": "1234567890",
        "date_of_birth": "1990-05-15",
        "name": "Rashidul Islam"
    }
    res = client.post("/api/v1/mock-nid/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["mode"] == "DEMO_MOCK_ADAPTER"
    assert "disclaimer" in data
    assert "Rashidul" in data["name_en"]


def test_mock_nid_legacy_17_digit_verification(client):
    payload = {
        "nid_number": "19852691234567890",
        "date_of_birth": "1985-11-20",
    }
    res = client.post("/api/v1/mock-nid/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["name_en"] == "Khadija Begum"
    assert data["name_bn"] == "খাদিজা বেগম"


def test_mock_nid_invalid_format(client):
    payload = {
        "nid_number": "12345",  # Invalid length (neither 10 nor 13/17)
        "date_of_birth": "1992-01-01"
    }
    # Pydantic schema enforces min_length 10 so either 422 or 200 with is_valid=False
    res = client.post("/api/v1/mock-nid/verify", json=payload)
    assert res.status_code in [200, 422]
    if res.status_code == 200:
        assert res.json()["is_valid"] is False
