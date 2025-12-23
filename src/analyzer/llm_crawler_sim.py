"""LLM Crawler Simulation module.

Simulates how major LLM training crawlers see a website by making simple HTTP
requests with real crawler User-Agent strings. This provides an accurate picture
of what content is available to LLM training pipelines.

Unlike headless browsers, LLM crawlers:
- Don't execute JavaScript
- Make simple HTTP GET requests
- Respect robots.txt
- Identify themselves via User-Agent
- Get blocked easily by bot protection

This module also analyzes content quality for LLM optimization, checking:
- Meta tags (title, description, Open Graph)
- Schema.org markup
- Content hierarchy (headings)
- Semantic HTML usage
- Content depth and structure
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp


@dataclass
class LLMCrawler:
    """Represents a known LLM crawler."""
    name: str
    user_agent: str
    organization: str
    description: str
    robots_txt_token: str  # The token used in robots.txt (e.g., "GPTBot")


class SimpleHTMLParser(HTMLParser):
    """Simple HTML parser to extract meta tags and structural information."""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self.meta_tags: Dict[str, str] = {}
        self.title: Optional[str] = None
        self.headings: Dict[str, List[str]] = {}  # h1, h2, h3, etc.
        self.has_schema_markup = False
        self.in_title = False
        self.title_content: List[str] = []
        self.semantic_tags: Set[str] = set()
        self.internal_links: List[str] = []
        self.external_links: List[str] = []
        self.base_url = base_url
        self.current_heading_tag: Optional[str] = None

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
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                # Resolve relative URLs
                absolute_url = urljoin(self.base_url, href)
                # Check if it's internal (same domain)
                base_domain = urlparse(self.base_url).netloc
                link_domain = urlparse(absolute_url).netloc
                if base_domain == link_domain:
                    self.internal_links.append(absolute_url)
                else:
                    self.external_links.append(absolute_url)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
            if self.title_content:
                self.title = "".join(self.title_content).strip()
                self.title_content = []
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.current_heading_tag = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_content.append(data)
        elif self.current_heading_tag:
            heading_text = data.strip()
            if heading_text:
                if self.current_heading_tag not in self.headings:
                    self.headings[self.current_heading_tag] = []
                self.headings[self.current_heading_tag].append(heading_text)


@dataclass
class ContentAnalysis:
    """Analysis of page content for LLM optimization."""
    # Meta information
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    has_og_tags: bool = False
    has_twitter_cards: bool = False

    # Schema markup
    has_schema_markup: bool = False

    # Content structure
    h1_count: int = 0
    h2_count: int = 0
    h3_count: int = 0
    has_good_heading_hierarchy: bool = False
    headings: Dict[str, List[str]] = field(default_factory=dict)

    # Semantic HTML
    semantic_tags_used: Set[str] = field(default_factory=set)
    uses_semantic_html: bool = False

    # Content depth
    word_count: int = 0
    has_substantial_content: bool = False  # 200+ words

    # Links
    internal_link_count: int = 0
    external_link_count: int = 0

    # Overall score (0-10)
    llm_readiness_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Known LLM training crawlers and their User-Agent strings
# Sources: robots.txt documentation from each provider
KNOWN_LLM_CRAWLERS: List[LLMCrawler] = [
    LLMCrawler(
        name="GPTBot",
        user_agent="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
        organization="OpenAI",
        description="Used to crawl content for training GPT models",
        robots_txt_token="GPTBot",
    ),
    LLMCrawler(
        name="ChatGPT-User",
        user_agent="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)",
        organization="OpenAI",
        description="Used by ChatGPT for browsing/plugins (not training)",
        robots_txt_token="ChatGPT-User",
    ),
    LLMCrawler(
        name="ClaudeBot",
        user_agent="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-bot)",
        organization="Anthropic",
        description="Used to crawl content for training Claude models",
        robots_txt_token="ClaudeBot",
    ),
    LLMCrawler(
        name="anthropic-ai",
        user_agent="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; anthropic-ai/1.0; +https://www.anthropic.com)",
        organization="Anthropic",
        description="Alternative Anthropic crawler identifier",
        robots_txt_token="anthropic-ai",
    ),
    LLMCrawler(
        name="Google-Extended",
        user_agent="Mozilla/5.0 (compatible; Google-Extended)",
        organization="Google",
        description="Used for Gemini/Bard training data (separate from search)",
        robots_txt_token="Google-Extended",
    ),
    LLMCrawler(
        name="CCBot",
        user_agent="CCBot/2.0 (https://commoncrawl.org/faq/)",
        organization="Common Crawl",
        description="Common Crawl dataset used by many LLM projects for training",
        robots_txt_token="CCBot",
    ),
    LLMCrawler(
        name="Bytespider",
        user_agent="Mozilla/5.0 (compatible; Bytespider; spider-feedback@bytedance.com)",
        organization="ByteDance",
        description="ByteDance crawler, potentially used for LLM training",
        robots_txt_token="Bytespider",
    ),
    LLMCrawler(
        name="PerplexityBot",
        user_agent="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)",
        organization="Perplexity",
        description="Perplexity AI search and answer engine",
        robots_txt_token="PerplexityBot",
    ),
    LLMCrawler(
        name="Amazonbot",
        user_agent="Mozilla/5.0 (compatible; Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot)",
        organization="Amazon",
        description="Amazon crawler, used for Alexa and potentially AI training",
        robots_txt_token="Amazonbot",
    ),
    LLMCrawler(
        name="Meta-ExternalAgent",
        user_agent="Mozilla/5.0 (compatible; Meta-ExternalAgent/1.0; +https://www.meta.com/help/contact-us/)",
        organization="Meta",
        description="Meta's external crawler for AI training",
        robots_txt_token="Meta-ExternalAgent",
    ),
]


@dataclass
class CrawlerResponse:
    """Result of a single crawler's request."""
    crawler: LLMCrawler
    url: str
    status_code: int
    content_length: int
    content_type: Optional[str]
    title: Optional[str]
    is_blocked: bool
    block_reason: Optional[str]
    response_time_ms: float
    error: Optional[str] = None
    content_preview: Optional[str] = None  # First 500 chars of body
    has_meaningful_content: bool = False
    redirect_url: Optional[str] = None
    content_analysis: Optional[ContentAnalysis] = None  # LLM readiness analysis


