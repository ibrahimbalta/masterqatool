from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class TestCaseCreate(BaseModel):
    code_identifier: str
    title: str
    objective: Optional[str] = None
    category: str = "Functional"
    priority: str = "medium"
    risk_level: str = "medium"
    automation_status: str = "candidate"
    approval_status: str = "draft"
    preconditions: List[str] = []
    test_data: Dict[str, Any] = {}
    steps: List[Dict[str, Any]] = []
    expected_result: str

class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    objective: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    automation_status: Optional[str] = None
    approval_status: Optional[str] = None
    preconditions: Optional[List[str]] = None
    test_data: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None

class TestCaseRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    suite_id: Optional[uuid.UUID] = None
    code_identifier: str
    title: str
    objective: Optional[str] = None
    category: str
    priority: str
    risk_level: str
    automation_status: str
    approval_status: str
    current_version: int
    ai_confidence_score: Optional[float] = None
    provenance: str
    latest_spec: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
