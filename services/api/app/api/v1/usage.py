from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.db.session import get_db
from services.api.app.models.project import Project
from services.api.app.models.subscription import Subscription, UsageRecord
from services.api.app.models.user import OrganizationMember
from services.api.app.schemas.usage import UsageSummaryRead
from services.api.app.security.deps import get_current_organization_membership

router = APIRouter(prefix="/usage", tags=["Usage & Quota"])

@router.get("", response_model=UsageSummaryRead)
async def get_usage_summary(
    membership: OrganizationMember = Depends(get_current_organization_membership),
    db: AsyncSession = Depends(get_db)
):
    # Get active subscription or defaults
    sub_res = await db.execute(
        select(Subscription).where(
            Subscription.organization_id == membership.organization_id,
            Subscription.status == "active"
        )
    )
    sub = sub_res.scalars().first()

    plan_tier = sub.plan_tier if sub else "free"
    test_minutes_limit = sub.max_test_minutes_monthly if sub else 60
    projects_limit = sub.max_projects if sub else 3
    ai_tokens_limit = sub.max_ai_tokens_monthly if sub else 100000
    concurrent_runs_limit = sub.max_concurrent_runs if sub else 1

    # Count projects
    proj_count_res = await db.execute(
        select(func.count(Project.id)).where(Project.organization_id == membership.organization_id)
    )
    projects_count = proj_count_res.scalar() or 0

    # Aggregate test minutes used
    min_res = await db.execute(
        select(func.sum(UsageRecord.quantity)).where(
            UsageRecord.organization_id == membership.organization_id,
            UsageRecord.metric_type == "test_minutes"
        )
    )
    test_minutes_used = float(min_res.scalar() or 0.0)

    # Aggregate AI tokens used
    tokens_res = await db.execute(
        select(func.sum(UsageRecord.quantity)).where(
            UsageRecord.organization_id == membership.organization_id,
            UsageRecord.metric_type == "ai_tokens"
        )
    )
    ai_tokens_used = int(tokens_res.scalar() or 0)

    return UsageSummaryRead(
        plan_tier=plan_tier,
        test_minutes_used=test_minutes_used,
        test_minutes_limit=test_minutes_limit,
        projects_count=projects_count,
        projects_limit=projects_limit,
        ai_tokens_used=ai_tokens_used,
        ai_tokens_limit=ai_tokens_limit,
        concurrent_runs_limit=concurrent_runs_limit
    )
