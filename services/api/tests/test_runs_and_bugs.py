import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_test_run_execution_and_bug_tracking(client: AsyncClient):
    auth_resp = await client.post("/api/v1/auth/register", json={
        "email": "runner@example.com",
        "password": "Password123!",
        "full_name": "Test Runner",
        "organization_name": "Runner Corp"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Project & Test Case
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "Checkout Flow",
        "target_url": "https://example.com/checkout",
        "environment": "staging"
    }, headers=headers)
    project_id = proj_resp.json()["id"]

    tc_resp = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-CHK-01",
        "title": "Validate postal code validation",
        "category": "Validation",
        "expected_result": "Invalid postal code produces error badge"
    }, headers=headers)
    test_case_id = tc_resp.json()["id"]

    # Queue Test Run (must return 202 Accepted)
    run_resp = await client.post("/api/v1/test-runs", json={
        "project_id": project_id,
        "trigger": "manual"
    }, headers=headers)
    assert run_resp.status_code == 202
    run_data = run_resp.json()
    assert run_data["status"] == "queued"
    assert run_data["total_cases"] == 1
    run_id = run_data["id"]

    # Get Test Run status
    get_run = await client.get(f"/api/v1/test-runs/{run_id}", headers=headers)
    assert get_run.status_code == 200
    assert len(get_run.json()["results"]) == 1

    # Cancel Test Run
    cancel_resp = await client.post(f"/api/v1/test-runs/{run_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Create Bug connected to project
    bug_resp = await client.post("/api/v1/bugs", json={
        "project_id": project_id,
        "title": "Postal code input accepts invalid characters",
        "severity": "high",
        "expected_behavior": "Should highlight input in red",
        "actual_behavior": "Allows submission with invalid chars"
    }, headers=headers)
    assert bug_resp.status_code == 201
    bug_id = bug_resp.json()["id"]

    # List bugs
    bugs_list = await client.get("/api/v1/bugs", headers=headers)
    assert bugs_list.status_code == 200
    assert len(bugs_list.json()) == 1

    # Get Usage summary
    usage_resp = await client.get("/api/v1/usage", headers=headers)
    assert usage_resp.status_code == 200
    usage_data = usage_resp.json()
    assert usage_data["projects_count"] == 1
    assert usage_data["plan_tier"] == "free"
