import uuid
import copy
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db, AsyncSessionLocal
from services.api.app.models.project import Project
from services.api.app.models.test_suite import TestCase, TestCaseVersion
from services.api.app.models.test_run import TestRun, TestResult, TestStep, LocatorRepair
from services.api.app.models.user import OrganizationMember
from services.api.app.models.subscription import AuditLog, Subscription, UsageRecord
from services.api.app.schemas.test_run import TestRunCreate, TestRunRead, LocatorRepairRead, LocatorRepairUpdate
from services.api.app.security.deps import get_current_organization_membership, require_role
from services.worker.app.browser.runner import PlaywrightRunner

router = APIRouter(tags=["Test Runs & Execution"])

async def run_browser_task(run_id: uuid.UUID, allow_private_dev: bool = False):
    async with AsyncSessionLocal() as session:
        runner = PlaywrightRunner(session)
        await runner.execute_test_run(run_id, allow_private_dev=allow_private_dev)

@router.post("/test-runs", response_model=TestRunRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_test_run(
    run_in: TestRunCreate,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Run synchronously for immediate verification"),
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

    # Check monthly test minutes quota
    sub_res = await db.execute(
        select(Subscription).where(
            Subscription.organization_id == membership.organization_id,
            Subscription.status == "active"
        )
    )
    sub = sub_res.scalars().first()
    test_minutes_limit = sub.max_test_minutes_monthly if sub else 60

    min_res = await db.execute(
        select(func.sum(UsageRecord.quantity)).where(
            UsageRecord.organization_id == membership.organization_id,
            UsageRecord.metric_type == "test_minutes"
        )
    )
    test_minutes_used = float(min_res.scalar() or 0.0)

    if test_minutes_used >= test_minutes_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Monthly test minutes quota reached ({test_minutes_used:.1f}/{test_minutes_limit} min). Please upgrade plan tier."
        )

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

    if sync:
        runner = PlaywrightRunner(db)
        await runner.execute_test_run(test_run.id)
        stmt = (
            select(TestRun)
            .options(selectinload(TestRun.results).selectinload(TestResult.steps))
            .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
            .options(selectinload(TestRun.results).selectinload(TestResult.locator_repairs))
            .where(TestRun.id == test_run.id)
        )
        return (await db.execute(stmt)).scalar_one()
    else:
        background_tasks.add_task(run_browser_task, test_run.id)

    # Return queued representation
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.results).selectinload(TestResult.steps))
        .options(selectinload(TestRun.results).selectinload(TestResult.artifacts))
        .options(selectinload(TestRun.results).selectinload(TestResult.locator_repairs))
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
        .options(selectinload(TestRun.results).selectinload(TestResult.locator_repairs))
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
        .options(selectinload(TestRun.results).selectinload(TestResult.locator_repairs))
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
        .options(selectinload(TestRun.results).selectinload(TestResult.locator_repairs))
        .where(
            TestRun.project_id == project_id,
            TestRun.organization_id == membership.organization_id
        )
        .order_by(TestRun.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/test-results/{result_id}/locator-repairs", response_model=List[LocatorRepairRead])
async def list_locator_repairs_for_result(
    result_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LocatorRepair)
        .join(TestResult, TestResult.id == LocatorRepair.test_result_id)
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(
            LocatorRepair.test_result_id == result_id,
            TestRun.organization_id == membership.organization_id
        )
        .order_by(LocatorRepair.confidence_score.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/locator-repairs/{repair_id}", response_model=LocatorRepairRead)
async def update_locator_repair(
    repair_id: uuid.UUID,
    repair_in: LocatorRepairUpdate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LocatorRepair)
        .join(TestResult, TestResult.id == LocatorRepair.test_result_id)
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(
            LocatorRepair.id == repair_id,
            TestRun.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    repair = res.scalar_one_or_none()
    if not repair:
        raise HTTPException(status_code=404, detail="Locator repair not found")

    repair.status = repair_in.status

    # If status is applied, propagate repair into TestCase latest_spec steps
    if repair_in.status == "applied":
        tc_res = await db.execute(select(TestCase).where(TestCase.id == repair.test_case_id))
        test_case = tc_res.scalar_one_or_none()
        if test_case and test_case.latest_spec:
            new_spec = copy.deepcopy(test_case.latest_spec)
            steps = new_spec.get("steps", [])
            updated = False
            for step in steps:
                if step.get("step_number") == repair.step_number or step.get("target_locator") == repair.original_locator:
                    step["target_locator"] = repair.suggested_locator
                    updated = True
            if updated:
                test_case.latest_spec = new_spec
                flag_modified(test_case, "latest_spec")
                test_case.current_version += 1
                version = TestCaseVersion(
                    test_case_id=test_case.id,
                    version_number=test_case.current_version,
                    spec_snapshot=new_spec,
                    change_summary=f"Self-healed step {repair.step_number} locator to {repair.suggested_locator}",
                    changed_by_user_id=membership.user_id
                )
                db.add(version)

    await db.commit()
    await db.refresh(repair)
    return repair
