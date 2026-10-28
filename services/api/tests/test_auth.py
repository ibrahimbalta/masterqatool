import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    # Register User
    reg_payload = {
        "email": "tester@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test Engineer",
        "organization_name": "Acme QA Corp"
    }
    response = await client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "owner"
    assert data["organization_id"] is not None

    token = data["access_token"]

    # Verify /me endpoint
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "tester@example.com"
    assert me_data["full_name"] == "Test Engineer"

    # Login with form data
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "tester@example.com", "password": "StrongPassword123!"}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient):
    reg_payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!"
    }
    resp1 = await client.post("/api/v1/auth/register", json=reg_payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=reg_payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]
