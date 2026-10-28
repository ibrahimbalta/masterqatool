from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
import uuid

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    role: str

class TokenPayload(BaseModel):
    sub: str
    org_id: Optional[str] = None
    role: Optional[str] = None
    exp: int

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    organization_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)
