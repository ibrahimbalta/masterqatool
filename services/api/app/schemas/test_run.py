from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class TestRunCreate(BaseModel):
    project_id: uuid.UUID
    test_case_ids: Optional[List[uuid.UUID]] = None
    trigger: str = "manual"

class ArtifactRead(BaseModel):
    id: uuid.UUID
    artifact_type: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TestStepRead(BaseModel):
    id: uuid.UUID
    step_number: int
    action_type: str
    target_locator: Optional[str] = None
    input_value: Optional[str] = None
    status: str
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int

    model_config = ConfigDict(from_attributes=True)

class TestResultRead(BaseModel):
    id: uuid.UUID
    test_run_id: uuid.UUID
    test_case_id: uuid.UUID
    test_case_code: Optional[str] = None
    test_case_title: Optional[str] = None
    status: str
    duration_ms: int
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    steps: List[TestStepRead] = []
    artifacts: List[ArtifactRead] = []

    model_config = ConfigDict(from_attributes=True)

class TestRunRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    organization_id: uuid.UUID
    trigger: str
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    duration_ms: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    results: List[TestResultRead] = []

    model_config = ConfigDict(from_attributes=True)
