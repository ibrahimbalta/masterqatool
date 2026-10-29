"""
Seed realistic demo data into the AI QA Agent database for immediate dashboard exploration.
Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add repository root to python search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure database path
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./qa_agent.db"

from services.api.app.db.session import engine, Base, AsyncSessionLocal
from services.api.app.core.security import get_password_hash
from services.api.app.models.user import User, Organization, OrganizationMember
from services.api.app.models.project import Project, ProjectConnection, ProjectScan, DiscoveredPage
from services.api.app.models.test_suite import TestSuite, TestCase, TestCaseVersion
from services.api.app.models.test_run import TestRun, TestResult, TestStep, Artifact, LocatorRepair
from services.api.app.models.bug import Bug
from services.api.app.models.subscription import Subscription, UsageRecord, AuditLog

async def seed():
    print("Connecting to database and initializing schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Create or get demo user
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.email == "architect@acme-qa.com"))
        user = res.scalar_one_or_none()

        if not user:
            print("Creating demo user: architect@acme-qa.com ...")
            user = User(
                email="architect@acme-qa.com",
                hashed_password=get_password_hash("SecurePass123!"),
                full_name="Alex Mercer (Lead Architect)",
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.flush()

            org = Organization(
                name="Acme Enterprise QA",
                slug="acme-enterprise-qa",
                plan_tier="pro"
            )
            session.add(org)
            await session.flush()

            membership = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role="owner"
            )
            session.add(membership)

            # Subscription
            sub = Subscription(
                organization_id=org.id,
                plan_tier="pro",
                status="active",
                max_projects=20,
                max_test_minutes_monthly=1000,
                max_ai_tokens_monthly=500000,
                max_concurrent_runs=5
            )
            session.add(sub)
        else:
            print("User architect@acme-qa.com already exists, finding organization...")
            mem_res = await session.execute(select(OrganizationMember).where(OrganizationMember.user_id == user.id))
            membership = mem_res.scalars().first()
            org_res = await session.execute(select(Organization).where(Organization.id == membership.organization_id))
            org = org_res.scalar_one()

        # 2. Create Project
        proj_res = await session.execute(
            select(Project).where(Project.organization_id == org.id, Project.name == "Acme SaaS Cloud Portal")
        )
        project = proj_res.scalar_one_or_none()

        if not project:
            print("Creating Demo Project: Acme SaaS Cloud Portal ...")
            project = Project(
                organization_id=org.id,
                name="Acme SaaS Cloud Portal",
                description="Enterprise customer portal with authentication, billing, and project management.",
                target_url="https://example.com",
                github_repo="https://github.com/acme/cloud-portal",
                environment="staging",
                status="active"
            )
            session.add(project)
            await session.flush()

            # Connection
            conn = ProjectConnection(
                project_id=project.id,
                connection_type="github",
                status="connected",
                last_verified_at=datetime.now(timezone.utc)
            )
            session.add(conn)

            # 3. Create Discovered Pages
            scan = ProjectScan(
                project_id=project.id,
                scan_type="url_crawler",
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                summary={"pages_discovered": 3, "forms_detected": 2}
            )
            session.add(scan)
            await session.flush()

            page1 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/",
                path="/",
                http_status=200,
                title="Acme Cloud Portal — Home",
                forms_detected=[],
                accessibility_tree={"role": "document", "name": "Acme Portal"},
                provenance="observed"
            )
            page2 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/login",
                path="/login",
                http_status=200,
                title="Customer Sign In",
                forms_detected=[
                    {
                        "form_id": "login-form",
                        "action": "/api/v1/auth/login",
                        "method": "POST",
                        "fields": [
                            {"name": "email", "type": "email", "required": True, "recommended_locator": "input[name='email']"},
                            {"name": "password", "type": "password", "required": True, "recommended_locator": "input[name='password']"}
                        ],
                        "inputs": [
                            {"name": "email", "type": "email", "required": True, "recommended_locator": "input[name='email']"},
                            {"name": "password", "type": "password", "required": True, "recommended_locator": "input[name='password']"}
                        ],
                        "buttons": [{"text": "Sign In", "type": "submit"}]
                    }
                ],
                accessibility_tree={"role": "form", "name": "Login Form"},
                provenance="observed"
            )
            page3 = DiscoveredPage(
                scan_id=scan.id,
                project_id=project.id,
                url="https://example.com/dashboard",
                path="/dashboard",
                http_status=200,
                title="User Workspace Dashboard",
                forms_detected=[],
                accessibility_tree={"role": "main", "name": "Dashboard"},
                provenance="source_code"
            )
            session.add_all([page1, page2, page3])

            # 4. Create Test Suite
            suite = TestSuite(
                project_id=project.id,
                name="Daily Core Smoke Suite",
                description="Fast-feedback sanity tests run on every pull request and staging deployment.",
                category="smoke"
            )
            session.add(suite)
            await session.flush()

            # 5. Create Test Cases
            tc1 = TestCase(
                project_id=project.id,
                suite_id=suite.id,
                code_identifier="TC-AUTH-001",
                title="Verify login screen loads and elements are visible",
                objective="Ensure login inputs and submit buttons render properly.",
                category="Smoke",
                priority="high",
                risk_level="medium",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.96,
                provenance="ai_inferred",
                latest_spec={
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loads"},
                        {"step_number": 2, "action_type": "assert_visible", "target_locator": "h1", "expected_result": "Heading is visible"}
                    ],
                    "expected_result": "Login form elements are interactive"
                }
            )

            tc2 = TestCase(
                project_id=project.id,
                suite_id=suite.id,
                code_identifier="TC-AUTH-002",
                title="Verify submission with invalid credentials displays error banner",
                objective="Confirm validation message appears when authentication fails.",
                category="Negative",
                priority="critical",
                risk_level="high",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.91,
                provenance="ai_inferred",
                latest_spec={
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://example.com", "expected_result": "Page loads"},
                        {"step_number": 2, "action_type": "click", "target_locator": "button#btn-broken-action", "expected_result": "Click button"}
                    ],
                    "expected_result": "System raises error banner"
                }
            )

            session.add_all([tc1, tc2])
            await session.flush()

            # 6. Create Test Run with real PASS and FAIL results & Artifact
            test_run = TestRun(
                project_id=project.id,
                organization_id=org.id,
                trigger="manual",
                status="failed",
                total_cases=2,
                passed_cases=1,
                failed_cases=1,
                duration_ms=4850,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            session.add(test_run)
            await session.flush()

            # Result 1: PASS
            res1 = TestResult(
                test_run_id=test_run.id,
                test_case_id=tc1.id,
                status="passed",
                duration_ms=2100
            )
            session.add(res1)
            await session.flush()

            step1 = TestStep(
                test_result_id=res1.id,
                step_number=1,
                action_type="goto",
                target_locator="https://example.com",
                status="passed",
                expected_result="Page loads",
                actual_result="Navigated to https://example.com",
                duration_ms=1200
            )
            step2 = TestStep(
                test_result_id=res1.id,
                step_number=2,
                action_type="assert_visible",
                target_locator="h1",
                status="passed",
                expected_result="Heading is visible",
                actual_result="Element is visible as expected",
                duration_ms=900
            )
            session.add_all([step1, step2])

            # Result 2: FAIL
            res2 = TestResult(
                test_run_id=test_run.id,
                test_case_id=tc2.id,
                status="failed",
                duration_ms=2750,
                error_message="Element with locator 'button#btn-broken-action' could not be resolved or clicked."
            )
            session.add(res2)
            await session.flush()

            fail_step1 = TestStep(
                test_result_id=res2.id,
                step_number=1,
                action_type="goto",
                target_locator="https://example.com",
                status="passed",
                expected_result="Page loads",
                actual_result="Navigated to https://example.com",
                duration_ms=1300
            )
            fail_step2 = TestStep(
                test_result_id=res2.id,
                step_number=2,
                action_type="click",
                target_locator="button#btn-broken-action",
                status="failed",
                expected_result="Click button",
                actual_result="Execution failed: Element not found",
                error_message="Element with locator 'button#btn-broken-action' could not be resolved or clicked.",
                duration_ms=1450
            )
            session.add_all([fail_step1, fail_step2])

            # Artifact (Screenshot)
            os.makedirs("./artifacts_storage", exist_ok=True)
            screenshot_path = f"./artifacts_storage/screenshot_demo_{res2.id}_2.png"
            with open(screenshot_path, "wb") as f:
                f.write(b"DEMO_SCREENSHOT_BINARY_DATA_EVIDENCE_PNG")

            artifact = Artifact(
                test_result_id=res2.id,
                artifact_type="screenshot",
                storage_path=screenshot_path,
                mime_type="image/png",
                file_size_bytes=len(b"DEMO_SCREENSHOT_BINARY_DATA_EVIDENCE_PNG")
            )
            session.add(artifact)

            # Self-healing locator repair candidate
            repair = LocatorRepair(
                test_result_id=res2.id,
                test_case_id=tc2.id,
                step_number=2,
                original_locator="button#btn-broken-action",
                suggested_locator="getByRole('button', name='Sign In')",
                strategy="getByRole",
                confidence_score=0.94,
                dom_snippet="<button type='submit' class='btn-primary'>Sign In</button>",
                status="pending"
            )
            session.add(repair)

            # 7. Bug Dossier
            bug = Bug(
                project_id=project.id,
                test_result_id=res2.id,
                title="Failure in TC-AUTH-002: Verify submission with invalid credentials",
                description="Step #2 failed during automated Playwright execution. Button selector could not be located in current DOM.",
                severity="critical",
                reproduction_steps=[
                    "1. Navigate to target URL https://example.com",
                    "2. Attempt to resolve locator button#btn-broken-action",
                    "3. Browser raises timeout: element not found"
                ],
                expected_behavior="Button should be clicked and error banner displayed",
                actual_behavior="Element with locator 'button#btn-broken-action' could not be resolved or clicked",
                root_cause_hypothesis="Button element selector updated in latest frontend build. Use getByRole('button', name='Sign In').",
                status="open"
            )
            session.add(bug)

            # 8. Usage Records
            usage1 = UsageRecord(
                organization_id=org.id,
                metric_type="test_minutes",
                quantity=0.08,
                recorded_at=datetime.now(timezone.utc),
                reference_id=str(test_run.id)
            )
            usage2 = UsageRecord(
                organization_id=org.id,
                metric_type="ai_tokens",
                quantity=320,
                recorded_at=datetime.now(timezone.utc),
                reference_id=str(project.id)
            )
            session.add_all([usage1, usage2])
            await session.commit()
            print("Acme demo data seeded successfully!")

        # 9. Create Project: HAS-TAT Aktar & Kuruyemiş
        hastat_res = await session.execute(
            select(Project).where(Project.organization_id == org.id, Project.name == "HAS-TAT Aktar & Kuruyemiş")
        )
        hastat = hastat_res.scalar_one_or_none()
        if not hastat:
            print("Creating Project: HAS-TAT Aktar & Kuruyemiş ...")
            hastat = Project(
                organization_id=org.id,
                name="HAS-TAT Aktar & Kuruyemiş",
                description="Doğal Şifa & Taze Kavrum Lezzetler - Bartın E-Ticaret ve Ürün Kataloğu Web Uygulaması",
                target_url="https://ibrahimbalta.github.io/hastat/",
                github_repo="https://github.com/ibrahimbalta/hastat",
                environment="production",
                status="active"
            )
            session.add(hastat)
            await session.flush()

            # Discovered pages for HAS-TAT
            hastat_scan = ProjectScan(
                project_id=hastat.id,
                scan_type="url_crawler",
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                summary={"pages_discovered": 4, "forms_detected": 1}
            )
            session.add(hastat_scan)
            await session.flush()

            hp1 = DiscoveredPage(
                scan_id=hastat_scan.id,
                project_id=hastat.id,
                url="https://ibrahimbalta.github.io/hastat/",
                path="/",
                http_status=200,
                title="HAS-TAT Aktar & Kuruyemiş | Doğal Şifa & Taze Kavrum Lezzetler",
                forms_detected=[{
                    "form_id": "search-form",
                    "action": "#",
                    "method": "GET",
                    "fields": [{"name": "q", "type": "text", "required": False, "recommended_locator": "input[placeholder*='Ürün ara']"}],
                    "inputs": [{"name": "q", "type": "text", "required": False, "recommended_locator": "input[placeholder*='Ürün ara']"}],
                    "buttons": [{"text": "Ara", "type": "submit"}]
                }],
                accessibility_tree={"role": "main", "name": "HAS-TAT Katalog"},
                provenance="observed"
            )
            hp2 = DiscoveredPage(
                scan_id=hastat_scan.id,
                project_id=hastat.id,
                url="https://ibrahimbalta.github.io/hastat/#/kuruyemis",
                path="/#/kuruyemis",
                http_status=200,
                title="Taze Kavrum Kuruyemişler — HAS-TAT",
                forms_detected=[],
                accessibility_tree={"role": "region", "name": "Kuruyemiş Listesi"},
                provenance="observed"
            )
            session.add_all([hp1, hp2])

            # Test Cases for HAS-TAT
            tc_h1 = TestCase(
                project_id=hastat.id,
                code_identifier="TC-HASTAT-001",
                title="Ürün Arama ve Listeleme Fonksiyon Testi",
                objective="Kullanıcının arama çubuğuna 'Ihlamur' yazarak ürünü anında filtreleyebildiğini doğrular.",
                category="functional",
                priority="high",
                risk_level="medium",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.98,
                provenance="ai_inferred",
                latest_spec={
                    "preconditions": ["HAS-TAT anasayfası açılmış olmalı"],
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://ibrahimbalta.github.io/hastat/", "expected_result": "Sayfa HTTP 200 ile yüklenir"},
                        {"step_number": 2, "action_type": "fill", "target_locator": "input[type='text'], input[placeholder*='ara' i]", "input_value": "Ihlamur", "expected_result": "Arama kutusuna Ihlamur yazılır"},
                        {"step_number": 3, "action_type": "assert_visible", "target_locator": "text=Ihlamur", "expected_result": "Ihlamur ürünü ekranda listelenir"}
                    ],
                    "expected_result": "İlgili şifalı bitki ürün kartı başarıyla filtrelenir"
                }
            )
            tc_h2 = TestCase(
                project_id=hastat.id,
                code_identifier="TC-HASTAT-002",
                title="Kategori Filtreleme Doğrulaması",
                objective="Kuruyemiş veya Şifalı Bitkiler kategorisi seçildiğinde doğru ürün grubunun gösterilmesi.",
                category="smoke",
                priority="high",
                risk_level="low",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.95,
                provenance="observed",
                latest_spec={
                    "preconditions": ["Katalog ekranı aktif"],
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://ibrahimbalta.github.io/hastat/", "expected_result": "Anasayfa açılır"},
                        {"step_number": 2, "action_type": "click", "target_locator": "button:has-text('Kuruyemiş'), nav a:has-text('Kuruyemiş')", "expected_result": "Kategoriye tıklanır"},
                        {"step_number": 3, "action_type": "assert_visible", "target_locator": "text=Fındık, text=Badem, text=Kavrum", "expected_result": "Kuruyemiş ürünleri listelenir"}
                    ],
                    "expected_result": "Filtrelenen kategori ürünleri eksiksiz gösterilir"
                }
            )
            tc_h3 = TestCase(
                project_id=hastat.id,
                code_identifier="TC-HASTAT-003",
                title="Geçersiz Ürün Arama Negatif Testi",
                objective="Veritabanında bulunmayan bir terim arandığında uygulamanın hata vermeden boş durum bildirmesi.",
                category="negative",
                priority="medium",
                risk_level="medium",
                automation_status="automated",
                approval_status="approved",
                current_version=1,
                ai_confidence_score=0.94,
                provenance="ai_inferred",
                latest_spec={
                    "preconditions": ["HAS-TAT arama çubuğu görünür olmalı"],
                    "steps": [
                        {"step_number": 1, "action_type": "goto", "target_locator": "https://ibrahimbalta.github.io/hastat/", "expected_result": "Sayfa açılır"},
                        {"step_number": 2, "action_type": "fill", "target_locator": "input[type='text'], input[placeholder*='ara' i]", "input_value": "asdfghjkl999", "expected_result": "Anlamsız kelime yazılır"},
                        {"step_number": 3, "action_type": "assert_visible", "target_locator": "body", "expected_result": "Sayfa çökmez, boş sonuç güvenle işlenir"}
                    ],
                    "expected_result": "Sayfa stabil kalır, JavaScript istisnası fırlatılmaz"
                }
            )
            session.add_all([tc_h1, tc_h2, tc_h3])
            await session.flush()

            # Test Suite for HAS-TAT
            h_suite = TestSuite(
                project_id=hastat.id,
                name="HAS-TAT E2E Regresyon Paketi",
                description="HAS-TAT web sitesinin vitrin, arama ve gezinme akışlarını denetleyen tam otomasyon paketi.",
                category="smoke"
            )
            h_suite.test_cases.extend([tc_h1, tc_h2, tc_h3])
            session.add(h_suite)

            # Test Run for HAS-TAT
            h_run = TestRun(
                project_id=hastat.id,
                organization_id=org.id,
                trigger="manual",
                status="completed",
                passed_cases=26,
                failed_cases=0,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_ms=4210
            )
            session.add(h_run)
            await session.flush()

            for idx, tc_item in enumerate([tc_h1, tc_h2, tc_h3], 1):
                res_item = TestResult(
                    test_run_id=h_run.id,
                    test_case_id=tc_item.id,
                    status="passed",
                    duration_ms=1300 + (idx * 150)
                )
                session.add(res_item)
                await session.flush()

                s1 = TestStep(test_result_id=res_item.id, step_number=1, action_type="goto", target_locator="https://ibrahimbalta.github.io/hastat/", status="passed", duration_ms=800)
                s2 = TestStep(test_result_id=res_item.id, step_number=2, action_type="fill", target_locator="input[type='text']", status="passed", duration_ms=250)
                s3 = TestStep(test_result_id=res_item.id, step_number=3, action_type="assert_visible", target_locator="text=Ihlamur", status="passed", duration_ms=250)
                session.add_all([s1, s2, s3])

            await session.commit()

        # 10. Create Project: SeramikBak
        seramik_res = await session.execute(
            select(Project).where(Project.organization_id == org.id, Project.target_url.ilike("%seramikbak%"))
        )
        seramik = seramik_res.scalar_one_or_none()
        if not seramik:
            print("Creating Project: SeramikBak ...")
            seramik = Project(
                organization_id=org.id,
                name="SeramikBak",
                description="Türkiye'nin Seramik Arama Motoru, 3D Mekân ve Bayi Ağı Web Platformu",
                target_url="https://www.seramikbak.com/",
                github_repo="https://github.com/ibrahimbalta/seramikbak",
                environment="production",
                status="active"
            )
            session.add(seramik)
            await session.flush()

        seramik_tc_check = await session.execute(
            select(TestCase).where(TestCase.project_id == seramik.id)
        )
        if not seramik_tc_check.scalars().first():
            print("Seeding SeramikBak Scans, Test Cases and Suites ...")
            seramik_scan = ProjectScan(
                project_id=seramik.id,
                scan_type="url_crawler",
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                summary={"pages_discovered": 3, "forms_detected": 1}
            )
            session.add(seramik_scan)
            await session.flush()

            sp1 = DiscoveredPage(
                scan_id=seramik_scan.id,
                project_id=seramik.id,
                url="https://www.seramikbak.com/",
                path="/",
                http_status=200,
                title="SeramikBak | Türkiye'nin Seramik Arama Motoru, 3D Mekân ve Bayi Ağı",
                forms_detected=[{
                    "form_id": "search-form",
                    "action": "/arama",
                    "method": "GET",
                    "fields": [{"name": "q", "type": "text", "required": False, "recommended_locator": "input[type='text'], input[placeholder*='ara' i]"}],
                    "inputs": [{"name": "q", "type": "text", "required": False, "recommended_locator": "input[type='text'], input[placeholder*='ara' i]"}],
                    "buttons": [{"text": "Ara", "type": "submit"}]
                }],
                accessibility_tree={"role": "main", "name": "SeramikBak Arama ve Keşif"},
                provenance="observed"
            )
            sp2 = DiscoveredPage(
                scan_id=seramik_scan.id,
                project_id=seramik.id,
                url="https://www.seramikbak.com/bayiler",
                path="/bayiler",
                http_status=200,
                title="Türkiye Çapında Yetkili Seramik Bayileri — SeramikBak",
                forms_detected=[],
                accessibility_tree={"role": "region", "name": "Bayi Listesi"},
                provenance="observed"
            )
            session.add_all([sp1, sp2])

            SERAMIK_CASES_SPEC = [
                ("TC-SERAMIK-001", "Ana sayfa hero alanı, arama motoru çubuğu ve vitrin başlıklarını doğrula", "smoke", "critical", "https://www.seramikbak.com/"),
                ("TC-SERAMIK-002", "Katalog modülü (/katalog) ürün ızgarası ve listeleme kontrolü", "functional", "high", "https://www.seramikbak.com/katalog"),
                ("TC-SERAMIK-003", "Kategori filtreleme (/kategori) mekanizmasını doğrula", "functional", "high", "https://www.seramikbak.com/kategori"),
                ("TC-SERAMIK-004", "Üretici marka rehberi (/marka) sayfalarının erişilebilirliği", "functional", "medium", "https://www.seramikbak.com/marka"),
                ("TC-SERAMIK-005", "Ürün detay sayfası (/urun) teknik özellikler ve ebat kontrolü", "functional", "high", "https://www.seramikbak.com/urun"),
                ("TC-SERAMIK-006", "Outlet ve fırsat seramikleri (/outlet) vitrin kontrolü", "functional", "medium", "https://www.seramikbak.com/outlet"),
                ("TC-SERAMIK-007", "3D Mekân Simülasyonu (/mekan-dene) motorunun yüklenmesi", "functional", "critical", "https://www.seramikbak.com/mekan-dene"),
                ("TC-SERAMIK-008", "Mekânımda Gör (/mekanimda-gor) AR kamera & fotoğraf yükleme alanı", "functional", "high", "https://www.seramikbak.com/mekanimda-gor"),
                ("TC-SERAMIK-009", "Kombinasyon ve Tasarım Aracı (/tasarim) bileşen kontrolü", "functional", "medium", "https://www.seramikbak.com/tasarim"),
                ("TC-SERAMIK-010", "Fiyat Teklifi Formu (/teklif-al) boş form validasyon kontrolü", "negative", "high", "https://www.seramikbak.com/teklif-al"),
                ("TC-SERAMIK-011", "Toplu Proje Talebi (/proje-talep) mimari ve müteahhit form kontrolü", "functional", "high", "https://www.seramikbak.com/proje-talep"),
                ("TC-SERAMIK-012", "İletişim Formu (/iletisim) ve şirket adres/harita doğrulaması", "smoke", "medium", "https://www.seramikbak.com/iletisim"),
                ("TC-SERAMIK-013", "Yetkili Bayi Rehberi (/bayiler) şehir ve ilçe filtre kontrolü", "functional", "high", "https://www.seramikbak.com/bayiler"),
                ("TC-SERAMIK-014", "Bayi kartlarında telefon ve WhatsApp yönlendirme butonları kontrolü", "functional", "medium", "https://www.seramikbak.com/bayiler"),
                ("TC-SERAMIK-015", "Usta Rehberi (/ustalar) onaylı seramik döşeme ustaları listesi", "functional", "high", "https://www.seramikbak.com/ustalar"),
                ("TC-SERAMIK-016", "Mimar Portalı (/mimar) CAD/BIM doküman ve numune talep akışı", "functional", "medium", "https://www.seramikbak.com/mimar"),
                ("TC-SERAMIK-017", "Mağaza Dokunmatik Kiosk Modu (/kiosk) tam ekran arayüz kontrolü", "smoke", "medium", "https://www.seramikbak.com/kiosk"),
                ("TC-SERAMIK-018", "Yapay Zeka Asistanı (/yapay-zeka) görsel seramik arama arayüzü", "functional", "high", "https://www.seramikbak.com/yapay-zeka"),
                ("TC-SERAMIK-019", "Trendler ve Keşif (/kesfet) küratörlü koleksiyon kontrolü", "smoke", "low", "https://www.seramikbak.com/kesfet"),
                ("TC-SERAMIK-020", "İlham Galerisi (/ilham) mimari uygulama fotoğrafları kontrolü", "smoke", "low", "https://www.seramikbak.com/ilham"),
                ("TC-SERAMIK-021", "Kullanıcı Girişi (/uyelik) geçersiz parola ile hata bildirimi", "negative", "high", "https://www.seramikbak.com/uyelik"),
                ("TC-SERAMIK-022", "Bayi B2B Portalı Giriş Koruması (/bayi)", "functional", "high", "https://www.seramikbak.com/bayi"),
                ("TC-SERAMIK-023", "Sistem Yönetim Konsolu (/admin) koruma katmanı kontrolü", "functional", "critical", "https://www.seramikbak.com/admin"),
                ("TC-SERAMIK-024", "Hakkımızda sayfası (/hakkimizda) vizyon ve şirket bilgileri kontrolü", "smoke", "low", "https://www.seramikbak.com/hakkimizda"),
                ("TC-SERAMIK-025", "KVKK ve Yasal Şartlar (/yasal) aydınlatma metni kontrolü", "smoke", "low", "https://www.seramikbak.com/yasal"),
                ("TC-SERAMIK-026", "Mobil Görünüm (375x667) mobil menü açılışı ve dokunmatik navigasyon", "functional", "high", "https://www.seramikbak.com/")
            ]

            all_seramik_cases = []
            for code, title, cat, prio, target in SERAMIK_CASES_SPEC:
                tc_obj = TestCase(
                    project_id=seramik.id,
                    code_identifier=code,
                    title=title,
                    objective=f"{title} - E2E otomatik kalite güvence testi.",
                    category=cat,
                    priority=prio,
                    risk_level="medium",
                    automation_status="automated",
                    approval_status="approved",
                    current_version=1,
                    ai_confidence_score=0.96,
                    provenance="observed",
                    latest_spec={
                        "preconditions": ["Aktif internet bağlantısı", "Vercel barındırma sunucusu aktif"],
                        "steps": [
                            {"step_number": 1, "action_type": "goto", "target_locator": target, "expected_result": "Hedef sayfa açılır"},
                            {"step_number": 2, "action_type": "assert_visible", "target_locator": "body", "expected_result": "Sayfa DOM öğeleri render edilir"}
                        ],
                        "expected_result": "Test senaryosu başarıyla tamamlanır"
                    }
                )
                all_seramik_cases.append(tc_obj)
            session.add_all(all_seramik_cases)
            await session.flush()

            s_suite = TestSuite(
                project_id=seramik.id,
                name="SeramikBak E2E Regresyon Paketi",
                description="SeramikBak platformunun vitrin, arama motoru ve bayi ağı akışlarını denetleyen tam otomasyon paketi.",
                category="smoke"
            )
            s_suite.test_cases.extend(all_seramik_cases)
            session.add(s_suite)

            s_run = TestRun(
                project_id=seramik.id,
                organization_id=org.id,
                trigger="manual",
                status="completed",
                passed_cases=26,
                failed_cases=0,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_ms=25418
            )
            session.add(s_run)
            await session.flush()

            for idx, tc_s_item in enumerate(all_seramik_cases, 1):
                res_s_item = TestResult(
                    test_run_id=s_run.id,
                    test_case_id=tc_s_item.id,
                    status="passed",
                    duration_ms=4000 + (idx * 500)
                )
                session.add(res_s_item)
                await session.flush()

                st1 = TestStep(test_result_id=res_s_item.id, step_number=1, action_type="goto", target_locator="https://www.seramikbak.com/", status="passed", duration_ms=2500)
                st2 = TestStep(test_result_id=res_s_item.id, step_number=2, action_type="assert_visible", target_locator="body", status="passed", duration_ms=800)
                session.add_all([st1, st2])

            await session.commit()
            print("SeramikBak demo data seeded successfully!")

        print("All projects seeded successfully!")
        print(f"Project ID: {project.id}")
        print(f"User: architect@acme-qa.com / SecurePass123!")
        print("Now launch the web app with 'npm run dev' to explore!")

if __name__ == "__main__":
    asyncio.run(seed())
