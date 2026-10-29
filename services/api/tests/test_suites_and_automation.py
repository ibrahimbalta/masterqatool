import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_suites_automation_and_github_integration(client: AsyncClient):
    # Register user
    reg = await client.post("/api/v1/auth/register", json={
        "email": "automation_architect@example.com",
        "password": "Password123!",
        "full_name": "Automation Architect",
        "organization_name": "Automation Studio Corp"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    org_id = reg.json()["organization_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj = await client.post("/api/v1/projects", json={
        "name": "Playwright Target App",
        "target_url": "https://example.com"
    }, headers=headers)
    assert proj.status_code == 201
    project_id = proj.json()["id"]

    # 1. Test Test Suites CRUD
    suite_resp = await client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Critical Smoke Suite",
        "description": "Essential smoke verification flows",
        "category": "smoke"
    }, headers=headers)
    assert suite_resp.status_code == 201
    suite_id = suite_resp.json()["id"]
    assert suite_resp.json()["total_cases"] == 0

    # Create 2 test cases
    tc1 = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-SMK-01",
        "title": "Navigation Smoke Test",
        "category": "Smoke",
        "expected_result": "Page loaded",
        "steps": [{"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "200 OK"}]
    }, headers=headers)
    assert tc1.status_code == 201
    tc1_id = tc1.json()["id"]

    tc2 = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-SMK-02",
        "title": "Login Button Visible",
        "category": "Smoke",
        "expected_result": "Button is visible",
        "steps": [
            {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loaded"},
            {"step_number": 2, "action_type": "assert_visible", "target_locator": "button.login", "expected_result": "Visible"}
        ]
    }, headers=headers)
    assert tc2.status_code == 201
    tc2_id = tc2.json()["id"]

    # Assign cases to suite
    assign_resp = await client.post(f"/api/v1/suites/{suite_id}/cases", json=[tc1_id, tc2_id], headers=headers)
    assert assign_resp.status_code == 200
    assert assign_resp.json()["total_cases"] == 2
    assert len(assign_resp.json()["test_cases"]) == 2

    # 2. Test Automation Lab Playwright Code Generation
    code_resp = await client.get(f"/api/v1/projects/{project_id}/automation/code", headers=headers)
    assert code_resp.status_code == 200
    code_data = code_resp.json()
    assert "@playwright/test" in code_data["code"]
    assert "TC-SMK-01" in code_data["code"]
    assert "TC-SMK-02" in code_data["code"]
    assert code_data["total_test_cases"] >= 2

    # Test Automation package ZIP export
    pkg_resp = await client.get(f"/api/v1/projects/{project_id}/automation/export-package", headers=headers)
    assert pkg_resp.status_code == 200
    assert pkg_resp.headers["content-type"] == "application/zip"
    assert len(pkg_resp.content) > 100

    # 3. Test GitHub Integration
    gh_resp = await client.post(f"/api/v1/projects/{project_id}/integrations/github", json={
        "github_repo": "https://github.com/my-org/my-saas-web"
    }, headers=headers)
    assert gh_resp.status_code == 200
    gh_data = gh_resp.json()
    assert gh_data["status"] == "connected"
    assert "detected_routes" in gh_data["analysis"]
    assert gh_data["analysis"]["provenance"] == "source_code"

    # Verify project integrations list
    conn_list = await client.get(f"/api/v1/projects/{project_id}/integrations", headers=headers)
    assert conn_list.status_code == 200
    assert len(conn_list.json()) >= 1
    assert conn_list.json()[0]["connection_type"] == "github"

    # 4. Test Team member invite/list
    add_mem = await client.post(f"/api/v1/organizations/{org_id}/members", json={
        "email": "teammate@example.com",
        "role": "member"
    }, headers=headers)
    assert add_mem.status_code == 201
    assert add_mem.json()["email"] == "teammate@example.com"
    assert add_mem.json()["role"] == "member"

    members_list = await client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
    assert members_list.status_code == 200
    assert len(members_list.json()) == 2
