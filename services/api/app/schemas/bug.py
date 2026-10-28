from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class BugCreate(BaseModel):
    project_id: uuid.UUID
    test_result_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    reproduction_steps: List[str] = []
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    root_cause_hypothesis: Optional[str] = None

class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    verified_cause: Optional[str] = None

class BugRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    test_result_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    severity: str
    reproduction_steps: List[str] = []
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    root_cause_hypothesis: Optional[str] = None
    verified_cause: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
