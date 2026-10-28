import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project
from services.api.app.models.bug import Bug
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.bug import BugCreate, BugUpdate, BugRead
from services.api.app.security.deps import get_current_organization_membership, require_role

router = APIRouter(prefix="/bugs", tags=["Bug Intelligence"])

@router.get("", response_model=List[BugRead])
async def list_bugs(
    project_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Bug)
        .join(Project, Project.id == Bug.project_id)
        .where(Project.organization_id == membership.organization_id)
    )
    if project_id:
        stmt = stmt.where(Bug.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Bug.status == status_filter)
    if severity:
        stmt = stmt.where(Bug.severity == severity)
    stmt = stmt.order_by(Bug.created_at.desc())

    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=BugRead, status_code=status.HTTP_201_CREATED)
async def create_bug(
    bug_in: BugCreate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(
        select(Project).where(
            Project.id == bug_in.project_id,
            Project.organization_id == membership.organization_id
        )
    )
    if not proj_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    bug = Bug(
        project_id=bug_in.project_id,
        test_result_id=bug_in.test_result_id,
        title=bug_in.title,
        description=bug_in.description,
        severity=bug_in.severity,
        reproduction_steps=bug_in.reproduction_steps,
        expected_behavior=bug_in.expected_behavior,
        actual_behavior=bug_in.actual_behavior,
        root_cause_hypothesis=bug_in.root_cause_hypothesis,
        status="open"
    )
    db.add(bug)
    await db.commit()
    await db.refresh(bug)
    return bug

@router.patch("/{bug_id}", response_model=BugRead)
async def update_bug(
    bug_id: uuid.UUID,
    bug_in: BugUpdate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Bug)
        .join(Project, Project.id == Bug.project_id)
        .where(
            Bug.id == bug_id,
            Project.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    bug = res.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    if bug_in.title is not None:
        bug.title = bug_in.title
    if bug_in.description is not None:
        bug.description = bug_in.description
    if bug_in.severity is not None:
        bug.severity = bug_in.severity
    if bug_in.status is not None:
        bug.status = bug_in.status
    if bug_in.verified_cause is not None:
        bug.verified_cause = bug_in.verified_cause

    await db.commit()
    await db.refresh(bug)
    return bug
