import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_self_healing_locator_repair_lifecycle(client: AsyncClient):
    # Register user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "healing_tester@example.com",
            "password": "Password123!",
            "full_name": "Heal Architect",
            "organization_name": "Self Healing Corp"
        }
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Healing Demo App",
            "target_url": "https://example.com"
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Create a test case with a broken locator step
    tc_resp = await client.post(
        f"/api/v1/projects/{project_id}/test-cases",
        json={
            "code_identifier": "TC-HEAL-001",
            "title": "Broken Button Click Test",
            "category": "Functional",
            "expected_result": "Button should be clicked",
            "steps": [
                {
                    "step_number": 1,
                    "action_type": "goto",
                    "target_locator": "https://example.com",
                    "expected_result": "Navigate to page"
                },
                {
                    "step_number": 2,
                    "action_type": "click",
                    "target_locator": "button#old-broken-submit-btn",
                    "expected_result": "Submit button clicked"
                }
            ]
        },
        headers=headers
    )
    assert tc_resp.status_code == 201
    test_case_id = tc_resp.json()["id"]

    # Run test synchronously to trigger execution & failure
    run_resp = await client.post(
        "/api/v1/test-runs?sync=true",
        json={
            "project_id": project_id,
            "test_case_ids": [test_case_id]
        },
        headers=headers
    )
    assert run_resp.status_code in [200, 202]
    run_data = run_resp.json()
    assert run_data["status"] == "failed"
    assert len(run_data["results"]) == 1
    result = run_data["results"][0]
    assert result["status"] == "failed"
    result_id = result["id"]

    # Verify locator repairs were generated
    repairs = result.get("locator_repairs", [])
    assert len(repairs) > 0, "Self-healing did not record locator repairs"
    repair = repairs[0]
    assert repair["original_locator"] == "button#old-broken-submit-btn"
    assert repair["status"] == "pending"
    repair_id = repair["id"]

    # Test GET /test-results/{result_id}/locator-repairs endpoint
    get_repairs_resp = await client.get(
        f"/api/v1/test-results/{result_id}/locator-repairs",
        headers=headers
    )
    assert get_repairs_resp.status_code == 200
    fetched_repairs = get_repairs_resp.json()
    assert len(fetched_repairs) >= 1
    assert fetched_repairs[0]["id"] == repair_id

    # Test PATCH /locator-repairs/{repair_id} with "applied"
    patch_resp = await client.patch(
        f"/api/v1/locator-repairs/{repair_id}",
        json={"status": "applied"},
        headers=headers
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["status"] == "applied"

    # Verify test case latest_spec was self-healed
    tc_check = await client.get(
        f"/api/v1/projects/{project_id}/test-cases",
        headers=headers
    )
    assert tc_check.status_code == 200
    cases = tc_check.json()
    target_case = next(c for c in cases if c["id"] == test_case_id)
    assert target_case["current_version"] == 2
    healed_step = target_case["latest_spec"]["steps"][1]
    assert healed_step["target_locator"] == patched_data["suggested_locator"]
