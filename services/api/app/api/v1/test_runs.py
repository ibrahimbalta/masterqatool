import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project
from services.api.app.models.test_suite import TestCase
from services.api.app.models.test_run import TestRun, TestResult, TestStep
from services.api.app.models.user import OrganizationMember
from services.api.app.models.subscription import AuditLog
from services.api.app.schemas.test_run import TestRunCreate, TestRunRead
from services.api.app.security.deps import get_current_organization_membership, require_role

router = APIRouter(tags=["Test Runs & Execution"])

@router.post("/test-runs", response_model=TestRunRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_test_run(
    run_in: TestRunCreate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify project
    proj_res = await db.execute(
        select(Project).where(
            Project.id == run_in.project_id,
            Project.organization_id == membership.organization_id
        )
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine test cases to run
    if run_in.test_case_ids:
        cases_res = await db.execute(
            select(TestCase).where(
                TestCase.id.in_(run_in.test_case_ids),
                TestCase.project_id == project.id
            )
        )
    else:
        cases_res = await db.execute(
            select(TestCase).where(TestCase.project_id == project.id)
        )
    test_cases = cases_res.scalars().all()

    test_run = TestRun(
        project_id=project.id,
        organization_id=membership.organization_id,
        trigger=run_in.trigger,
        status="queued",
        total_cases=len(test_cases),
        passed_cases=0,
        failed_cases=0,
        duration_ms=0,
        started_at=datetime.now(timezone.utc)
    )
    db.add(test_run)
    await db.flush()

    # Pre-populate queued results for each test case
    for tc in test_cases:
        res = TestResult(
            test_run_id=test_run.id,
            test_case_id=tc.id,
            status="queued",
            duration_ms=0
        )
        db.add(res)

    audit = AuditLog(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="test_run_queued",
        resource_type="test_run",
        resource_id=str(test_run.id),
        details={"total_cases": len(test_cases), "trigger": run_in.trigger}
    )
    db.add(audit)
    await db.commit()

    # Refresh with preloaded results
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.results).selectinload(TestResult.steps))
        .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
        .where(TestRun.id == test_run.id)
    )
    full_run = (await db.execute(stmt)).scalar_one()
    return full_run

@router.get("/test-runs/{run_id}", response_model=TestRunRead)
async def get_test_run(
    run_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.results).selectinload(TestResult.steps))
        .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
        .where(
            TestRun.id == run_id,
            TestRun.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    test_run = res.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return test_run

@router.post("/test-runs/{run_id}/cancel", response_model=TestRunRead)
async def cancel_test_run(
    run_id: uuid.UUID,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestRun)
        .where(
            TestRun.id == run_id,
            TestRun.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    test_run = res.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if test_run.status in ["passed", "failed", "cancelled", "timed_out"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel run with terminal status '{test_run.status}'")

    test_run.status = "cancelled"
    test_run.completed_at = datetime.now(timezone.utc)
    await db.commit()

    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.results).selectinload(TestResult.steps))
        .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
        .where(TestRun.id == test_run.id)
    )
    return (await db.execute(stmt)).scalar_one()

@router.get("/projects/{project_id}/test-runs", response_model=List[TestRunRead])
async def list_project_test_runs(
    project_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.results).selectinload(TestResult.steps))
        .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
        .where(
            TestRun.project_id == project_id,
            TestRun.organization_id == membership.organization_id
        )
        .order_by(TestRun.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
