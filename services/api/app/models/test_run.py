import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Integer, BigInteger, DateTime
from sqlalchemy.orm import relationship
from services.api.app.db.session import Base
from services.api.app.models.base import GUID, TimestampMixin

class TestRun(Base, TimestampMixin):
    __tablename__ = "test_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger = Column(String(50), default="manual", nullable=False)  # manual, schedule, webhook, ci
    status = Column(String(50), default="queued", nullable=False)  # queued, starting, running, passed, failed, blocked, cancelled, timed_out, flaky
    total_cases = Column(Integer, default=0, nullable=False)
    passed_cases = Column(Integer, default=0, nullable=False)
    failed_cases = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    project = relationship("Project", back_populates="test_runs")
    results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan")

class TestResult(Base, TimestampMixin):
    __tablename__ = "test_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    test_run_id = Column(GUID, ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(GUID, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="queued", nullable=False)  # passed, failed, blocked, skipped, flaky
    duration_ms = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    test_run = relationship("TestRun", back_populates="results")
    test_case = relationship("TestCase", back_populates="results")
    steps = relationship("TestStep", back_populates="test_result", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="test_result", cascade="all, delete-orphan")

class TestStep(Base, TimestampMixin):
    __tablename__ = "test_steps"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    test_result_id = Column(GUID, ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    target_locator = Column(String(512), nullable=True)
    input_value = Column(String(512), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # passed, failed, skipped
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)

    test_result = relationship("TestResult", back_populates="steps")

class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    test_result_id = Column(GUID, ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type = Column(String(50), nullable=False)  # screenshot, playwright_trace, console_log, network_har
    storage_path = Column(String(1024), nullable=False)
    mime_type = Column(String(100), default="image/png", nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)

    test_result = relationship("TestResult", back_populates="artifacts")
