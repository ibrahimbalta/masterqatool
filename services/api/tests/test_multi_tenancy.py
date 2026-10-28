import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_data_isolation(client: AsyncClient):
    # 1. Register User A in Org A
    user_a_resp = await client.post("/api/v1/auth/register", json={
        "email": "org_a_user@example.com",
        "password": "Password123!",
        "full_name": "User Alpha",
        "organization_name": "Organization Alpha"
    })
    assert user_a_resp.status_code == 201
    token_a = user_a_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. User A creates a Project
    proj_a_resp = await client.post("/api/v1/projects", json={
        "name": "Alpha Portal",
        "description": "Sensitive Alpha Project",
        "target_url": "https://example.com/alpha",
        "environment": "staging"
    }, headers=headers_a)
    assert proj_a_resp.status_code == 201
    project_a_id = proj_a_resp.json()["id"]

    # 3. Register User B in Org B
    user_b_resp = await client.post("/api/v1/auth/register", json={
        "email": "org_b_user@example.com",
        "password": "Password123!",
        "full_name": "User Beta",
        "organization_name": "Organization Beta"
    })
    assert user_b_resp.status_code == 201
    token_b = user_b_resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. User B attempts to access Org A's Project -> MUST BE 404
    cross_get_resp = await client.get(f"/api/v1/projects/{project_a_id}", headers=headers_b)
    assert cross_get_resp.status_code == 404
    assert "not found" in cross_get_resp.json()["detail"].lower()

    # 5. User B attempts to mutate Org A's Project -> MUST BE 404
    cross_patch_resp = await client.patch(f"/api/v1/projects/{project_a_id}", json={
        "name": "Hacked Project"
    }, headers=headers_b)
    assert cross_patch_resp.status_code == 404

    # 6. User B lists projects -> MUST NOT include Org A's project
    b_projects_resp = await client.get("/api/v1/projects", headers=headers_b)
    assert b_projects_resp.status_code == 200
    b_projects = b_projects_resp.json()
    assert len(b_projects) == 0
