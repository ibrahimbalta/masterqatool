import uuid
from sqlalchemy import Column, String, ForeignKey, JSON, Integer, Float, BigInteger, DateTime
from sqlalchemy.orm import relationship
from services.api.app.db.session import Base
from services.api.app.models.base import GUID, TimestampMixin

class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_tier = Column(String(50), default="free", nullable=False)  # free, pro, team
    status = Column(String(50), default="active", nullable=False)  # active, past_due, cancelled, trialing
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    max_test_minutes_monthly = Column(Integer, default=60, nullable=False)
    max_projects = Column(Integer, default=3, nullable=False)
    max_concurrent_runs = Column(Integer, default=1, nullable=False)
    max_ai_tokens_monthly = Column(Integer, default=100000, nullable=False)

    organization = relationship("Organization", back_populates="subscriptions")

class UsageRecord(Base, TimestampMixin):
    __tablename__ = "usage_records"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # test_minutes, ai_tokens, storage_bytes
    quantity = Column(Float, default=0.0, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    reference_id = Column(String(255), nullable=True)  # test_run_id or job_id

    organization = relationship("Organization", back_populates="usage_records")

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, nullable=False, index=True)
    user_id = Column(GUID, nullable=True, index=True)
    action = Column(String(100), nullable=False)  # user_login, project_created, test_run_cancelled, etc.
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)
