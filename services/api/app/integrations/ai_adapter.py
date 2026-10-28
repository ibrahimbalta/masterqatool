import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from pydantic import ValidationError

from packages.test_schema.models import TestCaseSpec, TestStepSpec, TestCaseCategory, Priority, RiskLevel, AutomationStatus, Provenance, ActionType
from services.api.app.core.config import settings

logger = logging.getLogger("ai_adapter")

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_test_cases(self, project_name: str, target_url: str, discovered_pages: List[Dict[str, Any]]) -> List[TestCaseSpec]:
        pass

class MockAIProvider(BaseAIProvider):
    """Deterministic, schema-compliant provider for offline testing and local evaluation."""
    async def generate_test_cases(self, project_name: str, target_url: str, discovered_pages: List[Dict[str, Any]]) -> List[TestCaseSpec]:
        generated: List[TestCaseSpec] = []
        tc_counter = 1

        for page in discovered_pages:
            url = page.get("url", target_url)
            path = page.get("path", "/")
            title = page.get("title", "Page")
            forms = page.get("forms", [])

            # 1. Functional Smoke Test
            generated.append(
                TestCaseSpec(
                    code_identifier=f"TC-SMK-{tc_counter:03d}",
                    title=f"Verify {title} loads with accessible navigation and valid status",
                    objective=f"Ensure {path} responds and principal landmarks are visible in DOM",
                    category=TestCaseCategory.SMOKE,
                    priority=Priority.HIGH,
                    risk_level=RiskLevel.LOW,
                    automation_status=AutomationStatus.AUTOMATED,
                    provenance=Provenance.AI_INFERRED,
                    ai_confidence_score=0.95,
                    preconditions=["Network connectivity to target environment is active"],
                    test_data={"target_url": url},
                    steps=[
                        TestStepSpec(
                            step_number=1,
                            action_type=ActionType.GOTO,
                            description=f"Navigate to {url}",
                            target_locator=url,
                            expected_result="Page loads with HTTP 200"
                        ),
                        TestStepSpec(
                            step_number=2,
                            action_type=ActionType.ASSERT_VISIBLE,
                            description="Assert page title or main container is visible",
                            target_locator="main, h1, body",
                            expected_result="Main container is visible"
                        )
                    ],
                    expected_result=f"Page {path} renders correctly without console errors"
                )
            )
            tc_counter += 1

            # 2. Form Validation & Negative Test Cases
            for form in forms:
                form_id = form.get("form_id", "form")
                fields = form.get("fields", [])
                buttons = form.get("buttons", [])
                btn_locator = buttons[0]["recommended_locator"] if buttons else "getByRole('button')"

                # Negative / Boundary Test for required inputs
                required_fields = [f for f in fields if f.get("required") or f.get("name") in ["email", "password", "username", "name"]]
                if required_fields:
                    first_req = required_fields[0]
                    target_loc = first_req.get("recommended_locator") or f"locator('[name=\"{first_req.get('name')}\"]')"
                    generated.append(
                        TestCaseSpec(
                            code_identifier=f"TC-VAL-{tc_counter:03d}",
                            title=f"Validate submission error when required field '{first_req.get('name')}' is empty on {path}",
                            objective=f"Negative test verifying client-side validation prevents empty submission on {form_id}",
                            category=TestCaseCategory.NEGATIVE,
                            priority=Priority.MEDIUM,
                            risk_level=RiskLevel.MEDIUM,
                            automation_status=AutomationStatus.AUTOMATED,
                            provenance=Provenance.AI_INFERRED,
                            ai_confidence_score=0.90,
                            preconditions=["Navigate to form page"],
                            test_data={"invalid_input": ""},
                            steps=[
                                TestStepSpec(
                                    step_number=1,
                                    action_type=ActionType.GOTO,
                                    description=f"Open form at {url}",
                                    target_locator=url,
                                    expected_result="Form renders"
                                ),
                                TestStepSpec(
                                    step_number=2,
                                    action_type=ActionType.FILL,
                                    description=f"Clear required input '{first_req.get('name')}'",
                                    target_locator=target_loc,
                                    input_value="",
                                    expected_result="Input is empty"
                                ),
                                TestStepSpec(
                                    step_number=3,
                                    action_type=ActionType.CLICK,
                                    description="Attempt form submission",
                                    target_locator=btn_locator,
                                    expected_result="Validation error displayed"
                                ),
                                TestStepSpec(
                                    step_number=4,
                                    action_type=ActionType.ASSERT_VISIBLE,
                                    description="Verify error state or required attribute",
                                    target_locator=":invalid, [role='alert'], .error",
                                    expected_result="Validation indicator is visible"
                                )
                            ],
                            expected_result="Form rejects submission and guides user to complete required field"
                        )
                    )
                    tc_counter += 1

        # Fallback if no pages provided
        if not generated:
            generated.append(
                TestCaseSpec(
                    code_identifier="TC-GEN-001",
                    title=f"Verify target home page loads at {target_url}",
                    objective="Base connectivity and rendering validation",
                    category=TestCaseCategory.SMOKE,
                    priority=Priority.HIGH,
                    risk_level=RiskLevel.LOW,
                    automation_status=AutomationStatus.AUTOMATED,
                    provenance=Provenance.AI_INFERRED,
                    ai_confidence_score=0.90,
                    preconditions=[],
                    test_data={"target_url": target_url},
                    steps=[
                        TestStepSpec(
                            step_number=1,
                            action_type=ActionType.GOTO,
                            description=f"Navigate to {target_url}",
                            target_locator=target_url,
                            expected_result="HTTP status 200"
                        )
                    ],
                    expected_result="Home page displays successfully"
                )
            )

        return generated

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_test_cases(self, project_name: str, target_url: str, discovered_pages: List[Dict[str, Any]]) -> List[TestCaseSpec]:
        # Implementation calling OpenAI chat completions with structured JSON schema format
        prompt = (
            f"You are a QA Automation Architect. Analyze the following discovered web pages for project '{project_name}' ({target_url}):\n"
            f"{json.dumps(discovered_pages, indent=2)}\n"
            "Generate comprehensive test cases adhering strictly to the JSON schema with categories: Functional, Negative, Boundary Value, Smoke, API, Accessibility."
        )
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You output strictly valid JSON conforming to the requested schema."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API failed: {resp.status_code} - {resp.text}")
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            raw_cases = parsed.get("test_cases", [])
            valid_cases: List[TestCaseSpec] = []
            for item in raw_cases:
                try:
                    valid_cases.append(TestCaseSpec.model_validate(item))
                except ValidationError as e:
                    logger.warning(f"Skipping invalid AI test case schema: {e}")
            return valid_cases

def get_ai_provider() -> BaseAIProvider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured in environment")
        return OpenAIProvider(settings.OPENAI_API_KEY)
    elif provider == "mock":
        return MockAIProvider()
    else:
        # Default fallback to Mock if provider key not configured
        return MockAIProvider()
