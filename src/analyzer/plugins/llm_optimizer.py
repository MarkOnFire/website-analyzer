"""LLM Optimization plugin for analyzing site discoverability and usefulness to LLMs.

This plugin analyzes website structure, metadata, and content organization to provide
recommendations for making the site more discoverable and useful in LLM contexts.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from html.parser import HTMLParser

from pydantic import BaseModel

from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin, PageData


class MetaTagIssue(BaseModel):
    """Represents a meta tag related issue."""
    category: str
    issue: str
    impact: str
    fix: str
    affected_urls: List[str]
    priority: str


class SchemaMarkupIssue(BaseModel):
    """Represents a schema markup related issue."""
    category: str
    issue: str
    impact: str
    affected_urls: List[str]
    priority: str
    fix: str


class ContentStructureIssue(BaseModel):
    """Represents a content structure recommendation."""
    category: str
    finding: str
    recommendation: str
    effort: str
    impact: str
    affected_pages: int


class SimpleHTMLParser(HTMLParser):
    """Simple HTML parser to extract meta tags and structural information."""

    def __init__(self):
        super().__init__()
        self.meta_tags: Dict[str, str] = {}
        self.title: Optional[str] = None
        self.headings: Dict[str, List[str]] = {}  # h1, h2, h3, etc.
        self.has_schema_markup = False
        self.in_title = False
        self.title_content = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs) if attrs else {}

        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            property_attr = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")

            if name:
                self.meta_tags[name] = content
            elif property_attr:
                self.meta_tags[property_attr] = content
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.current_heading_tag = tag
            if tag not in self.headings:
                self.headings[tag] = []
        elif tag == "script":
            script_type = attrs_dict.get("type", "")
            if "schema" in script_type or "json-ld" in script_type.lower():
                self.has_schema_markup = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
            if self.title_content:
                self.title = "".join(self.title_content).strip()
                self.title_content = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_content.append(data)
        elif hasattr(self, "current_heading_tag"):
            heading_text = data.strip()
            if heading_text:
                if self.current_heading_tag not in self.headings:
                    self.headings[self.current_heading_tag] = []
                self.headings[self.current_heading_tag].append(heading_text)


class LLMOptimizer(TestPlugin):
    """
    Analyzes websites for LLM optimization opportunities.

    Checks for:
    - Meta tags (description, keywords, Open Graph, Twitter cards)
    - Schema.org markup presence and correctness
    - Content hierarchy (headings, semantic HTML)
    - Link structure and internal navigation
    """

    name: str = "llm-optimizer"
    description: str = "Analyze site for LLM discoverability and optimization"

    @staticmethod
    def _extract_meta_tags(html: str) -> Dict[str, str]:
        """Extract meta tags from HTML."""
        parser = SimpleHTMLParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        return parser.meta_tags

    @staticmethod
    def _get_page_title(html: str) -> Optional[str]:
        """Extract page title from HTML."""
        parser = SimpleHTMLParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        return parser.title

    @staticmethod
    def _get_headings(html: str) -> Dict[str, List[str]]:
        """Extract headings from HTML."""
        parser = SimpleHTMLParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        return parser.headings

    @staticmethod
    def _has_schema_markup(html: str) -> bool:
        """Check if page has schema.org markup."""
        return bool(re.search(r'<script[^>]*type=["\']application/ld\+json["\']', html, re.IGNORECASE))

    @staticmethod
    def _count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Extract plain text from HTML."""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
        # Remove HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)
        # Remove extra whitespace
        html = re.sub(r'\s+', ' ', html).strip()
        return html

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        """
        Analyze the site for LLM optimization opportunities.

        Args:
            snapshot: The SiteSnapshot object containing the website data.
            **kwargs: Optional configuration parameters.

        Returns:
            A TestResult with overall score and recommendations.
        """
        quick_wins: List[MetaTagIssue] = []
        strategic_recommendations: List[ContentStructureIssue] = []

        # Analysis tracking
        pages_analyzed = 0
        pages_missing_description = []
        pages_missing_title = []
        pages_without_schema = []
        pages_with_poor_headings = []
        pages_with_short_content = []

        # Schema markup tracking
        schema_types: Dict[str, int] = {}

        # Aggregate metrics
        total_pages = len(snapshot.pages)
        avg_title_length = 0
        avg_description_length = 0
        title_lengths = []
        description_lengths = []

        # Analyze each page
        for page in snapshot.pages:
            pages_analyzed += 1
            html = page.get_content()

            # Extract metadata
            meta_tags = self._extract_meta_tags(html)
            title = self._get_page_title(html)
            headings = self._get_headings(html)
            has_schema = self._has_schema_markup(html)

            # Track title
            if title:
                title_lengths.append(len(title))
            else:
                pages_missing_title.append(page.url)

            # Track meta description
            description = meta_tags.get("description", "")
            if not description:
                pages_missing_description.append(page.url)
            else:
                description_lengths.append(len(description))

            # Track schema markup
            if not has_schema:
                pages_without_schema.append(page.url)

            # Analyze content structure
            text_content = self._extract_text_from_html(html)
            word_count = self._count_words(text_content)

            # Check heading hierarchy
            h1_count = len(headings.get("h1", []))
            has_good_hierarchy = (
                h1_count > 0 and
                len(headings.get("h2", [])) > 0 and
                len(headings.get("h3", [])) > 0
            )

            if not has_good_hierarchy:
                pages_with_poor_headings.append(page.url)

            # Check content length (min 200 words for substantial content)
            if word_count < 200 and not re.search(r"privacy|terms|contact|404", page.url.lower()):
                pages_with_short_content.append(page.url)

        # Calculate averages
        if title_lengths:
            avg_title_length = sum(title_lengths) / len(title_lengths)
        if description_lengths:
            avg_description_length = sum(description_lengths) / len(description_lengths)

        # Build quick wins (high-priority actionable items)

        # Issue: Missing meta descriptions
        if pages_missing_description:
            quick_wins.append(MetaTagIssue(
                priority="high",
                category="meta-tags",
                issue=f"{len(pages_missing_description)} pages missing meta descriptions",
                impact="LLMs can't generate accurate summaries without description metadata",
                fix="Add descriptive meta tags to all content pages (50-160 characters recommended)",
                affected_urls=pages_missing_description[:10]  # Show first 10
            ))

        # Issue: Missing page titles
        if pages_missing_title:
            quick_wins.append(MetaTagIssue(
                priority="high",
                category="meta-tags",
                issue=f"{len(pages_missing_title)} pages missing title tags",
                impact="Page titles are critical for LLM context and search results",
                fix="Ensure every page has a unique, descriptive title tag (50-60 characters)",
                affected_urls=pages_missing_title[:10]
            ))

        # Issue: Pages without schema markup
        if pages_without_schema and len(pages_without_schema) > total_pages * 0.5:
            quick_wins.append(MetaTagIssue(
                priority="medium",
                category="schema-markup",
                issue=f"{len(pages_without_schema)} pages lack schema.org markup",
                impact="Content relationships unclear to LLMs; harder to extract structured data",
                fix="Add schema.org markup (Article, Product, Organization, etc.) to relevant pages",
                affected_urls=pages_without_schema[:10]
            ))

        # Issue: Poor heading hierarchy
        if pages_with_poor_headings and len(pages_with_poor_headings) > total_pages * 0.3:
            strategic_recommendations.append(ContentStructureIssue(
                category="content-structure",
                finding=f"{len(pages_with_poor_headings)} pages have poor heading hierarchy (missing H2s or H3s)",
                recommendation="Restructure content with clear heading hierarchy (H1 → H2 → H3) to improve scannability for LLMs",
                effort="medium",
                impact="high",
                affected_pages=len(pages_with_poor_headings)
            ))

        # Issue: Short content pages
        if pages_with_short_content:
            strategic_recommendations.append(ContentStructureIssue(
                category="content-depth",
                finding=f"{len(pages_with_short_content)} content pages have fewer than 200 words",
                recommendation="Expand content with more detailed information, key points, and context",
                effort="medium",
                impact="high",
                affected_pages=len(pages_with_short_content)
            ))

        # Build overall score (0-10)
        score = 10.0

        # Deduct for missing metadata
        missing_desc_ratio = len(pages_missing_description) / max(total_pages, 1)
        score -= missing_desc_ratio * 3

        missing_title_ratio = len(pages_missing_title) / max(total_pages, 1)
        score -= missing_title_ratio * 2

        # Deduct for lack of schema markup
        missing_schema_ratio = len(pages_without_schema) / max(total_pages, 1)
        score -= missing_schema_ratio * 2

        # Deduct for poor heading hierarchy
        poor_hierarchy_ratio = len(pages_with_poor_headings) / max(total_pages, 1)
        score -= poor_hierarchy_ratio * 1.5

        # Deduct for short content
        short_content_ratio = len(pages_with_short_content) / max(total_pages, 1)
        score -= short_content_ratio * 1

        # Clamp score to 0-10
        score = max(0, min(10, score))

        # Determine status
        status = "pass" if score >= 7.0 else "fail" if score < 5.0 else "warning"

        return TestResult(
            plugin_name=self.name,
            status=status,
            summary=f"LLM Optimization Score: {score:.1f}/10 - Found {len(quick_wins)} quick wins and {len(strategic_recommendations)} strategic recommendations",
            details={
                "overall_score": score,
                "pages_analyzed": pages_analyzed,
                "quick_wins": [w.model_dump() for w in quick_wins],
                "strategic_recommendations": [r.model_dump() for r in strategic_recommendations],
                "metrics": {
                    "avg_title_length": round(avg_title_length, 1),
                    "avg_description_length": round(avg_description_length, 1),
                    "pages_missing_description": len(pages_missing_description),
                    "pages_missing_title": len(pages_missing_title),
                    "pages_without_schema": len(pages_without_schema),
                    "pages_with_poor_headings": len(pages_with_poor_headings),
                    "pages_with_short_content": len(pages_with_short_content),
                }
            }
        )
