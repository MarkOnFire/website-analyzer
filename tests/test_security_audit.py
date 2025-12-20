"""Tests for Security Audit plugin."""

import pytest
from pathlib import Path
from src.analyzer.plugins.security_audit import SecurityAudit
from src.analyzer.test_plugin import SiteSnapshot, PageData


@pytest.fixture
def temp_snapshot(tmp_path: Path):
    """Create a temporary snapshot directory structure."""
    snapshot_dir = tmp_path / "test_snapshot"
    snapshot_dir.mkdir()

    # Create sitemap.json
    sitemap_path = snapshot_dir / "sitemap.json"
    sitemap_path.write_text('{"root": "https://example.com", "pages": []}')

    # Create summary.json
    summary_path = snapshot_dir / "summary.json"
    summary_path.write_text('{"total_pages": 0}')

    # Create pages directory
    pages_dir = snapshot_dir / "pages"
    pages_dir.mkdir()

    return snapshot_dir


def create_page(snapshot_dir: Path, page_id: str, url: str, html_content: str,
                status_code: int = 200, headers: dict = None):
    """Helper to create a page in the snapshot."""
    page_dir = snapshot_dir / "pages" / page_id
    page_dir.mkdir(parents=True, exist_ok=True)

    # Write metadata
    import json
    metadata = {
        "url": url,
        "status_code": status_code,
        "timestamp": "2025-01-01T00:00:00Z",
        "title": "Test Page",
        "links": [],
        "headers": headers or {},
    }
    (page_dir / "metadata.json").write_text(json.dumps(metadata))

    # Write HTML content
    (page_dir / "raw.html").write_text(html_content)
    (page_dir / "cleaned.html").write_text(html_content)
    (page_dir / "content.md").write_text("Test content")


@pytest.mark.asyncio
async def test_plugin_protocol():
    """Test that SecurityAudit implements TestPlugin protocol."""
    plugin = SecurityAudit()
    assert plugin.name == "security-audit"
    assert plugin.description
    assert hasattr(plugin, "analyze")


@pytest.mark.asyncio
async def test_https_check(temp_snapshot):
    """Test HTTPS usage detection."""
    # Create pages with HTTP URLs
    create_page(temp_snapshot, "page1", "http://example.com/page1", "<html><body>Test</body></html>")
    create_page(temp_snapshot, "page2", "http://example.com/page2", "<html><body>Test</body></html>")
    create_page(temp_snapshot, "page3", "https://example.com/page3", "<html><body>Test</body></html>")

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    assert result.plugin_name == "security-audit"
    assert result.status == "fail"  # HTTP pages found
    assert "2 pages served over HTTP" in str(result.details)


@pytest.mark.asyncio
async def test_mixed_content_detection(temp_snapshot):
    """Test mixed content detection on HTTPS pages."""
    html_with_mixed_content = """
    <html>
    <head>
        <script src="http://insecure.com/script.js"></script>
        <link rel="stylesheet" href="http://insecure.com/style.css">
    </head>
    <body>
        <img src="http://insecure.com/image.jpg">
    </body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://example.com/page1", html_with_mixed_content)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    assert result.status == "fail"
    high_severity = result.details["high_severity"]
    mixed_content_findings = [f for f in high_severity if "Mixed Content" in f["category"]]
    assert len(mixed_content_findings) > 0


@pytest.mark.asyncio
async def test_security_headers_missing(temp_snapshot):
    """Test detection of missing security headers."""
    headers = {}  # No security headers
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    # Should have findings for missing headers
    all_findings = result.details["high_severity"] + result.details["medium_severity"]
    header_findings = [f for f in all_findings if "Security Headers" in f["category"]]
    assert len(header_findings) > 0


@pytest.mark.asyncio
async def test_security_headers_present(temp_snapshot):
    """Test that good security headers don't trigger findings."""
    headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=()",
    }
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    # Should have no or few findings for security headers
    all_findings = result.details["high_severity"] + result.details["medium_severity"]
    header_findings = [f for f in all_findings if "Missing" in f["finding"] and "Security Headers" in f["category"]]
    assert len(header_findings) == 0


@pytest.mark.asyncio
async def test_weak_csp_detection(temp_snapshot):
    """Test detection of weak CSP policies."""
    headers = {
        "Content-Security-Policy": "default-src *; script-src 'unsafe-inline' 'unsafe-eval'"
    }
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    weak_csp = [f for f in medium_findings if "weak Content-Security-Policy" in f["finding"]]
    assert len(weak_csp) > 0


