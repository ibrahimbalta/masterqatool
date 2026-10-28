import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from services.api.app.db.session import Base
from services.api.app.models.base import GUID, TimestampMixin

class Bug(Base, TimestampMixin):
    __tablename__ = "bugs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    test_result_id = Column(GUID, ForeignKey("test_results.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    reproduction_steps = Column(JSON, default=list, nullable=False)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    root_cause_hypothesis = Column(Text, nullable=True)
    verified_cause = Column(Text, nullable=True)
    status = Column(String(50), default="open", nullable=False)  # open, in_investigation, resolved, ignored

    project = relationship("Project", back_populates="bugs")
    test_result = relationship("TestResult")
