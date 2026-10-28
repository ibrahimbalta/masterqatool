from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TestCaseCategory(str, Enum):
    FUNCTIONAL = "Functional"
    NEGATIVE = "Negative"
    BOUNDARY_VALUE = "Boundary Value"
    VALIDATION = "Validation"
    REGRESSION = "Regression"
    SMOKE = "Smoke"
    API = "API"
    ACCESSIBILITY = "Accessibility"
    VISUAL = "Visual"
    EXPLORATORY = "Exploratory"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AutomationStatus(str, Enum):
    MANUAL_ONLY = "manual_only"
    AUTOMATED = "automated"
    CANDIDATE = "candidate"
    IN_PROGRESS = "in_progress"

class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"

class Provenance(str, Enum):
    OBSERVED = "observed"
    SOURCE_CODE = "source_code"
    AI_INFERRED = "ai_inferred"
    MANUAL = "manual"

class ActionType(str, Enum):
    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    PRESS = "press"
    SELECT_OPTION = "select_option"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_TEXT = "assert_text"
    ASSERT_URL = "assert_url"
    WAIT_FOR = "wait_for"

class TestStepSpec(BaseModel):
    step_number: int
    action_type: ActionType
    description: str
    target_locator: Optional[str] = None
    input_value: Optional[str] = None
    expected_result: str
    timeout_ms: int = Field(default=5000)

class TestCaseSpec(BaseModel):
    code_identifier: str = Field(description="Unique code identifier, e.g. TC-001")
    title: str
    objective: str
    category: TestCaseCategory
    priority: Priority
    risk_level: RiskLevel
    automation_status: AutomationStatus = AutomationStatus.CANDIDATE
    provenance: Provenance = Provenance.AI_INFERRED
    ai_confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preconditions: List[str] = Field(default_factory=list)
    test_data: Dict[str, Any] = Field(default_factory=dict)
    steps: List[TestStepSpec]
    expected_result: str
