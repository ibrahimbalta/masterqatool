import uuid
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from services.api.app.models.test_run import LocatorRepair, TestResult
from services.api.app.models.test_suite import TestCase

logger = logging.getLogger("self_healing")

class SelfHealingAssistant:
    @staticmethod
    def analyze_dom_for_alternatives(
        dom_html: str,
        failed_locator: str,
        action_type: str,
        input_value: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Parses current DOM and extracts prioritized locator candidates for repairing broken selectors."""
        soup = BeautifulSoup(dom_html or "", "html.parser")
        candidates: List[Dict[str, Any]] = []

        # If action was a click on a button/link
        if action_type in ["click"]:
            # 1. getByRole('button', name='...')
            for btn in soup.find_all(["button", "a", "input"]):
                if btn.name == "input" and btn.get("type") not in ["submit", "button"]:
                    continue
                name_text = btn.get_text(strip=True) or btn.get("value", "") or btn.get("aria-label", "")
                if name_text:
                    role = "button" if btn.name in ["button", "input"] else "link"
                    candidates.append({
                        "suggested_locator": f"getByRole('{role}', name='{name_text}')",
                        "strategy": "getByRole",
                        "confidence_score": 0.92,
                        "dom_snippet": str(btn)[:200]
                    })

                testid = btn.get("data-testid") or btn.get("data-test")
                if testid:
                    candidates.append({
                        "suggested_locator": f"getByTestId('{testid}')",
                        "strategy": "getByTestId",
                        "confidence_score": 0.88,
                        "dom_snippet": str(btn)[:200]
                    })

        # If action was filling an input
        elif action_type in ["fill", "type"]:
            for inp in soup.find_all(["input", "textarea"]):
                aria_label = inp.get("aria-label")
                if aria_label:
                    candidates.append({
                        "suggested_locator": f"getByLabel('{aria_label}')",
                        "strategy": "getByLabel",
                        "confidence_score": 0.95,
                        "dom_snippet": str(inp)[:200]
                    })

                placeholder = inp.get("placeholder")
                if placeholder:
                    candidates.append({
                        "suggested_locator": f"getByPlaceholder('{placeholder}')",
                        "strategy": "getByPlaceholder",
                        "confidence_score": 0.89,
                        "dom_snippet": str(inp)[:200]
                    })

                testid = inp.get("data-testid") or inp.get("data-test")
                if testid:
                    candidates.append({
                        "suggested_locator": f"getByTestId('{testid}')",
                        "strategy": "getByTestId",
                        "confidence_score": 0.85,
                        "dom_snippet": str(inp)[:200]
                    })

        # General text fallback
        if not candidates and failed_locator:
            # Clean selector fallback
            candidates.append({
                "suggested_locator": f"locator('{failed_locator.split(' > ')[-1]}')",
                "strategy": "css",
                "confidence_score": 0.60,
                "dom_snippet": ""
            })

        return candidates
