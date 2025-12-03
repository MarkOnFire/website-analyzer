"""Basic web crawler using Crawl4AI AsyncWebCrawler.

This module provides fundamental crawling capabilities for single URL crawling
with page artifact storage (raw HTML, cleaned HTML, markdown, metadata).
"""

import json
import posixpath
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urljoin, urlparse, urlunparse, urlencode

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CacheMode, CrawlerRunConfig


class BasicCrawler:
    """Basic web crawler using Crawl4AI AsyncWebCrawler.

    Provides single-URL crawling with artifact storage (HTML, markdown, metadata).
    Respects robots.txt and implements configurable page timeout.
    """

    def __init__(self, config: Optional[CrawlerRunConfig] = None) -> None:
        """Initialize crawler with optional custom configuration.

        Args:
            config: Optional CrawlerRunConfig. If None, uses default configuration.
        """
        self.config = config or self._default_config()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a URL for consistent comparison and storage.

        Normalization steps:
        - Require http/https scheme
        - Lowercase scheme and hostname
        - Drop fragments
        - Remove default ports (80/443)
        - Normalize path, removing duplicate slashes
        - Sort query parameters for stable ordering

        Args:
            url: Raw URL to normalize.

        Returns:
            Normalized URL string.

        Raises:
            ValueError: If the URL is empty, missing host, or uses an unsupported scheme.
        """
        if not url:
            raise ValueError("URL cannot be empty")

        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme or 'missing'}")
        if not parsed.hostname:
            raise ValueError("URL must include hostname")

        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower()
        port = parsed.port

        # Remove default ports for scheme
        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc = f"{hostname}:{port}"
        else:
            netloc = hostname

        # Normalize path (collapse duplicate slashes, handle '.' segments)
        path = parsed.path or "/"
        normalized_path = posixpath.normpath(path)
        normalized_path = re.sub(r"/{2,}", "/", normalized_path)
        if normalized_path == ".":
            normalized_path = "/"
        if not normalized_path.startswith("/"):
            normalized_path = f"/{normalized_path}"
        if normalized_path != "/" and normalized_path.endswith("/"):
            normalized_path = normalized_path.rstrip("/")

        # Stable query ordering
        query = ""
        if parsed.query:
            query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))

        return urlunparse((scheme, netloc, normalized_path, "", query, ""))

    @staticmethod
    def deduplicate_urls(urls: list[str]) -> list[str]:
        """Deduplicate and normalize a collection of URLs, preserving order.

        Invalid URLs are skipped.
        """
        seen: set[str] = set()
        unique: list[str] = []
        for url in urls:
            try:
                normalized = BasicCrawler.normalize_url(url)
            except ValueError:
                continue
            if normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)
        return unique

    @staticmethod
    def _default_config() -> CrawlerRunConfig:
        """Create default crawler configuration.

        Configuration:
        - cache_mode: BYPASS (no caching)
        - check_robots_txt: True (respect robots.txt)
        - wait_until: domcontentloaded (wait for DOM ready)
        - page_timeout: 60000ms (60 seconds default timeout)
        - screenshot: False (no screenshots)
        - capture_network_requests: False (no network capture)

        Returns:
            CrawlerRunConfig with sensible defaults
        """
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            check_robots_txt=True,
            wait_until="domcontentloaded",
            page_timeout=60_000,
            screenshot=False,
            capture_network_requests=False,
        )

    async def crawl_url(self, url: str) -> "CrawlResult":
        """Crawl a single URL and return the result.

        Args:
            url: URL to crawl

        Returns:
            CrawlResult containing HTML, markdown, status code, and metadata

        Raises:
            Exception: If crawl fails (network error, timeout, etc.)
        """
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url, config=self.config)
            return result

    @staticmethod
    def filter_internal_links(base_url: str, links: list[str]) -> list[str]:
        """Return normalized, deduplicated internal links for a base URL."""
        normalized_base = BasicCrawler.normalize_url(base_url)
        base_parsed = urlparse(normalized_base)
        base_port = base_parsed.port
        base_host = base_parsed.hostname

        candidates: list[str] = []
        for link in links:
            if not link:
                continue
            lower = link.lower()
            if lower.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if lower.startswith("#"):
                continue
            try:
                absolute = urljoin(normalized_base, link)
                normalized = BasicCrawler.normalize_url(absolute)
                parsed = urlparse(normalized)
            except ValueError:
                continue

            # Internal if hostname matches and port matches (including default/None)
            if parsed.hostname != base_host:
                continue
            parsed_port = parsed.port
            if (parsed_port or None) != (base_port or None):
                continue

            candidates.append(normalized)

        return BasicCrawler.deduplicate_urls(candidates)

    @staticmethod
    def save_page_artifacts(
        result: "CrawlResult",
        output_dir: Path,
    ) -> None:
        """Save crawl result artifacts to directory.

        Saves four artifacts from the crawl result:
        - raw.html: Raw HTML from the page
        - cleaned.html: Cleaned/processed HTML
        - content.md: Markdown conversion of page content
        - metadata.json: Metadata (URL, status code, links, timestamp)

        Args:
            result: CrawlResult from crawler.arun()
            output_dir: Directory to save artifacts to (created if needed)
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw HTML
        (output_dir / "raw.html").write_text(
            result.html or "", encoding="utf-8"
        )

        # Save cleaned HTML
        (output_dir / "cleaned.html").write_text(
            result.cleaned_html or "", encoding="utf-8"
        )

        # Save markdown
        (output_dir / "content.md").write_text(
            result.markdown or "", encoding="utf-8"
        )

        # Prepare links
        links: list[str] = []
        if result.url:
            links = BasicCrawler.filter_internal_links(
                base_url=result.url, links=result.links or []
            )

        # Save metadata
        metadata = {
            "url": result.url,
            "status_code": result.status_code,
            "redirected_url": result.redirected_url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "links": links,
            "title": result.title,
        }
        (output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
