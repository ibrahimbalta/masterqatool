import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project
from services.api.app.models.test_suite import TestSuite, TestCase
from services.api.app.models.test_run import TestRun, TestResult
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.test_suite import TestSuiteCreate, TestSuiteUpdate, TestSuiteRead, TestSuiteDetail
from services.api.app.schemas.test_run import TestRunRead
from services.api.app.security.deps import get_current_organization_membership, require_role

router = APIRouter(tags=["Test Suites"])

@router.get("/projects/{project_id}/suites", response_model=List[TestSuiteRead])
async def list_suites(
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

    stmt = (
        select(TestSuite)
        .options(selectinload(TestSuite.test_cases))
        .where(TestSuite.project_id == project_id)
        .order_by(TestSuite.created_at.desc())
    )
    suites = (await db.execute(stmt)).scalars().all()

    result = []
    for s in suites:
        read_obj = TestSuiteRead(
            id=s.id,
            project_id=s.project_id,
            name=s.name,
            description=s.description,
            category=s.category,
            total_cases=len(s.test_cases),
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        result.append(read_obj)
    return result

@router.post("/projects/{project_id}/suites", response_model=TestSuiteRead, status_code=status.HTTP_201_CREATED)
async def create_suite(
    project_id: uuid.UUID,
    suite_in: TestSuiteCreate,
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

    suite = TestSuite(
        project_id=project_id,
        name=suite_in.name,
        description=suite_in.description,
        category=suite_in.category
    )
    db.add(suite)
    await db.commit()
    await db.refresh(suite)

    return TestSuiteRead(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        category=suite.category,
        total_cases=0,
        created_at=suite.created_at,
        updated_at=suite.updated_at
    )

@router.get("/suites/{suite_id}", response_model=TestSuiteDetail)
async def get_suite(
    suite_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestSuite)
        .options(selectinload(TestSuite.test_cases))
        .join(Project, Project.id == TestSuite.project_id)
        .where(
            TestSuite.id == suite_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    suite = res.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    return TestSuiteDetail(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        category=suite.category,
        total_cases=len(suite.test_cases),
        created_at=suite.created_at,
        updated_at=suite.updated_at,
        test_cases=suite.test_cases
    )

@router.patch("/suites/{suite_id}", response_model=TestSuiteRead)
async def update_suite(
    suite_id: uuid.UUID,
    suite_in: TestSuiteUpdate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestSuite)
        .options(selectinload(TestSuite.test_cases))
        .join(Project, Project.id == TestSuite.project_id)
        .where(
            TestSuite.id == suite_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    suite = res.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    if suite_in.name is not None:
        suite.name = suite_in.name
    if suite_in.description is not None:
        suite.description = suite_in.description
    if suite_in.category is not None:
        suite.category = suite_in.category

    await db.commit()
    await db.refresh(suite)

    return TestSuiteRead(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        category=suite.category,
        total_cases=len(suite.test_cases),
        created_at=suite.created_at,
        updated_at=suite.updated_at
    )

@router.delete("/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suite(
    suite_id: uuid.UUID,
    membership: OrganizationMember = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestSuite)
        .join(Project, Project.id == TestSuite.project_id)
        .where(
            TestSuite.id == suite_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    suite = res.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    await db.delete(suite)
    await db.commit()
    return None

@router.post("/suites/{suite_id}/cases", response_model=TestSuiteDetail)
async def assign_cases_to_suite(
    suite_id: uuid.UUID,
    case_ids: List[uuid.UUID],
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(TestSuite)
        .options(selectinload(TestSuite.test_cases))
        .join(Project, Project.id == TestSuite.project_id)
        .where(
            TestSuite.id == suite_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    suite = res.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Fetch matching test cases in this project
    cases_stmt = select(TestCase).where(
        TestCase.id.in_(case_ids),
        TestCase.project_id == suite.project_id
    )
    cases = (await db.execute(cases_stmt)).scalars().all()
    for c in cases:
        c.suite_id = suite.id

    await db.commit()
    await db.refresh(suite)

    # Reload with updated test cases
    reloaded = (await db.execute(
        select(TestSuite).options(selectinload(TestSuite.test_cases)).where(TestSuite.id == suite.id)
    )).scalar_one()

    return TestSuiteDetail(
        id=reloaded.id,
        project_id=reloaded.project_id,
        name=reloaded.name,
        description=reloaded.description,
        category=reloaded.category,
        total_cases=len(reloaded.test_cases),
        created_at=reloaded.created_at,
        updated_at=reloaded.updated_at,
        test_cases=reloaded.test_cases
    )