@pytest.mark.asyncio
async def test_weak_hsts_detection(temp_snapshot):
    """Test detection of weak HSTS configuration."""
    # HSTS with short max-age
    headers = {
        "Strict-Transport-Security": "max-age=3600"  # Only 1 hour
    }
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    weak_hsts = [f for f in medium_findings if "weak HSTS" in f["finding"]]
    assert len(weak_hsts) > 0


@pytest.mark.asyncio
async def test_cookie_security_flags(temp_snapshot):
    """Test cookie security flag detection."""
    # Cookie without security flags
    headers = {
        "Set-Cookie": "session=abc123"
    }
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    cookie_findings = [f for f in medium_findings if "Cookie Security" in f["category"]]
    assert len(cookie_findings) > 0


@pytest.mark.asyncio
async def test_exposed_files_detection(temp_snapshot):
    """Test detection of exposed sensitive files."""
    # Create pages for sensitive paths
    create_page(temp_snapshot, "git", "https://example.com/.git/config", "<html><body>Git config</body></html>", status_code=200)
    create_page(temp_snapshot, "env", "https://example.com/.env", "<html><body>ENV vars</body></html>", status_code=200)
    create_page(temp_snapshot, "admin", "https://example.com/admin/", "<html><body>Admin panel</body></html>", status_code=200)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    assert result.status == "fail"
    high_findings = result.details["high_severity"]
    exposed_findings = [f for f in high_findings if "Exposed Files" in f["category"]]
    assert len(exposed_findings) > 0
    assert "3 potentially sensitive" in exposed_findings[0]["finding"]


@pytest.mark.asyncio
async def test_information_disclosure_comments(temp_snapshot):
    """Test detection of sensitive information in HTML comments."""
    html_with_comments = """
    <html>
    <head>
        <!-- TODO: Remove hardcoded password before deploy -->
        <!-- API_KEY = secret123 -->
    </head>
    <body>
        <!-- DEBUG MODE ENABLED -->
        <p>Content</p>
    </body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://example.com/page1", html_with_comments)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    low_findings = result.details["low_severity"]
    comment_findings = [f for f in low_findings if "HTML comments" in f["finding"]]
    assert len(comment_findings) > 0


@pytest.mark.asyncio
async def test_information_disclosure_errors(temp_snapshot):
    """Test detection of error messages in page content."""
    html_with_errors = """
    <html>
    <body>
        <h1>Application Error</h1>
        <pre>
        Stack trace:
        Exception in thread "main" java.lang.NullPointerException
            at com.example.MyClass.method(MyClass.java:42)
        MySQL Error 1064: You have an error in your SQL syntax
        </pre>
    </body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://example.com/error", html_with_errors)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    error_findings = [f for f in medium_findings if "error messages or stack traces" in f["finding"]]
    assert len(error_findings) > 0


@pytest.mark.asyncio
async def test_third_party_scripts_audit(temp_snapshot):
    """Test third-party script source auditing."""
    html_with_third_party = """
    <html>
    <head>
        <script src="https://cdn.example.com/lib.js"></script>
        <script src="https://analytics.google.com/ga.js"></script>
        <script src="/local/script.js"></script>
    </head>
    <body>Test</body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://mysite.com/page1", html_with_third_party)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    low_findings = result.details["low_severity"]
    third_party_findings = [f for f in low_findings if "Third-Party Scripts" in f["category"]]
    assert len(third_party_findings) > 0
    assert "2 third-party script domain" in third_party_findings[0]["finding"]


@pytest.mark.asyncio
async def test_sri_hash_checking(temp_snapshot):
    """Test SRI hash checking for external resources."""
    html_without_sri = """
    <html>
    <head>
        <script src="https://cdn.example.com/lib.js"></script>
        <link rel="stylesheet" href="https://cdn.example.com/style.css">
        <script src="/local.js"></script>  <!-- Local, no SRI needed -->
    </head>
    <body>Test</body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://mysite.com/page1", html_without_sri)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    sri_findings = [f for f in medium_findings if "Subresource Integrity" in f["category"]]
    assert len(sri_findings) > 0
    assert "2 external resource" in sri_findings[0]["finding"]


