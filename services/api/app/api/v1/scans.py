import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project, ProjectScan, DiscoveredPage
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.scan import ScanCreate, ScanRead
from services.api.app.security.deps import get_current_organization_membership, require_role

router = APIRouter(prefix="/projects/{project_id}/scans", tags=["Web Discovery & Scans"])

@router.post("", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    project_id: uuid.UUID,
    scan_in: ScanCreate,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify project belongs to current org
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scan = ProjectScan(
        project_id=project.id,
        scan_type=scan_in.scan_type,
        status="pending",
        started_at=datetime.now(timezone.utc),
        summary={"max_pages": scan_in.max_pages, "pages_discovered": 0}
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan

@router.get("", response_model=List[ScanRead])
async def list_scans(
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
        select(ProjectScan)
        .where(ProjectScan.project_id == project_id)
        .order_by(ProjectScan.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ProjectScan)
        .options(selectinload(ProjectScan.discovered_pages))
        .where(ProjectScan.id == scan_id, ProjectScan.project_id == project_id)
    )
    res = await db.execute(stmt)
    scan = res.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
