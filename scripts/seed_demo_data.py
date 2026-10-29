"""
Seed realistic demo data into the AI QA Agent database for immediate dashboard exploration.
Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add repository root to python search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure database path
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./qa_agent.db"

from services.api.app.db.session import engine, Base, AsyncSessionLocal
from services.api.app.core.security import get_password_hash
from services.api.app.models.user import User, Organization, OrganizationMember
from services.api.app.models.project import Project, ProjectConnection, ProjectScan, DiscoveredPage
from services.api.app.models.test_suite import TestSuite, TestCase, TestCaseVersion
from services.api.app.models.test_run import TestRun, TestResult, TestStep, Artifact, LocatorRepair
from services.api.app.models.bug import Bug
from services.api.app.models.subscription import Subscription, UsageRecord, AuditLog

async def seed():
    print("Connecting to database and initializing schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Create or get demo user
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.email == "architect@acme-qa.com"))
        user = res.scalar_one_or_none()

        if not user:
            print("Creating demo user: architect@acme-qa.com ...")
            user = User(
                email="architect@acme-qa.com",
                hashed_password=get_password_hash("SecurePass123!"),
                full_name="Alex Mercer (Lead Architect)",
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.flush()

            org = Organization(
                name="Acme Enterprise QA",
                slug="acme-enterprise-qa",
                plan_tier="pro"
            )
            session.add(org)
            await session.flush()

            membership = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role="owner"
            )
            session.add(membership)

            # Subscription
            sub = Subscription(
                organization_id=org.id,
                plan_tier="pro",
                status="active",
                max_projects=20,
                max_test_minutes_monthly=1000,
                max_ai_tokens_monthly=500000,
                max_concurrent_runs=5
            )
            session.add(sub)
        else:
            print("User architect@acme-qa.com already exists, finding organization...")
            mem_res = await session.execute(select(OrganizationMember).where(OrganizationMember.user_id == user.id))
            membership = mem_res.scalars().first()
            org_res = await session.execute(select(Organization).where(Organization.id == membership.organization_id))
            org = org_res.scalar_one()

        # 2. Create Project
        proj_res = await session.execute(
            select(Project).where(Project.organization_id == org.id, Project.name == "Acme SaaS Cloud Portal")
        )
        project = proj_res.scalar_one_or_none()

        if not project:
            print("Creating Demo Project: Acme SaaS Cloud Portal ...")
            project = Project(
                organization_id=org.id,
                name="Acme SaaS Cloud Portal",
                description="Enterprise customer portal with authentication, billing, and project management.",
                target_url="https://example.com",
                github_repo="https://github.com/acme/cloud-portal",
                environment="staging",
                status="active"
            )
            session.add(project)
            await session.flush()

            # Connection
            conn = ProjectConnection(
                project_id=project.id,
                connection_type="github",
                status="connected",
                last_verified_at=datetime.now(timezone.utc)
            )
            session.add(conn)

            # 3. Create Discovered Pages
            scan = ProjectScan(
                project_id=project.id,
                scan_type="url_crawler",
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                summary={"pages_discovered": 3, "forms_detected": 2}
            )
            session.add(scan)
            await session.flush()

            page1 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/",
                path="/",
                http_status=200,
                title="Acme Cloud Portal — Home",
                forms_detected=[],
                accessibility_tree={"role": "document", "name": "Acme Portal"},
                provenance="observed"
            )
            page2 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/login",
                path="/login",
                http_status=200,
                title="Customer Sign In",
                forms_detected=[
                    {
                        "action": "/api/v1/auth/login",
                        "method": "POST",
                        "inputs": [
                            {"name": "email", "type": "email", "required": True},
                            {"name": "password", "type": "password", "required": True}
                        ],
                        "buttons": [{"text": "Sign In", "type": "submit"}]
                    }
                ],
                accessibility_tree={"role": "form", "name": "Login Form"},
                provenance="observed"
            )
            page3 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/dashboard",
                path="/dashboard",
                http_status=200,
                title="User Workspace Dashboard",
                forms_detected=[],
                accessibility_tree={"role": "main", "name": "Dashboard"},
                provenance="source_code"
            )
            session.add_all([page1, page2, page3])

            # 4. Create Test Suite
            suite = TestSuite(
                project_id=project.id,
                name="Daily Core Smoke Suite",
                description="Fast-feedback sanity tests run on every pull request and staging deployment.",
                category="smoke"
            )
            session.add(suite)
            await session.flush()

            # 5. Create Test Cases
            tc1 = TestCase(
                project_id=project.id,
                suite_id=suite.id,
                code_identifier="TC-AUTH-001",
                title="Verify login screen loads and elements are visible",
                objective="Ensure login inputs and submit buttons render properly.",
                category="Smoke",
                priority="high",
                risk_level="medium",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.96,
                provenance="ai_inferred",
                latest_spec={
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loads"},
                        {"step_number": 2, "action_type": "assert_visible", "target_locator": "h1", "expected_result": "Heading is visible"}
                    ],
                    "expected_result": "Login form elements are interactive"
                }
            )

            tc2 = TestCase(
                project_id=project.id,
                suite_id=suite.id,
                code_identifier="TC-AUTH-002",
                title="Verify submission with invalid credentials displays error banner",
                objective="Confirm validation message appears when authentication fails.",
                category="Negative",
                priority="critical",
                risk_level="high",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.91,
                provenance="ai_inferred",
                latest_spec={
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loads"},
                        {"step_number": 2, "action_type": "click", "target_locator": "button#btn-broken-action", "expected_result": "Click button"}
                    ],
                    "expected_result": "System raises error banner"
                }
            )

            session.add_all([tc1, tc2])
            await session.flush()

            # 6. Create Test Run with real PASS and FAIL results & Artifact
            test_run = TestRun(
                project_id=project.id,
                organization_id=org.id,
                trigger="manual",
                status="failed",
                total_cases=2,
                passed_cases=1,
                failed_cases=1,
                duration_ms=4850,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            session.add(test_run)
            await session.flush()

            # Result 1: PASS
            res1 = TestResult(
                test_run_id=test_run.id,
                test_case_id=tc1.id,
                status="passed",
                duration_ms=2100
            )
            session.add(res1)
            await session.flush()

            step1 = TestStep(
                test_result_id=res1.id,
                step_number=1,
                action_type="goto",
                target_locator="https://example.com",
                status="passed",
                expected_result="Page loads",
                actual_result="Navigated to https://example.com",
                duration_ms=1200
            )
            step2 = TestStep(
                test_result_id=res1.id,
                step_number=2,
                action_type="assert_visible",
                target_locator="h1",
                status="passed",
                expected_result="Heading is visible",
                actual_result="Element is visible as expected",
                duration_ms=900
            )
            session.add_all([step1, step2])

            # Result 2: FAIL
            res2 = TestResult(
                test_run_id=test_run.id,
                test_case_id=tc2.id,
                status="failed",
                duration_ms=2750,
                error_message="Element with locator 'button#btn-broken-action' could not be resolved or clicked."
            )
            session.add(res2)
            await session.flush()

            fail_step1 = TestStep(
                test_result_id=res2.id,
                step_number=1,
                action_type="goto",
                target_locator="https://example.com",
                status="passed",
                expected_result="Page loads",
                actual_result="Navigated to https://example.com",
                duration_ms=1300
            )
            fail_step2 = TestStep(
                test_result_id=res2.id,
                step_number=2,
                action_type="click",
                target_locator="button#btn-broken-action",
                status="failed",
                expected_result="Click button",
                actual_result="Execution failed: Element not found",
                error_message="Element with locator 'button#btn-broken-action' could not be resolved or clicked.",
                duration_ms=1450
            )
            session.add_all([fail_step1, fail_step2])

            # Artifact (Screenshot)
            os.makedirs("./artifacts_storage", exist_ok=True)
            screenshot_path = f"./artifacts_storage/screenshot_demo_{res2.id}_2.png"
            with open(screenshot_path, "wb") as f:
                f.write(b"DEMO_SCREENSHOT_BINARY_DATA_EVIDENCE_PNG")

            artifact = Artifact(
                test_result_id=res2.id,
                artifact_type="screenshot",
                storage_path=screenshot_path,
                mime_type="image/png",
                file_size_bytes=len(b"DEMO_SCREENSHOT_BINARY_DATA_EVIDENCE_PNG")
            )
            session.add(artifact)

            # Self-healing locator repair candidate
            repair = LocatorRepair(
                test_result_id=res2.id,
                test_case_id=tc2.id,
                step_number=2,
                original_locator="button#btn-broken-action",
                suggested_locator="getByRole('button', name='Sign In')",
                strategy="getByRole",
                confidence_score=0.94,
                dom_snippet="<button type='submit' class='btn-primary'>Sign In</button>",
                status="pending"
            )
            session.add(repair)

            # 7. Bug Dossier
            bug = Bug(
                project_id=project.id,
                test_result_id=res2.id,
                title="Failure in TC-AUTH-002: Verify submission with invalid credentials",
                description="Step #2 failed during automated Playwright execution. Button selector could not be located in current DOM.",
                severity="critical",
                reproduction_steps=[
                    "1. Navigate to target URL https://example.com",
                    "2. Attempt to resolve locator button#btn-broken-action",
                    "3. Browser raises timeout: element not found"
                ],
                expected_behavior="Button should be clicked and error banner displayed",
                actual_behavior="Element with locator 'button#btn-broken-action' could not be resolved or clicked",
                root_cause_hypothesis="Button element selector updated in latest frontend build. Use getByRole('button', name='Sign In').",
                status="open"
            )
            session.add(bug)

            # 8. Usage Records
            usage1 = UsageRecord(
                organization_id=org.id,
                metric_type="test_minutes",
                quantity=0.08,
                recorded_at=datetime.now(timezone.utc),
                reference_id=str(test_run.id)
            )
            usage2 = UsageRecord(
                organization_id=org.id,
                metric_type="ai_tokens",
                quantity=320,
                recorded_at=datetime.now(timezone.utc),
                reference_id=str(project.id)
            )
            session.add_all([usage1, usage2])

            await session.commit()
            print("Demo data seeded successfully!")
            print(f"Project ID: {project.id}")
            print(f"User: architect@acme-qa.com / SecurePass123!")
            print("Now launch the web app with 'npm run dev' to explore!")

if __name__ == "__main__":
    asyncio.run(seed())
