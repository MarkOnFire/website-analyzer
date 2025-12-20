"""Security Audit analyzer plugin.

Performs comprehensive security analysis including HTTPS/mixed content, security
headers, cookie flags, exposed files, information disclosure, third-party scripts,
and SRI verification.
"""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, Comment
from pydantic import BaseModel

from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin, PageData


class SecurityFinding(BaseModel):
    """Represents a single security issue or recommendation."""

    category: str
    finding: str
    severity: str  # high, medium, low
    affected_urls: List[str] = []
    recommendation: str = ""
    owasp_category: Optional[str] = None
    details: Optional[str] = None


class SecurityAudit(TestPlugin):
    """Plugin for comprehensive security analysis."""

    name: str = "security-audit"
    description: str = "Performs comprehensive security analysis including HTTPS, headers, cookies, and more"

    # Security header best practices
    REQUIRED_SECURITY_HEADERS = {
        "strict-transport-security": "Strict-Transport-Security",
        "content-security-policy": "Content-Security-Policy",
        "x-frame-options": "X-Frame-Options",
        "x-content-type-options": "X-Content-Type-Options",
        "x-xss-protection": "X-XSS-Protection",
        "referrer-policy": "Referrer-Policy",
        "permissions-policy": "Permissions-Policy",
    }

    # Sensitive file patterns to check
    SENSITIVE_PATHS = [
        "/.git",
        "/.env",
        "/.env.local",
        "/.env.production",
        "/admin",
        "/phpmyadmin",
        "/.htaccess",
        "/.htpasswd",
        "/config.php",
        "/wp-config.php",
        "/database.yml",
        "/backup",
        "/db",
        "/.DS_Store",
        "/composer.json",
        "/package.json",
        "/.svn",
    ]

    # OWASP Top 10 mappings
    OWASP_MAPPINGS = {
        "mixed_content": "A05:2021 – Security Misconfiguration",
        "missing_security_headers": "A05:2021 – Security Misconfiguration",
        "insecure_cookies": "A05:2021 – Security Misconfiguration",
        "exposed_files": "A01:2021 – Broken Access Control",
        "information_disclosure": "A04:2021 – Insecure Design",
        "third_party_scripts": "A08:2021 – Software and Data Integrity Failures",
        "missing_sri": "A08:2021 – Software and Data Integrity Failures",
        "weak_csp": "A03:2021 – Injection",
    }

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        """Analyze site for security issues.

        Args:
            snapshot: The SiteSnapshot object containing the website data.
            **kwargs: Configuration parameters.

        Returns:
            TestResult with security audit findings.
        """
        findings: List[SecurityFinding] = []

        # Run all security checks
        self._check_https_mixed_content(snapshot, findings)
        self._check_security_headers(snapshot, findings)
        self._check_cookie_security(snapshot, findings)
        self._check_exposed_files(snapshot, findings)
        self._check_information_disclosure(snapshot, findings)
        self._check_third_party_scripts(snapshot, findings)
        self._check_sri_hashes(snapshot, findings)

        # Classify findings by severity
        high_severity = [f for f in findings if f.severity == "high"]
        medium_severity = [f for f in findings if f.severity == "medium"]
        low_severity = [f for f in findings if f.severity == "low"]

        # Generate summary
        summary = self._generate_summary(
            len(snapshot.pages), len(high_severity), len(medium_severity), len(low_severity)
        )

        # Determine overall status
        if high_severity:
            status = "fail"
        elif medium_severity:
            status = "warning"
        else:
            status = "pass"

        return TestResult(
            plugin_name=self.name,
            status=status,
            summary=summary,
            details={
                "pages_analyzed": len(snapshot.pages),
                "high_severity": [f.model_dump() for f in high_severity],
                "medium_severity": [f.model_dump() for f in medium_severity],
                "low_severity": [f.model_dump() for f in low_severity],
                "total_findings": len(findings),
                "findings_by_category": self._categorize_findings(findings),
            },
        )

    def _check_https_mixed_content(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check for HTTPS usage and mixed content."""
        http_pages = []
        mixed_content_pages = []

        for page in snapshot.pages:
            try:
                parsed_url = urlparse(page.url)

                # Check if page is loaded over HTTP
                if parsed_url.scheme == "http":
                    http_pages.append(page.url)
                    continue

                # Check for mixed content on HTTPS pages
                if parsed_url.scheme == "https":
                    soup = BeautifulSoup(page.get_content(), "html.parser")
                    mixed_resources = []

                    # Check scripts
                    for script in soup.find_all("script", src=True):
                        src = script.get("src", "")
                        if src.startswith("http://"):
                            mixed_resources.append(("script", src))

                    # Check stylesheets
                    for link in soup.find_all("link", rel="stylesheet", href=True):
                        href = link.get("href", "")
                        if href.startswith("http://"):
                            mixed_resources.append(("stylesheet", href))

                    # Check images
                    for img in soup.find_all("img", src=True):
                        src = img.get("src", "")
                        if src.startswith("http://"):
                            mixed_resources.append(("image", src))

                    if mixed_resources:
                        mixed_content_pages.append((page.url, mixed_resources))

            except Exception:
                continue

        # Report findings
        if http_pages:
            findings.append(
                SecurityFinding(
                    category="HTTPS",
                    finding=f"{len(http_pages)} pages served over HTTP instead of HTTPS",
                    severity="high",
                    affected_urls=http_pages[:10],
                    recommendation="Enable HTTPS for all pages. Configure automatic HTTP to HTTPS redirects.",
                    owasp_category=self.OWASP_MAPPINGS["mixed_content"],
                    details="Unencrypted traffic can be intercepted and modified by attackers.",
                )
            )

        if mixed_content_pages:
            affected = [url for url, _ in mixed_content_pages[:10]]
            findings.append(
                SecurityFinding(
                    category="Mixed Content",
                    finding=f"{len(mixed_content_pages)} HTTPS pages load resources over HTTP",
                    severity="high",
                    affected_urls=affected,
                    recommendation="Update all resource URLs to use HTTPS or protocol-relative URLs (//example.com/resource).",
                    owasp_category=self.OWASP_MAPPINGS["mixed_content"],
                    details="Mixed content exposes users to man-in-the-middle attacks and may be blocked by browsers.",
                )
            )

    def _check_security_headers(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check for presence and quality of security headers."""
        missing_headers = defaultdict(list)
        weak_csp = []
        weak_hsts = []

        for page in snapshot.pages:
            try:
                headers = page.headers or {}
                # Normalize header names to lowercase
                headers_lower = {k.lower(): v for k, v in headers.items()}

                # Check for missing security headers
                for header_key, header_name in self.REQUIRED_SECURITY_HEADERS.items():
                    if header_key not in headers_lower:
                        missing_headers[header_name].append(page.url)

                # Check CSP strength
                csp = headers_lower.get("content-security-policy", "")
                if csp:
                    # Check for unsafe-inline or unsafe-eval
                    if "unsafe-inline" in csp or "unsafe-eval" in csp:
                        weak_csp.append(page.url)
                    # Check if CSP is too permissive (uses *)
                    elif "*" in csp and "default-src" in csp:
                        weak_csp.append(page.url)

                # Check HSTS strength
                hsts = headers_lower.get("strict-transport-security", "")
                if hsts:
                    # Check max-age is sufficient (at least 1 year = 31536000 seconds)
                    max_age_match = re.search(r"max-age=(\d+)", hsts)
                    if max_age_match:
                        max_age = int(max_age_match.group(1))
                        if max_age < 31536000:  # Less than 1 year
                            weak_hsts.append(page.url)
                    # Check for includeSubDomains
                    if "includesubdomains" not in hsts.lower():
                        weak_hsts.append(page.url)

            except Exception:
                continue

        # Report findings
        for header_name, affected_urls in missing_headers.items():
            severity = "high" if header_name in ["Strict-Transport-Security", "Content-Security-Policy"] else "medium"

            recommendation = self._get_header_recommendation(header_name)

            findings.append(
                SecurityFinding(
                    category="Security Headers",
                    finding=f"Missing {header_name} header on {len(affected_urls)} page(s)",
                    severity=severity,
                    affected_urls=affected_urls[:10],
                    recommendation=recommendation,
                    owasp_category=self.OWASP_MAPPINGS["missing_security_headers"],
                )
            )

        if weak_csp:
            findings.append(
                SecurityFinding(
                    category="Security Headers",
                    finding=f"{len(weak_csp)} pages have weak Content-Security-Policy (uses 'unsafe-inline', 'unsafe-eval', or overly permissive '*')",
                    severity="medium",
                    affected_urls=weak_csp[:10],
                    recommendation="Remove 'unsafe-inline' and 'unsafe-eval' directives. Use nonces or hashes for inline scripts. Avoid wildcard (*) in default-src.",
                    owasp_category=self.OWASP_MAPPINGS["weak_csp"],
                    details="Weak CSP provides limited protection against XSS attacks.",
                )
            )

        if weak_hsts:
            findings.append(
                SecurityFinding(
                    category="Security Headers",
                    finding=f"{len(weak_hsts)} pages have weak HSTS configuration",
                    severity="medium",
                    affected_urls=weak_hsts[:10],
                    recommendation="Set HSTS max-age to at least 31536000 (1 year) and include 'includeSubDomains' directive.",
                    owasp_category=self.OWASP_MAPPINGS["missing_security_headers"],
                    details="Example: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
                )
            )

    def _check_cookie_security(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check cookie security flags."""
        # Note: Cookie data would need to be in page metadata from browser inspection
        # For this implementation, we'll check if Set-Cookie headers are present
        insecure_cookies = []

        for page in snapshot.pages:
            try:
                headers = page.headers or {}
                set_cookie = headers.get("Set-Cookie") or headers.get("set-cookie", "")

                if set_cookie:
                    # Check for missing Secure flag
                    if "Secure" not in set_cookie and urlparse(page.url).scheme == "https":
                        insecure_cookies.append((page.url, "missing Secure flag"))

                    # Check for missing HttpOnly flag
                    if "HttpOnly" not in set_cookie:
                        insecure_cookies.append((page.url, "missing HttpOnly flag"))

                    # Check for missing SameSite
                    if "SameSite" not in set_cookie:
                        insecure_cookies.append((page.url, "missing SameSite attribute"))

            except Exception:
                continue

        if insecure_cookies:
            affected = list(set(url for url, _ in insecure_cookies[:10]))
            findings.append(
                SecurityFinding(
                    category="Cookie Security",
                    finding=f"Found {len(insecure_cookies)} cookie security issue(s) across {len(affected)} page(s)",
                    severity="medium",
                    affected_urls=affected,
                    recommendation="Set Secure, HttpOnly, and SameSite attributes on all cookies. Example: Set-Cookie: session=xyz; Secure; HttpOnly; SameSite=Strict",
                    owasp_category=self.OWASP_MAPPINGS["insecure_cookies"],
                    details="Insecure cookies can be intercepted or accessed by malicious scripts.",
                )
            )

    def _check_exposed_files(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check for exposed sensitive files."""
        exposed_files = []

        for page in snapshot.pages:
            try:
                parsed = urlparse(page.url)
                path = parsed.path

                # Check if page URL matches sensitive patterns
                for sensitive_path in self.SENSITIVE_PATHS:
                    if sensitive_path in path:
                        # Check if page was successfully crawled (not 404)
                        if page.status_code == 200:
                            exposed_files.append((page.url, sensitive_path))

            except Exception:
                continue

        if exposed_files:
            affected = [url for url, _ in exposed_files[:10]]
            exposed_paths = list(set(path for _, path in exposed_files))

            findings.append(
                SecurityFinding(
                    category="Exposed Files",
                    finding=f"Found {len(exposed_files)} potentially sensitive file(s) or directory/directories accessible: {', '.join(exposed_paths[:5])}",
                    severity="high",
                    affected_urls=affected,
                    recommendation="Block access to sensitive files and directories using .htaccess, nginx configuration, or firewall rules. Remove files that should not be publicly accessible.",
                    owasp_category=self.OWASP_MAPPINGS["exposed_files"],
                    details="Exposed configuration files, version control directories, or admin panels can leak sensitive information.",
                )
            )

    def _check_information_disclosure(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check for information disclosure in HTML comments and error messages."""
        pages_with_comments = []
        pages_with_errors = []

        # Patterns for sensitive information
        sensitive_patterns = [
            r"password",
            r"api[_-]?key",
            r"secret",
            r"token",
            r"TODO|FIXME|HACK",
            r"admin",
            r"debug",
        ]

        error_patterns = [
            r"stack trace",
            r"exception",
            r"error in",
            r"warning:",
            r"fatal error",
            r"syntax error",
            r"mysql",
            r"postgresql",
            r"ora-\d+",  # Oracle errors
        ]

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")

                # Check HTML comments
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_text = comment.lower()
                    for pattern in sensitive_patterns:
                        if re.search(pattern, comment_text, re.IGNORECASE):
                            pages_with_comments.append(page.url)
                            break

                # Check for error messages in visible content
                page_text = soup.get_text().lower()
                for pattern in error_patterns:
                    if re.search(pattern, page_text, re.IGNORECASE):
                        pages_with_errors.append(page.url)
                        break

            except Exception:
                continue

        if pages_with_comments:
            findings.append(
                SecurityFinding(
                    category="Information Disclosure",
                    finding=f"{len(set(pages_with_comments))} page(s) contain HTML comments with potentially sensitive information",
                    severity="low",
                    affected_urls=list(set(pages_with_comments))[:10],
                    recommendation="Remove or sanitize HTML comments that contain sensitive information, TODOs, or implementation details before deploying to production.",
                    owasp_category=self.OWASP_MAPPINGS["information_disclosure"],
                )
            )

        if pages_with_errors:
            findings.append(
                SecurityFinding(
                    category="Information Disclosure",
                    finding=f"{len(set(pages_with_errors))} page(s) contain error messages or stack traces",
                    severity="medium",
                    affected_urls=list(set(pages_with_errors))[:10],
                    recommendation="Configure error handling to show generic error pages to users. Log detailed errors server-side only.",
                    owasp_category=self.OWASP_MAPPINGS["information_disclosure"],
                    details="Error messages can reveal system architecture, file paths, and database schema.",
                )
            )

    def _check_third_party_scripts(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Audit third-party script sources."""
        third_party_domains = Counter()
        pages_with_third_party = []

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")
                page_domain = urlparse(page.url).netloc
                has_third_party = False

                for script in soup.find_all("script", src=True):
                    src = script.get("src", "")

                    # Parse script URL
                    if src.startswith("http://") or src.startswith("https://"):
                        script_domain = urlparse(src).netloc

                        # Check if it's a third-party domain
                        if script_domain and script_domain != page_domain:
                            third_party_domains[script_domain] += 1
                            has_third_party = True

                if has_third_party:
                    pages_with_third_party.append(page.url)

            except Exception:
                continue

        if third_party_domains:
            top_domains = [domain for domain, _ in third_party_domains.most_common(10)]

            findings.append(
                SecurityFinding(
                    category="Third-Party Scripts",
                    finding=f"Found {len(third_party_domains)} third-party script domain(s) on {len(pages_with_third_party)} page(s)",
                    severity="low",
                    affected_urls=pages_with_third_party[:10],
                    recommendation=f"Audit third-party scripts for necessity and trustworthiness. Top domains: {', '.join(top_domains[:5])}. Consider using CSP to restrict script sources.",
                    owasp_category=self.OWASP_MAPPINGS["third_party_scripts"],
                    details="Third-party scripts execute with full page privileges and can access sensitive data.",
                )
            )

    def _check_sri_hashes(self, snapshot: SiteSnapshot, findings: List[SecurityFinding]) -> None:
        """Check for Subresource Integrity hashes on external resources."""
        resources_without_sri = []

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")
                page_domain = urlparse(page.url).netloc

                # Check scripts
                for script in soup.find_all("script", src=True):
                    src = script.get("src", "")

                    # Only check external scripts
                    if src.startswith("http://") or src.startswith("https://"):
                        script_domain = urlparse(src).netloc
                        if script_domain and script_domain != page_domain:
                            # Check for integrity attribute
                            if not script.get("integrity"):
                                resources_without_sri.append((page.url, "script", src))

                # Check stylesheets
                for link in soup.find_all("link", rel="stylesheet", href=True):
                    href = link.get("href", "")

                    # Only check external stylesheets
                    if href.startswith("http://") or href.startswith("https://"):
                        link_domain = urlparse(href).netloc
                        if link_domain and link_domain != page_domain:
                            # Check for integrity attribute
                            if not link.get("integrity"):
                                resources_without_sri.append((page.url, "stylesheet", href))

            except Exception:
                continue

        if resources_without_sri:
            affected = list(set(url for url, _, _ in resources_without_sri[:10]))

            findings.append(
                SecurityFinding(
                    category="Subresource Integrity",
                    finding=f"{len(resources_without_sri)} external resource(s) loaded without SRI hashes",
                    severity="medium",
                    affected_urls=affected,
                    recommendation="Add integrity attributes to external scripts and stylesheets. Example: <script src='https://cdn.example.com/lib.js' integrity='sha384-...' crossorigin='anonymous'>",
                    owasp_category=self.OWASP_MAPPINGS["missing_sri"],
                    details="SRI ensures that resources haven't been tampered with. Generate hashes using tools like https://www.srihash.org/",
                )
            )

    def _get_header_recommendation(self, header_name: str) -> str:
        """Get specific recommendation for missing header."""
        recommendations = {
            "Strict-Transport-Security": "Add HSTS header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
            "Content-Security-Policy": "Add CSP header: Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}'; object-src 'none'",
            "X-Frame-Options": "Add X-Frame-Options: DENY or SAMEORIGIN to prevent clickjacking",
            "X-Content-Type-Options": "Add X-Content-Type-Options: nosniff to prevent MIME-type sniffing",
            "X-XSS-Protection": "Add X-XSS-Protection: 1; mode=block (legacy browsers)",
            "Referrer-Policy": "Add Referrer-Policy: strict-origin-when-cross-origin",
            "Permissions-Policy": "Add Permissions-Policy to control browser features: Permissions-Policy: geolocation=(), microphone=(), camera=()",
        }
        return recommendations.get(header_name, f"Add {header_name} header for enhanced security")

    def _categorize_findings(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Categorize findings by type."""
        category_counts = Counter(f.category for f in findings)
        return dict(category_counts)

    def _generate_summary(
        self, pages_analyzed: int, high_count: int, medium_count: int, low_count: int
    ) -> str:
        """Generate human-readable summary."""
        total_findings = high_count + medium_count + low_count

        if total_findings == 0:
            return f"Security audit complete. Analyzed {pages_analyzed} page(s). No security issues found. Excellent security posture!"

        parts = [
            f"Security audit complete. Analyzed {pages_analyzed} page(s).",
            f"Found {total_findings} security finding(s): {high_count} high severity, {medium_count} medium severity, {low_count} low severity.",
        ]

        if high_count > 0:
            parts.append("Address high severity issues immediately to reduce security risks.")
        elif medium_count > 0:
            parts.append("Fix medium severity issues to improve security posture.")
        else:
            parts.append("Address low severity findings for security best practices.")

        return " ".join(parts)
