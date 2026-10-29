from typing import Optional, List
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from services.api.app.schemas.test_case import TestCaseRead

class TestSuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "smoke"

class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class TestSuiteRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: str
    total_cases: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TestSuiteDetail(TestSuiteRead):
    test_cases: List[TestCaseRead] = []

    model_config = ConfigDict(from_attributes=True)
