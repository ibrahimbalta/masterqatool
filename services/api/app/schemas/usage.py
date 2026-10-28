from typing import Dict, Any
from pydantic import BaseModel

class UsageSummaryRead(BaseModel):
    plan_tier: str
    test_minutes_used: float
    test_minutes_limit: int
    projects_count: int
    projects_limit: int
    ai_tokens_used: int
    ai_tokens_limit: int
    concurrent_runs_limit: int