@dataclass
class SimulationResult:
    """Complete result of LLM crawler simulation for a URL."""
    url: str
    timestamp: str
    responses: List[CrawlerResponse] = field(default_factory=list)
    robots_txt_content: Optional[str] = None
    robots_txt_blocks: Dict[str, bool] = field(default_factory=dict)  # crawler -> blocked
    summary: Dict[str, Any] = field(default_factory=dict)
    content_analysis: Optional[ContentAnalysis] = None  # Aggregated content analysis


class LLMCrawlerSimulator:
    """Simulates LLM crawler access to a website."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        crawlers: Optional[List[LLMCrawler]] = None,
    ):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.crawlers = crawlers or KNOWN_LLM_CRAWLERS

    async def fetch_robots_txt(self, base_url: str) -> Optional[str]:
        """Fetch robots.txt from the site."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception:
            pass
        return None

    def parse_robots_txt(self, robots_txt: str, crawler_token: str) -> bool:
        """Check if a crawler is blocked by robots.txt. Returns True if blocked."""
        if not robots_txt:
            return False

        lines = robots_txt.lower().split('\n')
        current_agent = None
        is_relevant = False

        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            if line.startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                current_agent = agent
                is_relevant = (agent == '*' or agent == crawler_token.lower())

            elif line.startswith('disallow:') and is_relevant:
                path = line.split(':', 1)[1].strip()
                if path == '/' or path == '/*':
                    return True

        return False

    async def _fetch_as_crawler(
        self,
        session: aiohttp.ClientSession,
        url: str,
        crawler: LLMCrawler,
    ) -> CrawlerResponse:
        """Fetch a URL as a specific crawler."""
        start_time = asyncio.get_event_loop().time()

        try:
            headers = {
                "User-Agent": crawler.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            async with session.get(url, headers=headers, allow_redirects=True) as response:
                elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                content = await response.text()
                content_length = len(content)

                # Extract title
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else None

                # Detect blocking
                is_blocked, block_reason = self._detect_blocking(
                    response.status, content, title, str(response.url)
                )

                # Check for meaningful content
                has_meaningful = self._has_meaningful_content(content, response.status)

                # Get redirect URL if different
                redirect_url = None
                if str(response.url) != url:
                    redirect_url = str(response.url)

                return CrawlerResponse(
                    crawler=crawler,
                    url=url,
                    status_code=response.status,
                    content_length=content_length,
                    content_type=response.headers.get('Content-Type'),
                    title=title,
                    is_blocked=is_blocked,
                    block_reason=block_reason,
                    response_time_ms=elapsed_ms,
                    content_preview=content[:500] if content else None,
                    has_meaningful_content=has_meaningful,
                    redirect_url=redirect_url,
                )

        except asyncio.TimeoutError:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return CrawlerResponse(
                crawler=crawler,
                url=url,
                status_code=0,
                content_length=0,
                content_type=None,
                title=None,
                is_blocked=True,
                block_reason="timeout",
                response_time_ms=elapsed_ms,
                error="Request timed out",
                has_meaningful_content=False,
            )
        except Exception as e:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return CrawlerResponse(
                crawler=crawler,
                url=url,
                status_code=0,
                content_length=0,
                content_type=None,
                title=None,
                is_blocked=True,
                block_reason="error",
                response_time_ms=elapsed_ms,
                error=str(e),
                has_meaningful_content=False,
            )

    def _detect_blocking(
        self,
        status_code: int,
        content: str,
        title: Optional[str],
        final_url: str,
    ) -> tuple[bool, Optional[str]]:
        """Detect if the response indicates blocking."""
        # Status code blocks
        if status_code == 403:
            return True, "403 Forbidden"
        if status_code == 401:
            return True, "401 Unauthorized"
        if status_code == 429:
            return True, "429 Rate Limited"
        if status_code >= 500:
            return True, f"{status_code} Server Error"

        # Cloudflare detection
        if "cdn-cgi" in final_url or "__cf_chl" in final_url:
            return True, "Cloudflare challenge redirect"

        content_lower = content.lower()
        title_lower = (title or "").lower()

        # Title-based detection
        if "access denied" in title_lower:
            return True, "Access denied page"
        if "blocked" in title_lower:
            return True, "Blocked page"
        if "challenge" in title_lower and "cloudflare" in content_lower:
            return True, "Cloudflare challenge page"
        if "just a moment" in title_lower:
            return True, "Cloudflare 'Just a moment' challenge"
        if "attention required" in title_lower:
            return True, "Cloudflare attention required"

        # Content-based detection
        if "cf-browser-verification" in content_lower:
            return True, "Cloudflare browser verification"
        if "checking your browser" in content_lower:
            return True, "Bot detection check"
        if "_cf_chl_opt" in content:
            return True, "Cloudflare challenge script detected"

        # Captcha detection
        if "captcha" in content_lower and ("verify" in content_lower or "human" in content_lower):
            return True, "CAPTCHA challenge"
        if "recaptcha" in content_lower:
            return True, "reCAPTCHA challenge"
        if "hcaptcha" in content_lower:
            return True, "hCaptcha challenge"

        return False, None

    def _has_meaningful_content(self, content: str, status_code: int) -> bool:
        """Check if the page has meaningful content (not just boilerplate)."""
        if status_code != 200:
            return False

        # Strip HTML tags for content analysis
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Check word count (meaningful pages typically have 50+ words)
        word_count = len(text.split())
        return word_count >= 50

    def _extract_text_from_html(self, html: str) -> str:
        """Extract plain text from HTML for word counting."""
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def analyze_content(self, html: str, url: str) -> ContentAnalysis:
        """
        Analyze HTML content for LLM optimization factors.

        This checks everything that LLM training crawlers would see and evaluate:
        - Meta tags and descriptions
        - Schema.org markup
        - Content hierarchy (headings)
        - Semantic HTML usage
        - Content depth
        """
        analysis = ContentAnalysis()
        issues: List[str] = []
        recommendations: List[str] = []

        # Parse HTML
        parser = SimpleHTMLParser(base_url=url)
        try:
            parser.feed(html)
        except Exception:
            issues.append("HTML parsing error - malformed markup")

        # Meta information
        analysis.title = parser.title
        analysis.title_length = len(parser.title) if parser.title else 0
        analysis.meta_description = parser.meta_tags.get("description")
        analysis.meta_description_length = len(analysis.meta_description) if analysis.meta_description else 0

        # Check for Open Graph and Twitter cards
        og_tags = [k for k in parser.meta_tags.keys() if k.startswith("og:")]
        twitter_tags = [k for k in parser.meta_tags.keys() if k.startswith("twitter:")]
        analysis.has_og_tags = len(og_tags) > 0
        analysis.has_twitter_cards = len(twitter_tags) > 0

        # Schema markup (also check for inline JSON-LD)
        analysis.has_schema_markup = parser.has_schema_markup or bool(
            re.search(r'<script[^>]*type=["\']application/ld\+json["\']', html, re.IGNORECASE)
        )

        # Headings
        analysis.headings = parser.headings
        analysis.h1_count = len(parser.headings.get("h1", []))
        analysis.h2_count = len(parser.headings.get("h2", []))
        analysis.h3_count = len(parser.headings.get("h3", []))
        analysis.has_good_heading_hierarchy = (
            analysis.h1_count > 0 and
            analysis.h2_count > 0
        )

        # Semantic HTML
        analysis.semantic_tags_used = parser.semantic_tags
        analysis.uses_semantic_html = len(parser.semantic_tags) >= 2

        # Content depth
        text_content = self._extract_text_from_html(html)
        analysis.word_count = len(text_content.split())
        analysis.has_substantial_content = analysis.word_count >= 200

        # Links
        analysis.internal_link_count = len(parser.internal_links)
        analysis.external_link_count = len(parser.external_links)

        # Calculate LLM readiness score (0-10)
        score = 10.0

        # Title checks
        if not analysis.title:
            score -= 1.5
            issues.append("Missing page title")
            recommendations.append("Add a descriptive <title> tag (50-60 characters)")
        elif analysis.title_length < 30:
            score -= 0.5
            issues.append(f"Title too short ({analysis.title_length} chars)")
            recommendations.append("Expand title to 50-60 characters for better context")
        elif analysis.title_length > 70:
            score -= 0.3
            issues.append(f"Title too long ({analysis.title_length} chars)")

        # Meta description checks
        if not analysis.meta_description:
            score -= 1.5
            issues.append("Missing meta description")
            recommendations.append("Add a meta description (120-160 characters)")
        elif analysis.meta_description_length < 50:
            score -= 0.5
            issues.append(f"Meta description too short ({analysis.meta_description_length} chars)")
            recommendations.append("Expand meta description to 120-160 characters")
        elif analysis.meta_description_length > 160:
            score -= 0.3
            issues.append(f"Meta description too long ({analysis.meta_description_length} chars)")

        # Schema markup
        if not analysis.has_schema_markup:
            score -= 1.0
            issues.append("No schema.org markup found")
            recommendations.append("Add JSON-LD schema markup for better structured data")

        # Heading hierarchy
        if analysis.h1_count == 0:
            score -= 1.0
            issues.append("Missing H1 heading")
            recommendations.append("Add a single H1 heading for the main topic")
        elif analysis.h1_count > 1:
            score -= 0.5
            issues.append(f"Multiple H1 headings ({analysis.h1_count})")
            recommendations.append("Use only one H1 per page")

        if not analysis.has_good_heading_hierarchy:
            score -= 0.5
            issues.append("Poor heading hierarchy (missing H2s)")
            recommendations.append("Structure content with H1 → H2 → H3 hierarchy")

        # Semantic HTML
        if not analysis.uses_semantic_html:
            score -= 0.5
            issues.append("Limited semantic HTML usage")
            recommendations.append("Use semantic tags: <article>, <section>, <nav>, <main>, <header>, <footer>")

        # Content depth
        if analysis.word_count < 100:
            score -= 1.5
            issues.append(f"Very thin content ({analysis.word_count} words)")
            recommendations.append("Add more substantive content (200+ words minimum)")
        elif analysis.word_count < 200:
            score -= 0.5
            issues.append(f"Light content ({analysis.word_count} words)")
            recommendations.append("Consider expanding content for better LLM comprehension")

        # Internal linking
        if analysis.internal_link_count < 2:
            score -= 0.5
            issues.append(f"Few internal links ({analysis.internal_link_count})")
            recommendations.append("Add more internal links to related content")

        # Social meta tags (nice to have)
        if not analysis.has_og_tags:
            score -= 0.2
            issues.append("No Open Graph tags")
        if not analysis.has_twitter_cards:
            score -= 0.1
            issues.append("No Twitter card meta tags")

        # Clamp score
        analysis.llm_readiness_score = max(0.0, min(10.0, score))
        analysis.issues = issues
        analysis.recommendations = recommendations

        return analysis

    async def simulate(self, url: str, analyze_content: bool = True) -> SimulationResult:
        """Run full LLM crawler simulation for a URL.

        Args:
            url: URL to test
            analyze_content: Whether to analyze content for LLM readiness (default: True)
        """
        result = SimulationResult(
            url=url,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Fetch robots.txt first
        result.robots_txt_content = await self.fetch_robots_txt(url)

        # Check robots.txt for each crawler
        for crawler in self.crawlers:
            is_blocked = self.parse_robots_txt(
                result.robots_txt_content or "",
                crawler.robots_txt_token
            )
            result.robots_txt_blocks[crawler.name] = is_blocked

        # Fetch the page as each crawler
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self._fetch_as_crawler(session, url, crawler)
                for crawler in self.crawlers
            ]
            result.responses = await asyncio.gather(*tasks)

        # Analyze content from first successful response
        if analyze_content:
            for response in result.responses:
                if not response.is_blocked and response.content_preview:
                    # We need the full content, not just preview - fetch again
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        try:
                            async with session.get(url) as resp:
                                if resp.status == 200:
                                    html = await resp.text()
                                    result.content_analysis = self.analyze_content(html, url)
                        except Exception:
                            pass
                    break

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _generate_summary(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate a summary of the simulation results."""
        total = len(result.responses)
        blocked_count = sum(1 for r in result.responses if r.is_blocked)
        robots_blocked = sum(1 for blocked in result.robots_txt_blocks.values() if blocked)
        meaningful_count = sum(1 for r in result.responses if r.has_meaningful_content)

        # Group by block reason
        block_reasons: Dict[str, List[str]] = {}
        for r in result.responses:
            if r.is_blocked and r.block_reason:
                if r.block_reason not in block_reasons:
                    block_reasons[r.block_reason] = []
                block_reasons[r.block_reason].append(r.crawler.name)

        # Check for content differences
        titles = set(r.title for r in result.responses if r.title and not r.is_blocked)
        content_lengths = [r.content_length for r in result.responses if not r.is_blocked]
        has_content_variation = len(titles) > 1 or (
            content_lengths and max(content_lengths) - min(content_lengths) > 1000
        )

        summary = {
            "total_crawlers_tested": total,
            "crawlers_blocked": blocked_count,
            "crawlers_with_meaningful_content": meaningful_count,
            "robots_txt_blocks": robots_blocked,
            "block_reasons": block_reasons,
            "has_content_variation": has_content_variation,
            "accessibility_score": round((total - blocked_count) / total * 100, 1) if total > 0 else 0,
            "training_exposure": "high" if meaningful_count >= total * 0.8 else "medium" if meaningful_count >= total * 0.5 else "low",
        }

        # Add content analysis summary if available
        if result.content_analysis:
            summary["llm_readiness_score"] = result.content_analysis.llm_readiness_score
            summary["content_issues_count"] = len(result.content_analysis.issues)

        return summary


async def simulate_llm_crawlers(url: str, crawlers: Optional[List[str]] = None) -> SimulationResult:
    """
    Convenience function to run LLM crawler simulation.

    Args:
        url: URL to test
        crawlers: Optional list of crawler names to test (default: all)

    Returns:
        SimulationResult with detailed per-crawler results
    """
    simulator = LLMCrawlerSimulator()

    if crawlers:
        # Filter to requested crawlers
        crawler_set = set(c.lower() for c in crawlers)
        simulator.crawlers = [
            c for c in KNOWN_LLM_CRAWLERS
            if c.name.lower() in crawler_set
        ]

    return await simulator.simulate(url)


# Crawler categories for robots.txt generation
CRAWLER_CATEGORIES = {
    "training": [
        "GPTBot",           # OpenAI training
        "ClaudeBot",        # Anthropic training
        "anthropic-ai",     # Anthropic alternative
        "Google-Extended",  # Google AI training
        "CCBot",            # Common Crawl (used by many)
        "Bytespider",       # ByteDance
        "Meta-ExternalAgent",  # Meta AI training
    ],
    "inference": [
        "ChatGPT-User",     # ChatGPT browsing (not training)
        "PerplexityBot",    # Perplexity search
        "Amazonbot",        # Alexa/Amazon (mixed use)
    ],
    "all": [c.robots_txt_token for c in KNOWN_LLM_CRAWLERS],
}


def generate_robots_txt_rules(
    block_crawlers: Optional[List[str]] = None,
    block_category: Optional[str] = None,
    block_paths: Optional[List[str]] = None,
    allow_paths: Optional[List[str]] = None,
) -> str:
    """
    Generate robots.txt rules for LLM crawler management.

    Args:
        block_crawlers: List of specific crawler tokens to block (e.g., ["GPTBot", "ClaudeBot"])
        block_category: Block a category: "training", "inference", or "all"
        block_paths: Paths to block (default: ["/"] for all)
        allow_paths: Paths to explicitly allow (useful for exceptions)

    Returns:
        robots.txt formatted string
    """
    if block_paths is None:
        block_paths = ["/"]

    crawlers_to_block = []

    if block_category:
        if block_category not in CRAWLER_CATEGORIES:
            raise ValueError(f"Unknown category: {block_category}. Use: {list(CRAWLER_CATEGORIES.keys())}")
        crawlers_to_block = CRAWLER_CATEGORIES[block_category]
    elif block_crawlers:
        crawlers_to_block = block_crawlers
    else:
        # Default to blocking all training crawlers
        crawlers_to_block = CRAWLER_CATEGORIES["training"]

    lines = [
        "# LLM Crawler Rules",
        "# Generated by website-analyzer",
        f"# Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "#",
        "# For more information about these crawlers:",
        "# - OpenAI GPTBot: https://platform.openai.com/docs/gptbot",
        "# - Anthropic: https://www.anthropic.com/robots-txt",
        "# - Google AI: https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers",
        "# - Common Crawl: https://commoncrawl.org/faq/",
        "",
    ]

    for crawler in crawlers_to_block:
        lines.append(f"User-agent: {crawler}")

        # Add allow paths first (more specific)
        if allow_paths:
            for path in allow_paths:
                lines.append(f"Allow: {path}")

        # Then disallow paths
        for path in block_paths:
            lines.append(f"Disallow: {path}")

        lines.append("")  # Blank line between sections

    return "\n".join(lines)


def generate_robots_txt_block_all() -> str:
    """Generate robots.txt rules to block ALL known LLM crawlers."""
    return generate_robots_txt_rules(block_category="all")


def generate_robots_txt_block_training() -> str:
    """Generate robots.txt rules to block training crawlers but allow inference/search."""
    return generate_robots_txt_rules(block_category="training")


def generate_robots_txt_selective(
    block: Optional[List[str]] = None,
    allow: Optional[List[str]] = None,
) -> str:
    """
    Generate robots.txt rules with selective blocking.

    Args:
        block: List of crawler names to block
        allow: List of crawler names to explicitly allow (not blocked)

    Returns:
        robots.txt formatted string
    """
    all_crawlers = set(c.robots_txt_token for c in KNOWN_LLM_CRAWLERS)

    if allow:
        # Block all except those in allow list
        crawlers_to_block = [c for c in all_crawlers if c not in allow]
    elif block:
        crawlers_to_block = block
    else:
        crawlers_to_block = list(all_crawlers)

    return generate_robots_txt_rules(block_crawlers=crawlers_to_block)


@dataclass
class RobotsTxtAnalysis:
    """Analysis of a site's current robots.txt for LLM crawlers."""
    has_robots_txt: bool
    blocks_by_crawler: Dict[str, bool]
    training_crawlers_blocked: int
    inference_crawlers_blocked: int
    total_blocked: int
    recommendations: List[str]
    suggested_additions: Optional[str] = None


def analyze_robots_txt_for_llm(robots_txt_content: Optional[str]) -> RobotsTxtAnalysis:
    """
    Analyze existing robots.txt for LLM crawler rules.

    Args:
        robots_txt_content: Content of robots.txt file

    Returns:
        RobotsTxtAnalysis with current status and recommendations
    """
    if not robots_txt_content:
        return RobotsTxtAnalysis(
            has_robots_txt=False,
            blocks_by_crawler={c.robots_txt_token: False for c in KNOWN_LLM_CRAWLERS},
            training_crawlers_blocked=0,
            inference_crawlers_blocked=0,
            total_blocked=0,
            recommendations=[
                "No robots.txt found. Your site is fully accessible to all LLM crawlers.",
                "Consider adding robots.txt rules if you want to opt out of LLM training.",
            ],
            suggested_additions=generate_robots_txt_block_training(),
        )

    # Parse robots.txt for each crawler
    blocks_by_crawler = {}
    for crawler in KNOWN_LLM_CRAWLERS:
        is_blocked = _check_robots_txt_blocks(robots_txt_content, crawler.robots_txt_token)
        blocks_by_crawler[crawler.robots_txt_token] = is_blocked

    training_blocked = sum(
        1 for c in CRAWLER_CATEGORIES["training"]
        if blocks_by_crawler.get(c, False)
    )
    inference_blocked = sum(
        1 for c in CRAWLER_CATEGORIES["inference"]
        if blocks_by_crawler.get(c, False)
    )
    total_blocked = sum(1 for blocked in blocks_by_crawler.values() if blocked)

    recommendations = []
    suggested = None

    if total_blocked == 0:
        recommendations.append("Your robots.txt does not block any LLM crawlers.")
        recommendations.append("If you want to opt out of LLM training, add rules for training crawlers.")
        suggested = generate_robots_txt_block_training()
    elif training_blocked < len(CRAWLER_CATEGORIES["training"]):
        missing = [c for c in CRAWLER_CATEGORIES["training"] if not blocks_by_crawler.get(c, False)]
        recommendations.append(f"Some training crawlers are not blocked: {', '.join(missing)}")
        suggested = generate_robots_txt_rules(block_crawlers=missing)
    else:
        recommendations.append("All known training crawlers are blocked.")

    if training_blocked > 0 and inference_blocked == 0:
        recommendations.append("Training crawlers blocked, but inference/search bots allowed. This is a common configuration.")

    return RobotsTxtAnalysis(
        has_robots_txt=True,
        blocks_by_crawler=blocks_by_crawler,
        training_crawlers_blocked=training_blocked,
        inference_crawlers_blocked=inference_blocked,
        total_blocked=total_blocked,
        recommendations=recommendations,
        suggested_additions=suggested,
    )


def _check_robots_txt_blocks(robots_txt: str, crawler_token: str) -> bool:
    """Check if a specific crawler is blocked by robots.txt content."""
    lines = robots_txt.lower().split('\n')
    current_agent = None
    is_relevant = False

    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue

        if line.startswith('user-agent:'):
            agent = line.split(':', 1)[1].strip()
            current_agent = agent
            is_relevant = (agent == '*' or agent == crawler_token.lower())

        elif line.startswith('disallow:') and is_relevant:
            path = line.split(':', 1)[1].strip()
            if path == '/' or path == '/*':
                return True

    return False
