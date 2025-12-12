"""SEO Optimization analyzer plugin.

Identifies search engine optimization opportunities across technical SEO,
content SEO, and on-page optimization.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from pydantic import BaseModel

from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin, PageData


class SeoIssue(BaseModel):
    """Represents a single SEO issue or opportunity."""

    category: str
    issue: str
    impact: str
    affected_urls: List[str] = []
    recommendation: Optional[str] = None
    severity: Optional[str] = None  # For critical_issues


class SeoFinding(BaseModel):
    """Represents detailed SEO analysis findings."""

    overall_score: float
    critical_issues: List[SeoIssue] = []
    warnings: List[SeoIssue] = []
    opportunities: List[SeoIssue] = []


class SeoOptimizer(TestPlugin):
    """Plugin for analyzing and improving SEO optimization."""

    name: str = "seo-optimizer"
    description: str = "Identifies search engine optimization opportunities"

    # Constants for scoring and thresholds
    MIN_CONTENT_LENGTH = 300  # Words
    MIN_TITLE_LENGTH = 30
    MAX_TITLE_LENGTH = 60
    MIN_META_DESC_LENGTH = 120
    MAX_META_DESC_LENGTH = 160
    OPTIMAL_H1_COUNT = 1
    REASONABLE_PAGE_WORD_COUNT = 300

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        """Analyze site for SEO opportunities.

        Args:
            snapshot: The SiteSnapshot object containing the website data.
            **kwargs: Configuration parameters (e.g., target_keywords).

        Returns:
            TestResult with SEO analysis findings.
        """
        target_keywords = kwargs.get("target_keywords", [])
        if isinstance(target_keywords, str):
            target_keywords = [kw.strip() for kw in target_keywords.split(",")]

        # Initialize tracking
        findings = {
            "pages_analyzed": len(snapshot.pages),
            "pages_with_issues": 0,
            "critical_issues": [],
            "warnings": [],
            "opportunities": [],
            "issue_counts": Counter(),
        }

        # Technical SEO checks
        self._check_meta_tags(snapshot, findings)
        self._check_heading_structure(snapshot, findings)
        self._check_image_alt_text(snapshot, findings)
        self._check_link_health(snapshot, findings)
        self._check_robots_sitemap(snapshot, findings)

        # Content SEO checks
        self._check_content_length(snapshot, findings)
        self._check_keyword_usage(snapshot, findings, target_keywords)
        self._check_internal_linking(snapshot, findings)
        self._check_duplicate_content(snapshot, findings)

        # Calculate overall score (0-10)
        overall_score = self._calculate_score(findings, len(snapshot.pages))

        summary = self._generate_summary(
            overall_score,
            len(findings["critical_issues"]),
            len(findings["warnings"]),
            len(findings["opportunities"]),
        )

        return TestResult(
            plugin_name=self.name,
            status="pass" if overall_score >= 7.0 else "warning" if overall_score >= 5.0 else "fail",
            summary=summary,
            details={
                "overall_score": overall_score,
                "critical_issues": [
                    issue.model_dump() for issue in findings["critical_issues"]
                ],
                "warnings": [issue.model_dump() for issue in findings["warnings"]],
                "opportunities": [
                    issue.model_dump() for issue in findings["opportunities"]
                ],
                "pages_analyzed": findings["pages_analyzed"],
                "issue_counts": dict(findings["issue_counts"]),
                "target_keywords": target_keywords,
            },
        )

    def _check_meta_tags(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check for missing or suboptimal meta tags."""
        pages_without_title = []
        pages_without_desc = []
        pages_with_duplicate_title = {}
        pages_with_short_title = []
        pages_with_long_title = []
        pages_with_short_desc = []
        pages_with_long_desc = []

        title_counter = Counter()

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")

                # Check title tag
                title_tag = soup.find("title")
                if not title_tag or not title_tag.string:
                    pages_without_title.append(page.url)
                    findings["issue_counts"]["missing_title"] += 1
                else:
                    title_text = title_tag.string.strip()
                    title_counter[title_text] += 1

                    if len(title_text) < self.MIN_TITLE_LENGTH:
                        pages_with_short_title.append(page.url)
                        findings["issue_counts"]["short_title"] += 1
                    elif len(title_text) > self.MAX_TITLE_LENGTH:
                        pages_with_long_title.append(page.url)
                        findings["issue_counts"]["long_title"] += 1

                # Check meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if not meta_desc or not meta_desc.get("content"):
                    pages_without_desc.append(page.url)
                    findings["issue_counts"]["missing_meta_desc"] += 1
                else:
                    desc_text = meta_desc.get("content", "").strip()
                    if len(desc_text) < self.MIN_META_DESC_LENGTH:
                        pages_with_short_desc.append(page.url)
                        findings["issue_counts"]["short_meta_desc"] += 1
                    elif len(desc_text) > self.MAX_META_DESC_LENGTH:
                        pages_with_long_desc.append(page.url)
                        findings["issue_counts"]["long_meta_desc"] += 1

            except Exception:
                continue

        # Find duplicate titles
        for title, count in title_counter.items():
            if count > 1:
                pages_with_duplicate_title[title] = count

        # Add critical issue: Missing titles
        if pages_without_title:
            findings["critical_issues"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_without_title)} pages missing title tags",
                    impact="Search engines may not index properly",
                    affected_urls=pages_without_title[:10],
                    severity="high",
                )
            )
            findings["issue_counts"]["missing_title_critical"] += 1

        # Add critical issue: Duplicate titles
        if pages_with_duplicate_title:
            total_duplicates = sum(c for c in pages_with_duplicate_title.values() if c > 1)
            findings["critical_issues"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{total_duplicates} pages with duplicate title tags",
                    impact="Search engines may not index properly",
                    affected_urls=[],
                    severity="high",
                )
            )
            findings["issue_counts"]["duplicate_titles"] += 1

        # Add warnings for suboptimal meta tags
        if pages_without_desc:
            findings["warnings"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_without_desc)} pages missing meta descriptions",
                    impact="LLMs and search engines can't generate accurate summaries",
                    affected_urls=pages_without_desc[:10],
                )
            )
            findings["issue_counts"]["missing_meta_desc_warning"] += 1

        if pages_with_short_title:
            findings["warnings"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_with_short_title)} pages have short titles (< {self.MIN_TITLE_LENGTH} chars)",
                    impact="May not be fully displayed in search results",
                    affected_urls=pages_with_short_title[:10],
                )
            )

        if pages_with_long_title:
            findings["warnings"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_with_long_title)} pages have long titles (> {self.MAX_TITLE_LENGTH} chars)",
                    impact="May be truncated in search results",
                    affected_urls=pages_with_long_title[:10],
                )
            )

    def _check_heading_structure(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check heading hierarchy (H1-H6)."""
        pages_without_h1 = []
        pages_with_multiple_h1 = []
        pages_with_broken_hierarchy = []

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")

                h1_tags = soup.find_all("h1")
                h_tags = {f"h{i}": soup.find_all(f"h{i}") for i in range(1, 7)}

                # Check H1 count
                if len(h1_tags) == 0:
                    pages_without_h1.append(page.url)
                    findings["issue_counts"]["missing_h1"] += 1
                elif len(h1_tags) > 1:
                    pages_with_multiple_h1.append(page.url)
                    findings["issue_counts"]["multiple_h1"] += 1

                # Check heading hierarchy (simplified: warn if H3 before H2, etc.)
                all_headings = []
                for level in range(1, 7):
                    for tag in h_tags[f"h{level}"]:
                        all_headings.append((level, tag.get_text()[:50]))

                if all_headings:
                    last_level = all_headings[0][0]
                    for level, text in all_headings[1:]:
                        if level > last_level + 1:
                            pages_with_broken_hierarchy.append(page.url)
                            findings["issue_counts"]["broken_h_hierarchy"] += 1
                            break
                        last_level = min(level, last_level)

            except Exception:
                continue

        # Add critical/warning issues
        if pages_without_h1:
            findings["critical_issues"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_without_h1)} pages missing H1 tag",
                    impact="Page structure unclear to search engines",
                    affected_urls=pages_without_h1[:10],
                    severity="high",
                )
            )

        if pages_with_multiple_h1:
            findings["warnings"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_with_multiple_h1)} pages have multiple H1 tags",
                    impact="May dilute page topic relevance to search engines",
                    affected_urls=pages_with_multiple_h1[:10],
                )
            )

        if pages_with_broken_hierarchy:
            findings["opportunities"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{len(pages_with_broken_hierarchy)} pages have broken heading hierarchy",
                    impact="Reduces content scannability and structure clarity",
                    affected_urls=pages_with_broken_hierarchy[:10],
                    recommendation="Ensure headings follow proper sequence (H1 -> H2 -> H3)",
                )
            )

    def _check_image_alt_text(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check for missing image alt text."""
        pages_without_alt = []
        total_images = 0
        total_missing_alt = 0

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")
                images = soup.find_all("img")
                total_images += len(images)

                missing_alt_count = 0
                for img in images:
                    if not img.get("alt") or not img.get("alt").strip():
                        missing_alt_count += 1
                        total_missing_alt += 1

                if missing_alt_count > 0:
                    pages_without_alt.append(page.url)
                    findings["issue_counts"]["missing_alt_text"] += 1

            except Exception:
                continue

        if pages_without_alt and total_missing_alt > 0:
            findings["warnings"].append(
                SeoIssue(
                    category="technical",
                    issue=f"{total_missing_alt} images missing alt text across {len(pages_without_alt)} pages",
                    impact="Reduces accessibility and image SEO, LLMs can't understand images",
                    affected_urls=pages_without_alt[:10],
                    recommendation="Add descriptive alt text to all images",
                )
            )

    def _check_link_health(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check for broken links and redirect chains."""
        broken_links = {}
        external_links = []
        pages_with_issues = set()

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")
                links = soup.find_all("a", href=True)

                for link in links:
                    href = link.get("href", "").strip()

                    if not href or href.startswith("#"):
                        continue

                    # Check for external links
                    if href.startswith(("http://", "https://")):
                        try:
                            parsed = urlparse(href)
                            parsed_page = urlparse(page.url)

                            if parsed.netloc != parsed_page.netloc:
                                external_links.append((page.url, href))
                        except Exception:
                            pass

            except Exception:
                continue

        # Add opportunity for external links audit
        if external_links:
            findings["opportunities"].append(
                SeoIssue(
                    category="technical",
                    issue=f"Found {len(external_links)} external links on {len(set(url for url, _ in external_links))} pages",
                    impact="External links may leak link equity or affect user experience",
                    affected_urls=list(set(url for url, _ in external_links))[:10],
                    recommendation="Audit external links for relevance and add rel='nofollow' where appropriate",
                )
            )

    def _check_robots_sitemap(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check for robots.txt and sitemap.xml."""
        # Check if sitemap exists in crawl data
        sitemap_urls = []
        if snapshot.sitemap:
            sitemap_urls = snapshot.sitemap.get("pages", [])

        if not sitemap_urls:
            findings["opportunities"].append(
                SeoIssue(
                    category="technical",
                    issue="No sitemap.xml detected",
                    impact="Search engines may struggle to discover all pages",
                    affected_urls=[],
                    recommendation="Create and submit sitemap.xml to search engines",
                )
            )
        else:
            findings["issue_counts"]["has_sitemap"] += 1

    def _check_content_length(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check content length and quality indicators."""
        pages_under_min = []
        pages_over_max = []

        for page in snapshot.pages:
            try:
                markdown_content = page.get_markdown()
                word_count = len(markdown_content.split())

                if word_count < self.MIN_CONTENT_LENGTH:
                    pages_under_min.append((page.url, word_count))
                    findings["issue_counts"]["thin_content"] += 1

            except Exception:
                continue

        if pages_under_min:
            affected_urls = [url for url, _ in pages_under_min[:10]]
            findings["warnings"].append(
                SeoIssue(
                    category="content",
                    issue=f"{len(pages_under_min)} pages under {self.MIN_CONTENT_LENGTH} words",
                    impact="Thin content may rank poorly",
                    affected_urls=affected_urls,
                    recommendation=f"Expand content to at least {self.MIN_CONTENT_LENGTH} words",
                )
            )

    def _check_keyword_usage(
        self, snapshot: SiteSnapshot, findings: Dict, target_keywords: List[str]
    ) -> None:
        """Check keyword usage and placement."""
        if not target_keywords:
            return

        pages_missing_keywords = {kw: [] for kw in target_keywords}
        pages_good_keyword_density = {kw: [] for kw in target_keywords}

        for page in snapshot.pages:
            try:
                content = page.get_markdown().lower()
                title_tag = ""
                soup = BeautifulSoup(page.get_content(), "html.parser")
                title = soup.find("title")
                if title:
                    title_tag = title.string.lower() if title.string else ""

                for keyword in target_keywords:
                    keyword_lower = keyword.lower()

                    # Check if keyword is in title (high value)
                    in_title = keyword_lower in title_tag

                    # Check keyword density
                    keyword_count = len(re.findall(r"\b" + re.escape(keyword_lower) + r"\b", content))
                    word_count = len(content.split())
                    density = (keyword_count / word_count * 100) if word_count > 0 else 0

                    if keyword_count == 0:
                        pages_missing_keywords[keyword].append(page.url)
                    elif density >= 2 and in_title:
                        pages_good_keyword_density[keyword].append(page.url)

            except Exception:
                continue

        # Add opportunities for keyword optimization
        for keyword in target_keywords:
            missing = pages_missing_keywords[keyword]
            if missing:
                findings["opportunities"].append(
                    SeoIssue(
                        category="content",
                        issue=f"{len(missing)} pages don't mention target keyword '{keyword}'",
                        impact="Reduced relevance for search queries containing this term",
                        affected_urls=missing[:10],
                        recommendation=f"Incorporate '{keyword}' naturally in content and title tags",
                    )
                )

    def _check_internal_linking(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check internal linking structure."""
        pages_no_internal_links = []
        internal_link_counts = []

        for page in snapshot.pages:
            try:
                soup = BeautifulSoup(page.get_content(), "html.parser")
                internal_links = 0

                for link in soup.find_all("a", href=True):
                    href = link.get("href", "").strip()

                    if href.startswith(("/", "#")) or page.url in href:
                        internal_links += 1

                internal_link_counts.append(internal_links)

                if internal_links == 0:
                    pages_no_internal_links.append(page.url)
                    findings["issue_counts"]["no_internal_links"] += 1

            except Exception:
                continue

        if pages_no_internal_links:
            findings["opportunities"].append(
                SeoIssue(
                    category="internal-linking",
                    issue=f"{len(pages_no_internal_links)} pages have no internal links",
                    impact="Reduces crawlability and page authority distribution",
                    affected_urls=pages_no_internal_links[:10],
                    recommendation="Add contextual internal links to important pages",
                )
            )

    def _check_duplicate_content(self, snapshot: SiteSnapshot, findings: Dict) -> None:
        """Check for potential duplicate content."""
        content_hashes = {}
        duplicates = {}

        for page in snapshot.pages:
            try:
                # Simple hash of first 500 chars to detect near-duplicates
                content = page.get_markdown()
                content_hash = hash(content[:500])

                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(page.url)

            except Exception:
                continue

        # Find actual duplicates (>2 pages with same hash)
        for content_hash, urls in content_hashes.items():
            if len(urls) > 1:
                duplicates[content_hash] = urls

        if duplicates:
            total_duplicates = sum(len(urls) for urls in duplicates.values())
            affected_urls = []
            for urls in list(duplicates.values())[:3]:
                affected_urls.extend(urls[:2])

            findings["warnings"].append(
                SeoIssue(
                    category="content",
                    issue=f"Found {total_duplicates} pages with potential duplicate content",
                    impact="Search engines may penalize or choose only one canonical version",
                    affected_urls=affected_urls[:10],
                    recommendation="Use canonical tags or consolidate duplicate pages",
                )
            )

    def _calculate_score(self, findings: Dict, total_pages: int) -> float:
        """Calculate overall SEO score (0-10)."""
        score = 10.0

        # Deduct points based on issues
        critical_count = len(findings["critical_issues"])
        warning_count = len(findings["warnings"])
        opportunity_count = len(findings["opportunities"])

        # Critical issues heavily impact score
        score -= critical_count * 2.0

        # Warnings reduce score moderately
        score -= warning_count * 0.5

        # Opportunities reduce score slightly
        score -= opportunity_count * 0.1

        # Floor at 0, cap at 10
        return max(0.0, min(10.0, score))

    def _generate_summary(
        self, overall_score: float, critical_count: int, warning_count: int, opportunity_count: int
    ) -> str:
        """Generate human-readable summary."""
        status = "Excellent" if overall_score >= 8.0 else "Good" if overall_score >= 6.0 else "Needs Improvement"

        parts = [
            f"SEO score: {overall_score:.1f}/10 ({status}).",
            f"Found {critical_count} critical issue(s), {warning_count} warning(s), and {opportunity_count} improvement opportunity/opportunities.",
        ]

        if critical_count > 0:
            parts.append("Address critical issues first for immediate SEO improvements.")
        elif warning_count > 0:
            parts.append("Fix warnings to improve search engine rankings.")
        else:
            parts.append("Good SEO foundation; implement opportunities for competitive advantage.")

        return " ".join(parts)
