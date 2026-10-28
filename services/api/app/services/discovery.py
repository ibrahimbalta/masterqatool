import uuid
import logging
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.core.ssrf import validate_target_url
from services.api.app.models.project import Project, ProjectScan, DiscoveredPage

logger = logging.getLogger("discovery")

class WebDiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_discovery(self, scan_id: uuid.UUID, allow_private_dev: bool = False) -> ProjectScan:
        stmt = select(ProjectScan).where(ProjectScan.id == scan_id)
        res = await self.db.execute(stmt)
        scan = res.scalar_one_or_none()
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        proj_stmt = select(Project).where(Project.id == scan.project_id)
        proj_res = await self.db.execute(proj_stmt)
        project = proj_res.scalar_one()

        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        await self.db.commit()

        base_url = project.target_url
        is_valid, msg = validate_target_url(base_url, allow_private_dev=allow_private_dev)
        if not is_valid:
            scan.status = "failed"
            scan.error_message = f"Security SSRF check failed: {msg}"
            scan.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return scan

        parsed_base = urlparse(base_url)
        base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

        visited_urls: Set[str] = set()
        queue: List[str] = [base_url]
        max_pages = scan.summary.get("max_pages", 10)

        discovered_count = 0
        forms_total = 0

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            while queue and len(visited_urls) < max_pages:
                current_url = queue.pop(0)
                if current_url in visited_urls:
                    continue

                visited_urls.add(current_url)

                # SSRF check on every URL before fetching
                url_valid, url_msg = validate_target_url(current_url, allow_private_dev=allow_private_dev)
                if not url_valid:
                    logger.warning(f"Skipping URL {current_url} due to SSRF policy: {url_msg}")
                    continue

                try:
                    resp = await client.get(current_url)
                    # If redirect, validate target redirect
                    if resp.status_code in [301, 302, 307, 308]:
                        redir_target = resp.headers.get("location")
                        if redir_target:
                            full_redir = urljoin(current_url, redir_target)
                            redir_parsed = urlparse(full_redir)
                            if f"{redir_parsed.scheme}://{redir_parsed.netloc}" == base_origin:
                                if full_redir not in visited_urls:
                                    queue.append(full_redir)
                        continue

                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        continue

                    page_data = self._analyze_html(current_url, parsed_base.path or "/", resp.text, resp.status_code)

                    discovered_page = DiscoveredPage(
                        scan_id=scan.id,
                        project_id=project.id,
                        url=current_url,
                        path=urlparse(current_url).path or "/",
                        http_status=resp.status_code,
                        title=page_data["title"],
                        forms_detected=page_data["forms"],
                        accessibility_tree=page_data["accessibility_nodes"],
                        provenance="observed"
                    )
                    self.db.add(discovered_page)
                    discovered_count += 1
                    forms_total += len(page_data["forms"])

                    # Enqueue same-origin links
                    for link in page_data["links"]:
                        full_link = urljoin(current_url, link)
                        p_link = urlparse(full_link)
                        # Normalize: ignore fragment
                        normalized = f"{p_link.scheme}://{p_link.netloc}{p_link.path}"
                        if f"{p_link.scheme}://{p_link.netloc}" == base_origin:
                            if normalized not in visited_urls and normalized not in queue:
                                queue.append(normalized)

                except Exception as e:
                    logger.error(f"Error crawling {current_url}: {e}")

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.summary = {
            "pages_discovered": discovered_count,
            "forms_detected": forms_total,
            "max_pages_limit": max_pages,
            "visited_count": len(visited_urls)
        }
        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    def _analyze_html(self, url: str, path: str, html_content: str, status_code: int) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else path

        # Discover forms & interactive fields
        forms_list: List[Dict[str, Any]] = []
        for form_idx, form in enumerate(soup.find_all("form")):
            form_action = form.get("action", "")
            form_method = form.get("method", "GET").upper()
            form_id = form.get("id") or f"form_{form_idx}"

            fields: List[Dict[str, Any]] = []
            for inp in form.find_all(["input", "textarea", "select"]):
                tag_name = inp.name
                input_type = inp.get("type", "text") if tag_name == "input" else tag_name
                input_name = inp.get("name", "")
                input_id = inp.get("id", "")
                placeholder = inp.get("placeholder", "")
                aria_label = inp.get("aria-label", "")
                is_required = inp.has_attr("required")

                # Preferred locator strategy
                recommended_locator = None
                if aria_label:
                    recommended_locator = f"getByLabel('{aria_label}')"
                elif placeholder:
                    recommended_locator = f"getByPlaceholder('{placeholder}')"
                elif input_id:
                    recommended_locator = f"locator('#{input_id}')"
                elif input_name:
                    recommended_locator = f"locator('[name=\"{input_name}\"]')"

                fields.append({
                    "tag": tag_name,
                    "type": input_type,
                    "name": input_name,
                    "id": input_id,
                    "placeholder": placeholder,
                    "aria_label": aria_label,
                    "required": is_required,
                    "recommended_locator": recommended_locator
                })

            buttons: List[Dict[str, Any]] = []
            for btn in form.find_all(["button", "input"]):
                if btn.name == "input" and btn.get("type") not in ["submit", "button"]:
                    continue
                btn_text = btn.get_text(strip=True) or btn.get("value", "") or btn.get("aria-label", "")
                btn_type = btn.get("type", "submit")
                buttons.append({
                    "text": btn_text,
                    "type": btn_type,
                    "recommended_locator": f"getByRole('button', name='{btn_text}')" if btn_text else "getByRole('button')"
                })

            forms_list.append({
                "form_id": form_id,
                "action": form_action,
                "method": form_method,
                "fields": fields,
                "buttons": buttons
            })

        # Key Accessible elements (Buttons outside forms, navigation, links)
        accessibility_nodes: Dict[str, Any] = {
            "buttons_outside_forms": [
                {
                    "text": b.get_text(strip=True),
                    "locator": f"getByRole('button', name='{b.get_text(strip=True)}')"
                }
                for b in soup.find_all("button") if not b.find_parent("form") and b.get_text(strip=True)
            ][:10],
            "landmarks": [tag.name for tag in soup.find_all(["header", "nav", "main", "footer", "aside"])],
        }

        # Links
        links: List[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                links.append(href)

        return {
            "title": title,
            "forms": forms_list,
            "accessibility_nodes": accessibility_nodes,
            "links": links
        }
