import os
import sys
import time
from urllib.parse import urljoin

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_URL = "https://www.seramikbak.com"

ROUTES_TO_TEST = [
    {"path": "/", "name": "Ana Sayfa / Vitrin", "critical": True},
    {"path": "/katalog", "name": "Ürün Kataloğu", "critical": True},
    {"path": "/kategori", "name": "Kategori Filtreleme", "critical": False},
    {"path": "/marka", "name": "Üretici Markalar", "critical": False},
    {"path": "/mekan-dene", "name": "3D Mekân Simülasyonu", "critical": True},
    {"path": "/mekanimda-gor", "name": "Mekânımda Gör (AR)", "critical": False},
    {"path": "/tasarim", "name": "Tasarım & Kombinasyon", "critical": False},
    {"path": "/teklif-al", "name": "Fiyat Teklif Formu", "critical": True},
    {"path": "/proje-talep", "name": "Toplu Proje Talebi", "critical": False},
    {"path": "/bayiler", "name": "Yetkili Bayi Ağı", "critical": True},
    {"path": "/ustalar", "name": "Seramik Ustaları", "critical": False},
    {"path": "/mimar", "name": "Mimar Portalı", "critical": False},
    {"path": "/kiosk", "name": "Mağaza Kiosk Modu", "critical": False},
    {"path": "/yapay-zeka", "name": "AI Görsel Arama", "critical": False},
    {"path": "/kesfet", "name": "Trendler & Keşif", "critical": False},
    {"path": "/ilham", "name": "İlham Galerisi", "critical": False},
    {"path": "/uyelik", "name": "Kullanıcı Girişi & Kayıt", "critical": True},
    {"path": "/bayi", "name": "B2B Bayi Girişi", "critical": True},
    {"path": "/hakkimizda", "name": "Hakkımızda", "critical": False},
    {"path": "/iletisim", "name": "İletişim", "critical": True},
    {"path": "/yasal", "name": "KVKK & Yasal Şartlar", "critical": False},
]

def run_suite():
    print("=" * 70)
    print("🚀 MasterQA Kapsamlı SeramikBak E2E Test Koşumu Başlatılıyor")
    print(f"🌐 Hedef Platform: {BASE_URL}")
    print(f"📊 Test Edilecek Rota Sayısı: {len(ROUTES_TO_TEST)} modül")
    print("=" * 70)

    results = []
    start_total = time.time()

    with sync_playwright() as p:
        print("\n[1/3] Chromium Motoru Başlatılıyor...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) MasterQA-Enterprise-Bot/2.0"
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("\n[2/3] Tüm Sayfalar ve Modüller Tek Tek Taranıyor...\n")

        for idx, route in enumerate(ROUTES_TO_TEST, 1):
            url = urljoin(BASE_URL, route["path"])
            t0 = time.time()
            try:
                resp = page.goto(url, wait_until="load", timeout=20000)
                dur = int((time.time() - t0) * 1000)
                status = resp.status if resp else "N/A"
                passed = status in [200, 301, 302, 308]
                results.append({
                    "id": f"TC-SERAMIK-{idx:03d}",
                    "name": route["name"],
                    "path": route["path"],
                    "status_code": status,
                    "duration_ms": dur,
                    "passed": passed
                })
                icon = "✅" if passed else "❌"
                print(f"  {icon} [{idx:02d}/{len(ROUTES_TO_TEST)}] {route['name']:<28} {route['path']:<18} ({status}) - {dur}ms")
            except Exception as e:
                dur = int((time.time() - t0) * 1000)
                results.append({
                    "id": f"TC-SERAMIK-{idx:03d}",
                    "name": route["name"],
                    "path": route["path"],
                    "status_code": "ERR",
                    "duration_ms": dur,
                    "passed": False,
                    "error": str(e)
                })
                print(f"  ⚠️ [{idx:02d}/{len(ROUTES_TO_TEST)}] {route['name']:<28} {route['path']:<18} (Hata: {str(e)[:35]}...)")

        print("\n[3/3] Mobil Uyumluluk Testi (Viewport 375x667)...")
        m_page = context.new_page()
        m_page.set_viewport_size({"width": 375, "height": 667})
        m_t0 = time.time()
        m_resp = m_page.goto(BASE_URL, wait_until="load", timeout=20000)
        m_dur = int((time.time() - m_t0) * 1000)
        m_passed = m_resp and m_resp.status == 200
        results.append({
            "id": f"TC-SERAMIK-{len(ROUTES_TO_TEST)+1:03d}",
            "name": "Mobil Düzen & Viewport",
            "path": "/",
            "status_code": m_resp.status if m_resp else "N/A",
            "duration_ms": m_dur,
            "passed": m_passed
        })
        print(f"  {'✅' if m_passed else '❌'} Mobil (iPhone SE 375x667): Durum {m_resp.status if m_resp else 'N/A'} - {m_dur}ms")

        browser.close()

    total_time = round(time.time() - start_total, 2)
    passed_cnt = sum(1 for r in results if r["passed"])
    failed_cnt = len(results) - passed_cnt

    print("\n" + "=" * 70)
    print("🏁 KOŞUM ÖZET RAPORU (SeramikBak E2E Paketi)")
    print("=" * 70)
    print(f"Toplam Senaryo Sayısı : {len(results)}")
    print(f"Başarılı (PASSED)     : {passed_cnt} ✅")
    print(f"Başarısız/Hata        : {failed_cnt} {'❌' if failed_cnt > 0 else '🎉'}")
    print(f"Toplam Test Süresi    : {total_time} saniye")
    print(f"Bulunan Konsol Hatası : {len(console_errors)}")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
