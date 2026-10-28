import pytest
from services.api.app.core.ssrf import validate_target_url

def test_ssrf_loopback_blocked():
    blocked_urls = [
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.2:80",
        "https://127.1.1.1/secret",
        "http://[::1]/admin"
    ]
    for url in blocked_urls:
        valid, msg = validate_target_url(url, allow_private_dev=False)
        assert not valid, f"Expected {url} to be blocked by SSRF filter, but passed. Message: {msg}"

def test_ssrf_cloud_metadata_blocked():
    metadata_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/"
    ]
    for url in metadata_urls:
        valid, msg = validate_target_url(url)
        assert not valid, f"Expected metadata URL {url} to be blocked, but passed."

def test_ssrf_scheme_restrictions():
    bad_scheme_urls = [
        "file:///etc/passwd",
        "ftp://ftp.example.com",
        "gopher://example.com",
        "data:text/html,<h1>PWN</h1>"
    ]
    for url in bad_scheme_urls:
        valid, msg = validate_target_url(url)
        assert not valid
        assert "scheme" in msg.lower() or "invalid" in msg.lower()

def test_ssrf_legitimate_url_allowed():
    # Public domain names should validate properly
    valid, msg = validate_target_url("https://example.com")
    assert valid, f"Expected example.com to pass, got: {msg}"
