import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from services.api.app.db.session import Base
from services.api.app.models.base import GUID, TimestampMixin

class TestSuite(Base, TimestampMixin):
    __tablename__ = "test_suites"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="smoke", nullable=False)

    project = relationship("Project", back_populates="test_suites")
    test_cases = relationship("TestCase", back_populates="test_suite")

class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    suite_id = Column(GUID, ForeignKey("test_suites.id", ondelete="SET NULL"), nullable=True, index=True)
    code_identifier = Column(String(50), nullable=False)  # e.g., TC-001
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=True)
    category = Column(String(50), default="Functional", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    risk_level = Column(String(20), default="medium", nullable=False)
    automation_status = Column(String(50), default="candidate", nullable=False)
    approval_status = Column(String(50), default="draft", nullable=False)  # draft, in_review, approved, archived
    current_version = Column(Integer, default=1, nullable=False)
    ai_confidence_score = Column(Float, nullable=True)
    provenance = Column(String(50), default="ai_inferred", nullable=False)
    latest_spec = Column(JSON, default=dict, nullable=False)  # preconditions, steps, test_data, expected_result

    project = relationship("Project", back_populates="test_cases")
    test_suite = relationship("TestSuite", back_populates="test_cases")
    versions = relationship("TestCaseVersion", back_populates="test_case", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="test_case")

    __table_args__ = (
        UniqueConstraint("project_id", "code_identifier", name="uq_project_test_case_code"),
    )

class TestCaseVersion(Base, TimestampMixin):
    __tablename__ = "test_case_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    test_case_id = Column(GUID, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    spec_snapshot = Column(JSON, nullable=False)
    change_summary = Column(String(512), nullable=True)
    changed_by_user_id = Column(GUID, nullable=True)

    test_case = relationship("TestCase", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("test_case_id", "version_number", name="uq_case_version"),
    )
