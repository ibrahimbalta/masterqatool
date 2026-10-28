import uuid
import csv
import io
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project, ProjectScan, DiscoveredPage
from services.api.app.models.test_suite import TestCase, TestCaseVersion
from services.api.app.models.subscription import UsageRecord, AuditLog
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseRead
from services.api.app.security.deps import get_current_organization_membership, require_role
from services.api.app.integrations.ai_adapter import get_ai_provider

router = APIRouter(tags=["Test Cases"])

@router.get("/projects/{project_id}/test-cases", response_model=List[TestCaseRead])
async def list_test_cases(
    project_id: uuid.UUID,
    category: Optional[str] = None,
    approval_status: Optional[str] = None,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(TestCase).where(TestCase.project_id == project_id)
    if category:
        stmt = stmt.where(TestCase.category == category)
    if approval_status:
        stmt = stmt.where(TestCase.approval_status == approval_status)
    stmt = stmt.order_by(TestCase.code_identifier.asc())

    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/projects/{project_id}/test-cases", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    project_id: uuid.UUID,
    tc_in: TestCaseCreate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    dup_res = await db.execute(
        select(TestCase).where(
            TestCase.project_id == project_id,
            TestCase.code_identifier == tc_in.code_identifier
        )
    )
    if dup_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Test case with identifier '{tc_in.code_identifier}' already exists in this project.")

    latest_spec = {
        "preconditions": tc_in.preconditions,
        "test_data": tc_in.test_data,
        "steps": tc_in.steps,
        "expected_result": tc_in.expected_result,
    }

    test_case = TestCase(
        project_id=project_id,
        code_identifier=tc_in.code_identifier,
        title=tc_in.title,
        objective=tc_in.objective,
        category=tc_in.category,
        priority=tc_in.priority,
        risk_level=tc_in.risk_level,
        automation_status=tc_in.automation_status,
        approval_status=tc_in.approval_status,
        current_version=1,
        provenance="manual",
        latest_spec=latest_spec
    )
    db.add(test_case)
    await db.flush()

    version = TestCaseVersion(
        test_case_id=test_case.id,
        version_number=1,
        spec_snapshot=latest_spec,
        change_summary="Initial creation",
        changed_by_user_id=membership.user_id
    )
    db.add(version)

    await db.commit()
    await db.refresh(test_case)
    return test_case

@router.post("/projects/{project_id}/test-cases/generate", response_model=List[TestCaseRead], status_code=status.HTTP_201_CREATED)
async def generate_test_cases_with_ai(
    project_id: uuid.UUID,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify project
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch discovered pages for this project
    pages_res = await db.execute(
        select(DiscoveredPage).where(DiscoveredPage.project_id == project.id).order_by(DiscoveredPage.created_at.desc())
    )
    pages = pages_res.scalars().all()
    pages_data = [
        {
            "url": p.url,
            "path": p.path,
            "title": p.title,
            "forms": p.forms_detected,
            "accessibility": p.accessibility_tree
        }
        for p in pages
    ]

    # Generate structured test cases via AI adapter
    ai_provider = get_ai_provider()
    specs = await ai_provider.generate_test_cases(
        project_name=project.name,
        target_url=project.target_url,
        discovered_pages=pages_data
    )

    created_cases: List[TestCase] = []
    # Avoid duplicate identifiers
    existing_codes = set((await db.execute(
        select(TestCase.code_identifier).where(TestCase.project_id == project.id)
    )).scalars().all())

    for idx, spec in enumerate(specs):
        code_id = spec.code_identifier
        suffix = 1
        while code_id in existing_codes:
            code_id = f"{spec.code_identifier}-{suffix}"
            suffix += 1
        existing_codes.add(code_id)

        spec_dict = {
            "preconditions": spec.preconditions,
            "test_data": spec.test_data,
            "steps": [s.model_dump() for s in spec.steps],
            "expected_result": spec.expected_result,
        }

        tc = TestCase(
            project_id=project.id,
            code_identifier=code_id,
            title=spec.title,
            objective=spec.objective,
            category=spec.category.value,
            priority=spec.priority.value,
            risk_level=spec.risk_level.value,
            automation_status=spec.automation_status.value,
            approval_status="draft",
            current_version=1,
            ai_confidence_score=spec.ai_confidence_score,
            provenance="ai_inferred",
            latest_spec=spec_dict
        )
        db.add(tc)
        await db.flush()

        ver = TestCaseVersion(
            test_case_id=tc.id,
            version_number=1,
            spec_snapshot=spec_dict,
            change_summary="Generated by AI Test Designer",
            changed_by_user_id=membership.user_id
        )
        db.add(ver)
        created_cases.append(tc)

    # Record token usage (estimate 150 tokens per generated scenario)
    usage = UsageRecord(
        organization_id=membership.organization_id,
        metric_type="ai_tokens",
        quantity=float(len(created_cases) * 150),
        recorded_at=datetime.now(timezone.utc),
        reference_id=str(project.id)
    )
    db.add(usage)

    audit = AuditLog(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="ai_test_cases_generated",
        resource_type="project",
        resource_id=str(project.id),
        details={"scenarios_count": len(created_cases)}
    )
    db.add(audit)

    await db.commit()
    for tc in created_cases:
        await db.refresh(tc)

    return created_cases

@router.patch("/test-cases/{test_case_id}", response_model=TestCaseRead)
async def update_test_case(
    test_case_id: uuid.UUID,
    tc_in: TestCaseUpdate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestCase)
        .join(Project, Project.id == TestCase.project_id)
        .where(
            TestCase.id == test_case_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    test_case = res.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    spec_changed = False
    new_spec = dict(test_case.latest_spec)

    if tc_in.title is not None:
        test_case.title = tc_in.title
    if tc_in.objective is not None:
        test_case.objective = tc_in.objective
    if tc_in.category is not None:
        test_case.category = tc_in.category
    if tc_in.priority is not None:
        test_case.priority = tc_in.priority
    if tc_in.risk_level is not None:
        test_case.risk_level = tc_in.risk_level
    if tc_in.automation_status is not None:
        test_case.automation_status = tc_in.automation_status
    if tc_in.approval_status is not None:
        test_case.approval_status = tc_in.approval_status

    if tc_in.preconditions is not None:
        new_spec["preconditions"] = tc_in.preconditions
        spec_changed = True
    if tc_in.test_data is not None:
        new_spec["test_data"] = tc_in.test_data
        spec_changed = True
    if tc_in.steps is not None:
        new_spec["steps"] = tc_in.steps
        spec_changed = True
    if tc_in.expected_result is not None:
        new_spec["expected_result"] = tc_in.expected_result
        spec_changed = True

    if spec_changed:
        test_case.latest_spec = new_spec
        test_case.current_version += 1
        new_version = TestCaseVersion(
            test_case_id=test_case.id,
            version_number=test_case.current_version,
            spec_snapshot=new_spec,
            change_summary="Updated via Test Case Studio",
            changed_by_user_id=membership.user_id
        )
        db.add(new_version)

    await db.commit()
    await db.refresh(test_case)
    return test_case

@router.get("/projects/{project_id}/test-cases/export")
async def export_test_cases_csv(
    project_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.code_identifier.asc())
    cases = (await db.execute(stmt)).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Category", "Priority", "Risk", "Automation Status", "Approval Status", "Steps Count", "Expected Result"])

    for c in cases:
        steps_count = len(c.latest_spec.get("steps", []))
        expected = c.latest_spec.get("expected_result", "")
        writer.writerow([
            c.code_identifier,
            c.title,
            c.category,
            c.priority,
            c.risk_level,
            c.automation_status,
            c.approval_status,
            steps_count,
            expected
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}-test-cases.csv"}
    )
