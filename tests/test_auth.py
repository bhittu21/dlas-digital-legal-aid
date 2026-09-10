def test_register_and_login_applicant(client):
    register_payload = {
        "email": "new.citizen@example.com",
        "password": "SecurePassword123!",
        "full_name": "Jannatul Ferdous",
        "full_name_bn": "জান্নাতুল ফেরদৌস",
        "phone_number": "+8801700112233",
        "district": "Barishal"
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "new.citizen@example.com"
    assert user_data["role"] == "applicant"

    # Login
    login_payload = {
        "email": "new.citizen@example.com",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "applicant"

    # Test /me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "new.citizen@example.com"


def test_login_invalid_password(client):
    login_payload = {
        "email": "dlao.dhaka@dlas.gov.bd",
        "password": "WrongPassword!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 401


def test_register_duplicate_email(client):
    payload = {
        "email": "dlao.dhaka@dlas.gov.bd",
        "password": "AnyPassword123!",
        "full_name": "Duplicate User",
        "district": "Dhaka"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()
