from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class ScanCreate(BaseModel):
    scan_type: str = "url_crawler"  # url_crawler, github_code, hybrid
    max_pages: int = 15

class DiscoveredPageRead(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    url: str
    path: str
    http_status: Optional[int] = None
    title: Optional[str] = None
    forms_detected: List[Dict[str, Any]] = []
    accessibility_tree: Dict[str, Any] = {}
    provenance: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScanRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    scan_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Dict[str, Any] = {}
    error_message: Optional[str] = None
    discovered_pages: List[DiscoveredPageRead] = []

    model_config = ConfigDict(from_attributes=True)
