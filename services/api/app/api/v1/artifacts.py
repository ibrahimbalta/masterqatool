import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.test_run import Artifact, TestResult, TestRun
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.test_run import ArtifactRead
from services.api.app.security.deps import get_current_organization_membership

router = APIRouter(prefix="/artifacts", tags=["Artifacts & Evidence"])

@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact_metadata(
    artifact_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Artifact)
        .join(TestResult, TestResult.id == Artifact.test_result_id)
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(
            Artifact.id == artifact_id,
            TestRun.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    artifact = res.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact

@router.get("/{artifact_id}/file")
async def download_artifact_file(
    artifact_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Artifact)
        .join(TestResult, TestResult.id == Artifact.test_result_id)
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(
            Artifact.id == artifact_id,
            TestRun.organization_id == membership.organization_id
        )
    )
    res = await db.execute(stmt)
    artifact = res.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if not os.path.exists(artifact.storage_path):
        raise HTTPException(status_code=404, detail="Artifact physical file not found on storage")

    filename = os.path.basename(artifact.storage_path)
    return FileResponse(
        path=artifact.storage_path,
        media_type=artifact.mime_type,
        filename=filename
    )
