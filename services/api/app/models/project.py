import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from services.api.app.db.session import Base
from services.api.app.models.base import GUID, TimestampMixin

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_url = Column(String(2048), nullable=False)
    github_repo = Column(String(255), nullable=True)
    environment = Column(String(50), default="staging", nullable=False)
    status = Column(String(50), default="active", nullable=False)

    organization = relationship("Organization", back_populates="projects")
    connections = relationship("ProjectConnection", back_populates="project", cascade="all, delete-orphan")
    scans = relationship("ProjectScan", back_populates="project", cascade="all, delete-orphan")
    test_suites = relationship("TestSuite", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")
    bugs = relationship("Bug", back_populates="project", cascade="all, delete-orphan")

class ProjectConnection(Base, TimestampMixin):
    __tablename__ = "project_connections"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_type = Column(String(50), nullable=False)  # github, url_auth, api_docs
    credentials_encrypted = Column(Text, nullable=True)
    status = Column(String(50), default="connected", nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="connections")

class ProjectScan(Base, TimestampMixin):
    __tablename__ = "project_scans"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_type = Column(String(50), default="url_crawler", nullable=False)  # url_crawler, github_code, hybrid
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="scans")
    discovered_pages = relationship("DiscoveredPage", back_populates="scan", cascade="all, delete-orphan")

class DiscoveredPage(Base, TimestampMixin):
    __tablename__ = "discovered_pages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scan_id = Column(GUID, ForeignKey("project_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    path = Column(String(1024), nullable=False)
    http_status = Column(Integer, nullable=True)
    title = Column(String(512), nullable=True)
    forms_detected = Column(JSON, default=list, nullable=False)
    accessibility_tree = Column(JSON, default=dict, nullable=False)
    provenance = Column(String(50), default="observed", nullable=False)  # observed, source_code, ai_inferred, unverified

    scan = relationship("ProjectScan", back_populates="discovered_pages")
