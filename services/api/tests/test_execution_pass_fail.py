import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_execution_pass_and_deliberate_fail(client: AsyncClient):
    auth_resp = await client.post("/api/v1/auth/register", json={
        "email": "runner_lead@example.com",
        "password": "Password123!",
        "full_name": "Automation Lead",
        "organization_name": "Execution Org"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Project
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "E-Shop Target",
        "target_url": "https://example.com",
        "environment": "staging"
    }, headers=headers)
    project_id = proj_resp.json()["id"]

    # 1. Intentionally PASSING scenario (generic steps that succeed)
    pass_case = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-PASS-01",
        "title": "Verify home page generic navigation",
        "category": "Smoke",
        "priority": "high",
        "steps": [
            {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loads"}
        ],
        "expected_result": "Page displays successfully"
    }, headers=headers)
    pass_case_id = pass_case.json()["id"]

    # Run PASSING scenario
    run_pass = await client.post("/api/v1/test-runs?sync=true", json={
        "project_id": project_id,
        "test_case_ids": [pass_case_id]
    }, headers=headers)
    assert run_pass.status_code == 202
    run_pass_data = run_pass.json()
    assert run_pass_data["status"] == "passed"
    assert run_pass_data["passed_cases"] == 1
    assert run_pass_data["failed_cases"] == 0

    # 2. Intentionally FAILING scenario (SSRF violation or failed assertion)
    fail_case = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-FAIL-01",
        "title": "Verify non-existent element raises assertion error",
        "category": "Negative",
        "priority": "critical",
        "steps": [
            {
                "step_number": 1,
                "action_type": "goto",
                "target_locator": "http://127.0.0.1:9999/forbidden-internal",
                "expected_result": "Should be blocked by SSRF filter"
            }
        ],
        "expected_result": "Step assertion fails safely"
    }, headers=headers)
    fail_case_id = fail_case.json()["id"]

    # Run FAILING scenario
    run_fail = await client.post("/api/v1/test-runs?sync=true", json={
        "project_id": project_id,
        "test_case_ids": [fail_case_id]
    }, headers=headers)
    assert run_fail.status_code == 202
    run_fail_data = run_fail.json()
    assert run_fail_data["status"] == "failed"
    assert run_fail_data["failed_cases"] == 1

    first_res = run_fail_data["results"][0]
    assert first_res["status"] == "failed"
    assert "SSRF security violation" in first_res["error_message"]
    # Verify screenshot artifact was saved
    assert len(first_res["artifacts"]) > 0
    assert first_res["artifacts"][0]["artifact_type"] == "screenshot"

    # Verify Bug dossier was automatically created in Bug Intelligence
    bugs_resp = await client.get(f"/api/v1/bugs?project_id={project_id}", headers=headers)
    assert bugs_resp.status_code == 200
    bugs = bugs_resp.json()
    assert len(bugs) == 1
    assert "TC-FAIL-01" in bugs[0]["title"]
    assert bugs[0]["severity"] == "high"
