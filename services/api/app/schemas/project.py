from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_url: str
    github_repo: Optional[str] = None
    environment: str = "staging"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[str] = None
    github_repo: Optional[str] = None
    environment: Optional[str] = None
    status: Optional[str] = None

class ProjectRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    target_url: str
    github_repo: Optional[str] = None
    environment: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class URLValidationRequest(BaseModel):
    url: str

class URLValidationResponse(BaseModel):
    valid: bool
    message: str
    normalized_url: Optional[str] = None
