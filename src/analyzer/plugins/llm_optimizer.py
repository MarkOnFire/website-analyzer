"""LLM Optimization plugin for analyzing site discoverability and usefulness to LLMs.

This plugin analyzes website structure, metadata, and content organization to provide
recommendations for making the site more discoverable and useful in LLM contexts.
"""

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

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

    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self.meta_tags: Dict[str, str] = {}
        self.title: Optional[str] = None
        self.headings: Dict[str, List[str]] = {}  # h1, h2, h3, etc.
        self.has_schema_markup = False
        self.in_title = False
        self.title_content = []
        self.semantic_tags: Set[str] = set()
        self.internal_links: List[str] = []
        self.base_url = base_url

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
        elif tag in ["article", "section", "nav", "header", "footer", "aside", "main"]:
            self.semantic_tags.add(tag)
        elif tag == "a" and self.base_url:
            href = attrs_dict.get("href", "")
            if href:
                # Resolve relative URLs
                absolute_url = urljoin(self.base_url, href)
                # Check if it's internal (same domain)
                base_domain = urlparse(self.base_url).netloc
                link_domain = urlparse(absolute_url).netloc
                if base_domain == link_domain:
                    self.internal_links.append(absolute_url)

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

    @staticmethod
    def _get_semantic_tags(html: str) -> Set[str]:
        """Extract semantic HTML5 tags from HTML."""
        parser = SimpleHTMLParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        return parser.semantic_tags

    @staticmethod
    def _get_internal_links(html: str, base_url: str) -> List[str]:
        """Extract internal links from HTML."""
        parser = SimpleHTMLParser(base_url=base_url)
        try:
            parser.feed(html)
        except Exception:
            pass
        return parser.internal_links

    @staticmethod
    async def _check_meta_description_quality(description: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM (Haiku 3.5) to evaluate meta description quality.

        Returns None if API key not available or on error.
        """
        if not description:
            return None

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)

            prompt = f"""Evaluate this meta description for SEO and LLM optimization:

"{description}"

Rate it on a scale of 1-10 and provide brief feedback (max 50 words).
Respond in this exact format:
Score: [number]
Feedback: [your feedback]"""

            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Parse the response
            score_match = re.search(r'Score:\s*(\d+)', response_text)
            feedback_match = re.search(r'Feedback:\s*(.+)', response_text, re.DOTALL)

            if score_match and feedback_match:
                return {
                    "score": int(score_match.group(1)),
                    "feedback": feedback_match.group(1).strip()
                }
        except Exception:
            # Silently fail if LLM check unavailable
            pass

        return None

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
        pages_without_semantic_html = []
        pages_with_poor_linking = []

        # Schema markup tracking
        schema_types: Dict[str, int] = {}

        # Semantic HTML tracking
        all_semantic_tags: Set[str] = set()

        # Link structure tracking
        all_internal_links: Dict[str, List[str]] = {}  # page_url -> [linked_urls]
        pages_linked_to: Dict[str, int] = {}  # count how many times each page is linked to

        # LLM quality checks
        llm_description_checks: List[Dict[str, Any]] = []

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

                # LLM-based quality check for meta descriptions (sample first 5 pages)
                if len(llm_description_checks) < 5:
                    llm_check = await self._check_meta_description_quality(description)
                    if llm_check:
                        llm_description_checks.append({
                            "url": page.url,
                            "description": description,
                            **llm_check
                        })

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

            # Feature #80: Semantic HTML usage detection
            semantic_tags = self._get_semantic_tags(html)
            all_semantic_tags.update(semantic_tags)
            if len(semantic_tags) < 2:  # Expect at least 2 semantic tags
                pages_without_semantic_html.append(page.url)

            # Feature #81: Internal link structure analysis
            internal_links = self._get_internal_links(html, page.url)
            all_internal_links[page.url] = internal_links

            # Track how many times each page is linked to
            for link in internal_links:
                pages_linked_to[link] = pages_linked_to.get(link, 0) + 1

            # Poor linking: pages with very few outbound internal links
            if len(internal_links) < 2 and not re.search(r"privacy|terms|contact|404", page.url.lower()):
                pages_with_poor_linking.append(page.url)

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

        # Feature #80: Semantic HTML recommendations
        if pages_without_semantic_html and len(pages_without_semantic_html) > total_pages * 0.4:
            strategic_recommendations.append(ContentStructureIssue(
                category="semantic-html",
                finding=f"{len(pages_without_semantic_html)} pages lack semantic HTML5 tags (article, section, nav, etc.)",
                recommendation="Use semantic HTML5 elements to help LLMs understand content structure and relationships",
                effort="low",
                impact="medium",
                affected_pages=len(pages_without_semantic_html)
            ))

        # Feature #81: Internal linking recommendations
        if pages_with_poor_linking and len(pages_with_poor_linking) > total_pages * 0.3:
            strategic_recommendations.append(ContentStructureIssue(
                category="internal-linking",
                finding=f"{len(pages_with_poor_linking)} pages have weak internal link structure (fewer than 2 links)",
                recommendation="Add more contextual internal links to help LLMs understand content relationships and site structure",
                effort="low",
                impact="high",
                affected_pages=len(pages_with_poor_linking)
            ))

        # Find orphaned pages (not linked to by any other page)
        orphaned_pages = [url for url in all_internal_links.keys() if pages_linked_to.get(url, 0) == 0]
        if orphaned_pages and len(orphaned_pages) > 1:
            quick_wins.append(MetaTagIssue(
                priority="medium",
                category="internal-linking",
                issue=f"{len(orphaned_pages)} pages are orphaned (not linked to by other pages)",
                impact="Isolated content is harder for LLMs to discover and contextualize",
                fix="Add navigation links or contextual references from related pages",
                affected_urls=orphaned_pages[:10]
            ))

        # Feature #83: LLM-based meta description quality issues
        if llm_description_checks:
            low_quality_descriptions = [check for check in llm_description_checks if check["score"] < 7]
            if low_quality_descriptions:
                quick_wins.append(MetaTagIssue(
                    priority="medium",
                    category="meta-quality",
                    issue=f"{len(low_quality_descriptions)} meta descriptions rated low quality by LLM analysis",
                    impact="Poor meta descriptions reduce LLM understanding and search relevance",
                    fix=f"Example feedback: {low_quality_descriptions[0]['feedback'][:100]}...",
                    affected_urls=[check["url"] for check in low_quality_descriptions]
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

        # Feature #80: Deduct for lack of semantic HTML
        semantic_html_ratio = len(pages_without_semantic_html) / max(total_pages, 1)
        score -= semantic_html_ratio * 0.5

        # Feature #81: Deduct for poor internal linking
        poor_linking_ratio = len(pages_with_poor_linking) / max(total_pages, 1)
        score -= poor_linking_ratio * 0.75

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
                    "pages_without_semantic_html": len(pages_without_semantic_html),
                    "pages_with_poor_linking": len(pages_with_poor_linking),
                    "orphaned_pages": len(orphaned_pages) if orphaned_pages else 0,
                    "semantic_tags_found": list(all_semantic_tags),
                    "avg_internal_links_per_page": round(sum(len(links) for links in all_internal_links.values()) / max(total_pages, 1), 1),
                    "llm_description_checks": llm_description_checks,
                }
            }
        )
