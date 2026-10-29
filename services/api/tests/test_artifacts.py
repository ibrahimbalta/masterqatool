import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_artifacts_endpoints_and_isolation(client: AsyncClient):
    # Register org 1
    reg1 = await client.post("/api/v1/auth/register", json={
        "email": "artifact_tester@example.com",
        "password": "Password123!",
        "full_name": "Artifact Tester",
        "organization_name": "Artifacts Corp"
    })
    token1 = reg1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Create project & deliberately failing test to generate an artifact
    proj1 = await client.post("/api/v1/projects", json={
        "name": "Artifact Project",
        "target_url": "https://example.com"
    }, headers=headers1)
    project_id = proj1.json()["id"]

    tc = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-ART-01",
        "title": "Trigger screenshot failure",
        "category": "Negative",
        "expected_result": "Fails deliberately",
        "steps": [
            {"step_number": 1, "action_type": "goto", "target_locator": "http://127.0.0.1:8888/ssrf-block", "expected_result": "Blocked"}
        ]
    }, headers=headers1)
    tc_id = tc.json()["id"]

    # Run test synchronously
    run = await client.post("/api/v1/test-runs?sync=true", json={
        "project_id": project_id,
        "test_case_ids": [tc_id]
    }, headers=headers1)
    run_data = run.json()
    assert run_data["status"] == "failed"
    artifacts = run_data["results"][0]["artifacts"]
    assert len(artifacts) >= 1
    artifact_id = artifacts[0]["id"]

    # 1. Test GET /api/v1/artifacts/{artifact_id}
    meta_resp = await client.get(f"/api/v1/artifacts/{artifact_id}", headers=headers1)
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["id"] == artifact_id
    assert meta_data["artifact_type"] == "screenshot"

    # 2. Test GET /api/v1/artifacts/{artifact_id}/file
    file_resp = await client.get(f"/api/v1/artifacts/{artifact_id}/file", headers=headers1)
    assert file_resp.status_code == 200
    assert file_resp.headers["content-type"] == "image/png"
    assert len(file_resp.content) > 0

    # 3. Test Multi-tenant isolation: another org cannot access this artifact
    reg2 = await client.post("/api/v1/auth/register", json={
        "email": "unauthorized_org@example.com",
        "password": "Password123!",
        "full_name": "Spy User",
        "organization_name": "Spy Corp"
    })
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    forbidden_resp = await client.get(f"/api/v1/artifacts/{artifact_id}", headers=headers2)
    assert forbidden_resp.status_code == 404

    forbidden_file = await client.get(f"/api/v1/artifacts/{artifact_id}/file", headers=headers2)
    assert forbidden_file.status_code == 404
