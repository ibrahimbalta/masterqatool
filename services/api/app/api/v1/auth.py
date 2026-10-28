import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.core.security import get_password_hash, verify_password, create_access_token
from services.api.app.db.session import get_db
from services.api.app.models.user import User, Organization, OrganizationMember
from services.api.app.models.subscription import Subscription, AuditLog
from services.api.app.schemas.auth import Token, UserRegister, UserLogin, UserRead
from services.api.app.security.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    if len(user_in.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    # Create User
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name or user_in.email.split("@")[0]
    )
    db.add(new_user)
    await db.flush()

    # Create default Organization
    org_name = user_in.organization_name or f"{new_user.full_name}'s Team"
    slug = re.sub(r'[^a-zA-Z0-9-]', '', org_name.lower().replace(" ", "-")) + f"-{str(uuid.uuid4())[:6]}"
    new_org = Organization(
        name=org_name,
        slug=slug,
        plan_tier="free"
    )
    db.add(new_org)
    await db.flush()

    # Add as Owner
    member = OrganizationMember(
        organization_id=new_org.id,
        user_id=new_user.id,
        role="owner"
    )
    db.add(member)

    # Initialize Subscription
    sub = Subscription(
        organization_id=new_org.id,
        plan_tier="free",
        max_test_minutes_monthly=60,
        max_projects=3,
        max_concurrent_runs=1,
        max_ai_tokens_monthly=100000
    )
    db.add(sub)

    # Record Audit Log
    audit = AuditLog(
        organization_id=new_org.id,
        user_id=new_user.id,
        action="user_registered",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"email": new_user.email}
    )
    db.add(audit)
    await db.commit()

    token = create_access_token(
        subject=new_user.id,
        org_id=new_org.id,
        role="owner"
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        organization_id=new_org.id,
        role="owner"
    )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive account")

    # Fetch primary organization membership
    member_res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
        .order_by(OrganizationMember.created_at.asc())
    )
    membership = member_res.scalars().first()

    org_id = membership.organization_id if membership else None
    role = membership.role if membership else "viewer"

    token = create_access_token(subject=user.id, org_id=org_id, role=role)

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        organization_id=org_id,
        role=role
    )

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
