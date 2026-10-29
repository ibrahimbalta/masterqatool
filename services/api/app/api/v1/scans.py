import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db, AsyncSessionLocal
from services.api.app.models.project import Project, ProjectScan, DiscoveredPage
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.scan import ScanCreate, ScanRead
from services.api.app.security.deps import get_current_organization_membership, require_role
from services.api.app.services.discovery import WebDiscoveryService

router = APIRouter(prefix="/projects/{project_id}/scans", tags=["Web Discovery & Scans"])

async def run_discovery_task(scan_id: uuid.UUID, allow_private_dev: bool = False):
    async with AsyncSessionLocal() as session:
        service = WebDiscoveryService(session)
        await service.run_discovery(scan_id, allow_private_dev=allow_private_dev)

@router.post("", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    project_id: uuid.UUID,
    scan_in: ScanCreate,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Run synchronously for immediate testing results"),
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

    if sync:
        service = WebDiscoveryService(db)
        await service.run_discovery(scan.id)
    else:
        background_tasks.add_task(run_discovery_task, scan.id)

    stmt = (
        select(ProjectScan)
        .options(selectinload(ProjectScan.discovered_pages))
        .where(ProjectScan.id == scan.id)
    )
    return (await db.execute(stmt)).scalar_one()

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
        .options(selectinload(ProjectScan.discovered_pages))
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