@pytest.mark.asyncio
async def test_sri_with_integrity_attribute(temp_snapshot):
    """Test that resources with SRI don't trigger findings."""
    html_with_sri = """
    <html>
    <head>
        <script src="https://cdn.example.com/lib.js"
                integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxmFN..."
                crossorigin="anonymous"></script>
        <link rel="stylesheet" href="https://cdn.example.com/style.css"
              integrity="sha384-abc123..."
              crossorigin="anonymous">
    </head>
    <body>Test</body>
    </html>
    """
    create_page(temp_snapshot, "page1", "https://mysite.com/page1", html_with_sri)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    medium_findings = result.details["medium_severity"]
    sri_findings = [f for f in medium_findings if "Subresource Integrity" in f["category"]]
    # Should have no SRI findings since integrity attributes are present
    assert len(sri_findings) == 0


@pytest.mark.asyncio
async def test_owasp_mapping(temp_snapshot):
    """Test that findings include OWASP Top 10 mappings."""
    # Create a page with mixed content
    html = '<html><body><script src="http://insecure.com/script.js"></script></body></html>'
    create_page(temp_snapshot, "page1", "https://example.com/page1", html)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    high_findings = result.details["high_severity"]
    # All findings should have OWASP category
    for finding in high_findings:
        assert "owasp_category" in finding
        assert "A" in finding["owasp_category"]  # OWASP format: A01:2021


@pytest.mark.asyncio
async def test_severity_classification(temp_snapshot):
    """Test that findings are properly classified by severity."""
    # Create various security issues
    create_page(temp_snapshot, "http", "http://example.com/", "<html><body>Test</body></html>")  # High
    create_page(
        temp_snapshot,
        "nosri",
        "https://example.com/page",
        '<html><head><script src="https://cdn.com/lib.js"></script></head></html>',  # Medium
        headers={"Strict-Transport-Security": "max-age=31536000"}
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    assert len(result.details["high_severity"]) > 0
    assert len(result.details["medium_severity"]) > 0

    # Verify severity values
    for finding in result.details["high_severity"]:
        assert finding["severity"] == "high"

    for finding in result.details["medium_severity"]:
        assert finding["severity"] == "medium"


@pytest.mark.asyncio
async def test_hardening_recommendations(temp_snapshot):
    """Test that findings include actionable recommendations."""
    headers = {}  # Missing all security headers
    create_page(
        temp_snapshot,
        "page1",
        "https://example.com/page1",
        "<html><body>Test</body></html>",
        headers=headers
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    all_findings = (
        result.details["high_severity"] +
        result.details["medium_severity"] +
        result.details["low_severity"]
    )

    # All findings should have recommendations
    for finding in all_findings:
        assert "recommendation" in finding
        assert len(finding["recommendation"]) > 0
        # Recommendations should be actionable (contain examples or specific guidance)
        assert any(
            keyword in finding["recommendation"].lower()
            for keyword in ["add", "set", "configure", "use", "enable", "example"]
        )


@pytest.mark.asyncio
async def test_clean_site_passes(temp_snapshot):
    """Test that a secure site passes the audit."""
    headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'nonce-xyz'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=()",
        "Set-Cookie": "session=xyz; Secure; HttpOnly; SameSite=Strict",
    }

    html = """
    <html>
    <head>
        <title>Secure Page</title>
        <script src="/local.js"></script>
    </head>
    <body>
        <h1>Welcome</h1>
        <p>Clean content with no issues.</p>
        <img src="/image.jpg" alt="Description">
    </body>
    </html>
    """

    create_page(temp_snapshot, "page1", "https://example.com/", html, headers=headers)

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    # Should pass or at worst be a warning (might have some low-severity findings)
    assert result.status in ["pass", "warning"]
    assert len(result.details["high_severity"]) == 0


@pytest.mark.asyncio
async def test_summary_generation(temp_snapshot):
    """Test that summary is generated correctly."""
    create_page(temp_snapshot, "page1", "http://example.com/", "<html><body>Test</body></html>")

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    assert result.summary
    assert "Security audit complete" in result.summary
    assert "Analyzed" in result.summary
    assert "page" in result.summary


@pytest.mark.asyncio
async def test_findings_categorization(temp_snapshot):
    """Test that findings are categorized by type."""
    # Create multiple issue types
    create_page(temp_snapshot, "http", "http://example.com/", "<html><body>Test</body></html>")
    create_page(
        temp_snapshot,
        "nosri",
        "https://example.com/page",
        '<html><head><script src="https://cdn.com/lib.js"></script></head></html>'
    )

    snapshot = SiteSnapshot.load(temp_snapshot)
    plugin = SecurityAudit()
    result = await plugin.analyze(snapshot)

    category_counts = result.details["findings_by_category"]
    assert isinstance(category_counts, dict)
    assert len(category_counts) > 0
