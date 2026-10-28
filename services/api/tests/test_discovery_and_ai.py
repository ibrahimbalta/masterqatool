import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ai_test_case_generation(client: AsyncClient):
    auth_resp = await client.post("/api/v1/auth/register", json={
        "email": "ai_architect@example.com",
        "password": "Password123!",
        "full_name": "AI Architect",
        "organization_name": "AI QA Labs"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Project
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "Portal Intelligence Test",
        "target_url": "https://example.com",
        "environment": "staging"
    }, headers=headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Trigger AI generation
    gen_resp = await client.post(f"/api/v1/projects/{project_id}/test-cases/generate", headers=headers)
    assert gen_resp.status_code == 201
    cases = gen_resp.json()
    assert len(cases) > 0

    first_case = cases[0]
    assert first_case["provenance"] == "ai_inferred"
    assert "TC-" in first_case["code_identifier"]
    assert len(first_case["latest_spec"]["steps"]) > 0

    # Verify usage record recorded AI tokens
    usage_resp = await client.get("/api/v1/usage", headers=headers)
    assert usage_resp.status_code == 200
    assert usage_resp.json()["ai_tokens_used"] > 0
