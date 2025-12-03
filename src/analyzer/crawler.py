"""Basic web crawler using Crawl4AI AsyncWebCrawler.

This module provides fundamental crawling capabilities for single URL crawling
with page artifact storage (raw HTML, cleaned HTML, markdown, metadata).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

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

        # Save metadata
        metadata = {
            "url": result.url,
            "status_code": result.status_code,
            "redirected_url": result.redirected_url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "links": result.links or [],
            "title": result.title,
        }
        (output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
