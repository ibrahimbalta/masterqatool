import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.core.ssrf import validate_target_url
from services.api.app.db.session import get_db
from services.api.app.models.project import Project
from services.api.app.models.user import OrganizationMember
from services.api.app.models.subscription import AuditLog
from services.api.app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectRead,
    URLValidationRequest, URLValidationResponse
)
from services.api.app.security.deps import get_current_organization_membership, require_role

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/validate-url", response_model=URLValidationResponse)
async def validate_url_endpoint(
    payload: URLValidationRequest,
    membership: OrganizationMember = Depends(get_current_organization_membership)
):
    valid, message = validate_target_url(payload.url)
    return URLValidationResponse(valid=valid, message=message, normalized_url=payload.url if valid else None)

@router.get("", response_model=List[ProjectRead])
async def list_projects(
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(Project.organization_id == membership.organization_id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    # Enforce SSRF validation
    valid, err_msg = validate_target_url(project_in.target_url)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target URL security validation failed: {err_msg}"
        )

    project = Project(
        organization_id=membership.organization_id,
        name=project_in.name,
        description=project_in.description,
        target_url=project_in.target_url,
        github_repo=project_in.github_repo,
        environment=project_in.environment,
        status="active"
    )
    db.add(project)
    await db.flush()

    audit = AuditLog(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project_created",
        resource_type="project",
        resource_id=str(project.id),
        details={"name": project.name, "target_url": project.target_url}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(project)
    return project

@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_in.target_url:
        valid, err_msg = validate_target_url(project_in.target_url)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Target URL security validation failed: {err_msg}")
        project.target_url = project_in.target_url

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.github_repo is not None:
        project.github_repo = project_in.github_repo
    if project_in.environment is not None:
        project.environment = project_in.environment
    if project_in.status is not None:
        project.status = project_in.status

    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    membership: OrganizationMember = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return None
