import uuid
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.user import User, Organization, OrganizationMember
from services.api.app.schemas.organization import OrgCreate, OrgRead, OrgMemberAdd, OrgMemberRead
from services.api.app.security.deps import get_current_user, get_current_organization_membership, require_role

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("", response_model=List[OrgRead])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=OrgRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    slug = re.sub(r'[^a-zA-Z0-9-]', '', org_in.name.lower().replace(" ", "-")) + f"-{str(uuid.uuid4())[:6]}"
    org = Organization(name=org_in.name, slug=slug, plan_tier="free")
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/{org_id}/members", response_model=List[OrgMemberRead])
async def list_members(
    org_id: uuid.UUID,
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    if membership.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to organization")

    stmt = (
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == org_id)
    )
    res = await db.execute(stmt)
    members = []
    for member_record, user_record in res.all():
        members.append(
            OrgMemberRead(
                id=member_record.id,
                user_id=user_record.id,
                email=user_record.email,
                full_name=user_record.full_name,
                role=member_record.role,
                created_at=member_record.created_at
            )
        )
    return members

@router.post("/{org_id}/members", response_model=OrgMemberRead, status_code=status.HTTP_201_CREATED)
async def add_member(
    org_id: uuid.UUID,
    member_in: OrgMemberAdd,
    membership: OrganizationMember = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    if membership.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to organization")

    user_res = await db.execute(select(User).where(User.email == member_in.email))
    target_user = user_res.scalar_one_or_none()
    if not target_user:
        from services.api.app.core.security import get_password_hash
        target_user = User(
            email=member_in.email,
            hashed_password=get_password_hash("Welcome123!"),
            full_name=member_in.email.split("@")[0].capitalize(),
            is_active=True
        )
        db.add(target_user)
        await db.flush()

    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this organization")

    new_member = OrganizationMember(
        organization_id=org_id,
        user_id=target_user.id,
        role=member_in.role
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return OrgMemberRead(
        id=new_member.id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=new_member.role,
        created_at=new_member.created_at
    )

@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    membership: OrganizationMember = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    if membership.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to organization")

    mem_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id
        )
    )
    target_membership = mem_res.scalar_one_or_none()
    if not target_membership:
        raise HTTPException(status_code=404, detail="Organization member not found")

    if target_membership.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")

    await db.delete(target_membership)
    await db.commit()
    return None
