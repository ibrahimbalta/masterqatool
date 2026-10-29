import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project, ProjectConnection, DiscoveredPage, ProjectScan
from services.api.app.models.user import OrganizationMember
from services.api.app.security.deps import get_current_organization_membership, require_role
from services.api.app.integrations.github_client import GitHubIntegrationClient

router = APIRouter(tags=["Integrations"])

class GitHubConnectRequest(BaseModel):
    github_repo: str
    github_token: Optional[str] = None

class ConnectionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    connection_type: str
    status: str
    last_verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/projects/{project_id}/integrations", response_model=List[ConnectionRead])
async def list_project_integrations(
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

    stmt = select(ProjectConnection).where(ProjectConnection.project_id == project_id)
    return (await db.execute(stmt)).scalars().all()

@router.post("/projects/{project_id}/integrations/github")
async def connect_github_repository(
    project_id: uuid.UUID,
    req: GitHubConnectRequest,
    membership: OrganizationMember = Depends(require_role(["owner", "admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == membership.organization_id
        )
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = GitHubIntegrationClient(token=req.github_token)
    repo_analysis = await client.inspect_repository(req.github_repo)

    # Update project
    project.github_repo = req.github_repo

    # Check or create ProjectConnection
    conn_stmt = select(ProjectConnection).where(
        ProjectConnection.project_id == project_id,
        ProjectConnection.connection_type == "github"
    )
    conn = (await db.execute(conn_stmt)).scalar_one_or_none()
    if not conn:
        conn = ProjectConnection(
            project_id=project_id,
            connection_type="github",
            status="connected",
            last_verified_at=datetime.now(timezone.utc)
        )
        db.add(conn)
    else:
        conn.status = "connected"
        conn.last_verified_at = datetime.now(timezone.utc)

    # Register code scan
    scan = ProjectScan(
        project_id=project_id,
        scan_type="github_code",
        status="completed",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        summary=repo_analysis
    )
    db.add(scan)
    await db.flush()

    # Record discovered routes from source code
    base_target = project.target_url.rstrip("/")
    for r in repo_analysis.get("detected_routes", []):
        discovered = DiscoveredPage(
            scan_id=scan.id,
            project_id=project.id,
            url=f"{base_target}{r}",
            path=r,
            title=f"Source Route: {r}",
            forms_detected=[],
            accessibility_tree={},
            provenance="source_code"
        )
        db.add(discovered)

    await db.commit()
    return {
        "status": "connected",
        "repository": req.github_repo,
        "analysis": repo_analysis
    }
