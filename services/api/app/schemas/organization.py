from typing import Optional, List
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class OrgCreate(BaseModel):
    name: str

class OrgMemberRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime

class OrgRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan_tier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrgMemberAdd(BaseModel):
    email: str
    role: str = "member"  # admin, member, viewer
