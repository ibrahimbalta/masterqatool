import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_project_and_test_case_lifecycle(client: AsyncClient):
    # Register & Login
    auth_resp = await client.post("/api/v1/auth/register", json={
        "email": "qa_lead@example.com",
        "password": "Password123!",
        "full_name": "QA Lead",
        "organization_name": "QA Ops Inc"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Project
    proj_resp = await client.post("/api/v1/projects", json={
        "name": "E-Commerce Storefront",
        "target_url": "https://example.com/shop",
        "environment": "staging"
    }, headers=headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Create Test Case
    tc_resp = await client.post(f"/api/v1/projects/{project_id}/test-cases", json={
        "code_identifier": "TC-001",
        "title": "Verify user can add item to shopping cart",
        "objective": "Ensure add to cart button increments cart counter",
        "category": "Functional",
        "priority": "high",
        "risk_level": "medium",
        "automation_status": "candidate",
        "approval_status": "draft",
        "preconditions": ["User is logged in", "Item is in stock"],
        "steps": [
            {
                "step_number": 1,
                "action_type": "goto",
                "target_locator": "/products/123",
                "expected_result": "Product details page loads"
            },
            {
                "step_number": 2,
                "action_type": "click",
                "target_locator": "button#add-to-cart",
                "expected_result": "Cart counter increments to 1"
            }
        ],
        "expected_result": "Item is added to cart successfully"
    }, headers=headers)
    assert tc_resp.status_code == 201
    tc_data = tc_resp.json()
    assert tc_data["code_identifier"] == "TC-001"
    assert tc_data["current_version"] == 1
    test_case_id = tc_data["id"]

    # Update Test Case (Approve and bump version)
    patch_resp = await client.patch(f"/api/v1/test-cases/{test_case_id}", json={
        "approval_status": "approved",
        "expected_result": "Item is added to cart and toast notification appears"
    }, headers=headers)
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["approval_status"] == "approved"
    assert patched_data["current_version"] == 2

    # Export Test Cases as CSV
    export_resp = await client.get(f"/api/v1/projects/{project_id}/test-cases/export", headers=headers)
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    csv_text = export_resp.text
    assert "TC-001" in csv_text
    assert "Verify user can add item to shopping cart" in csv_text
