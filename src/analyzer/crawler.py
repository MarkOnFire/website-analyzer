"""Basic web crawler using Crawl4AI AsyncWebCrawler.

This module provides fundamental crawling capabilities for single URL crawling
with page artifact storage (raw HTML, cleaned HTML, markdown, metadata).
"""

import asyncio
import json
import posixpath
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urljoin, urlparse, urlunparse, urlencode
from urllib.robotparser import RobotFileParser

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CacheMode, CrawlerRunConfig
from .workspace import slugify_url


class BasicCrawler:
    """Basic web crawler using Crawl4AI AsyncWebCrawler.

    Provides single-URL crawling with artifact storage (HTML, markdown, metadata).
    Respects robots.txt and implements configurable page timeout.
    """

    class InterruptSignal(Exception):
        """Internal sentinel for interrupt handling."""

    DEFAULT_MAX_PAGES = 1000
    DEFAULT_MAX_DEPTH: int | None = None
    DEFAULT_MAX_CONCURRENCY = 5
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.5

    def __init__(
        self,
        config: Optional[CrawlerRunConfig] = None,
        max_pages: int = DEFAULT_MAX_PAGES,
        max_depth: int | None = DEFAULT_MAX_DEPTH,
        page_timeout_ms: int = 60_000,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        progress_interval: int = 10,
    ) -> None:
        """Initialize crawler with optional custom configuration.

        Args:
            config: Optional CrawlerRunConfig. If None, uses default configuration.
            max_pages: Maximum pages to process per crawl session (default 1000).
            max_depth: Optional maximum crawl depth (None for unlimited).
            page_timeout_ms: Per-page timeout in milliseconds (default 60_000).
            max_concurrency: Maximum concurrent crawl requests (default 5).
            max_retries: Maximum retry attempts on network errors (default 3).
            backoff_factor: Base backoff delay in seconds (default 0.5).
            progress_interval: Emit progress callback every N pages (default 10).
        """
        self.config = config or self._default_config(page_timeout_ms=page_timeout_ms)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.page_timeout_ms = page_timeout_ms
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.progress_interval = progress_interval

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
    def _default_config(page_timeout_ms: int = 60_000) -> CrawlerRunConfig:
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
            page_timeout=page_timeout_ms,
            screenshot=False,
            capture_network_requests=False,
        )

    async def crawl_url(self, url: str) -> "CrawlResult":
        """Crawl a single URL and return the result.

        Args:
            url: URL to crawl
            Robots:
                Respects robots.txt per config (check_robots_txt=True by default)

        Returns:
            CrawlResult containing HTML, markdown, status code, and metadata

        Raises:
            Exception: If crawl fails (network error, timeout, etc.)
        """
        async with AsyncWebCrawler() as crawler:
            result = await self._crawl_with_retry(crawler, url)
            return result

    async def _crawl_with_retry(
        self, crawler: AsyncWebCrawler, url: str
    ) -> "CrawlResult":
        """Run crawler.arun with retry/backoff."""
        attempt = 0
        delay = self.backoff_factor
        while True:
            try:
                return await crawler.arun(url, config=self.config)
            except KeyboardInterrupt:
                raise BasicCrawler.InterruptSignal()
            except Exception:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    async def crawl_urls(
        self,
        urls: list[str],
        max_concurrency: int | None = None,
        rate_limit_per_sec: float | None = None,
        progress_callback: Optional[callable] = None,
        on_interrupt: Optional[callable] = None,
    ) -> list["CrawlResult"]:
        """Crawl multiple URLs concurrently with optional rate limiting.

        Args:
            urls: URLs to crawl.
            max_concurrency: Max concurrent requests (default uses crawler setting).
            rate_limit_per_sec: Optional rate limit for request starts (requests/second).
            progress_callback: Optional callable(page_index:int, total:int) for progress.
            on_interrupt: Optional callable(partial_results:list[CrawlResult]) on KeyboardInterrupt.

        Returns:
            List of CrawlResult objects in the same order as input URLs.
        """
        if not urls:
            return []

        concurrency = max_concurrency or self.max_concurrency
        semaphore = asyncio.Semaphore(concurrency)
        rate_interval = 1 / rate_limit_per_sec if rate_limit_per_sec else 0
        rate_lock = asyncio.Lock()
        last_start = 0.0
        loop = asyncio.get_event_loop()
        total = len(urls)
        completed = 0
        interval = self.progress_interval

        async def fetch(url: str) -> "CrawlResult":
            nonlocal last_start
            async with semaphore:
                if rate_interval:
                    async with rate_lock:
                        now = loop.time()
                        wait_for = max(0, last_start + rate_interval - now)
                        if wait_for > 0:
                            await asyncio.sleep(wait_for)
                        last_start = loop.time()
                result = await self._crawl_with_retry(crawler, url)
                return result

        async with AsyncWebCrawler() as crawler:
            async def fetch_with_index(idx: int, url: str):
                res = await fetch(url)
                return idx, res

            tasks = [
                asyncio.create_task(fetch_with_index(idx, url))
                for idx, url in enumerate(urls)
            ]

            results: list["CrawlResult"] = [None] * total  # type: ignore

            try:
                for task in asyncio.as_completed(tasks):
                    idx, res = await task
                    results[idx] = res
                    completed += 1
                    if progress_callback and interval > 0 and completed % interval == 0:
                        try:
                            progress_callback(completed, total)
                        except Exception:
                            pass
            except BasicCrawler.InterruptSignal:
                partial = [r for r in results if r is not None]
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                if on_interrupt:
                    try:
                        on_interrupt(partial)
                    except Exception:
                        pass
                    return partial
                raise KeyboardInterrupt()

            return results

    @staticmethod
    def _build_robot_parser(robots_txt: str | None) -> RobotFileParser | None:
        """Create a RobotFileParser from robots.txt content."""
        if not robots_txt:
            return None
        rp = RobotFileParser()
        rp.parse(robots_txt.splitlines())
        return rp

    @staticmethod
    def is_allowed_by_robots(
        url: str, robots_txt: str | None, user_agent: str = "*"
    ) -> bool:
        """Check if a URL is allowed by robots.txt content.

        If no robots_txt is provided, this returns True.
        """
        parser = BasicCrawler._build_robot_parser(robots_txt)
        if parser is None:
            return True
        try:
            return parser.can_fetch(user_agent, url)
        except Exception:
            return True

    @staticmethod
    def filter_internal_links(
        base_url: str,
        links: list[str],
        robots_txt: str | None = None,
        user_agent: str = "*",
        max_pages: int | None = None,
        current_depth: int = 0,
        max_depth: int | None = None,
    ) -> list[str]:
        """Return normalized, deduplicated internal links for a base URL."""
        if max_depth is not None and current_depth >= max_depth:
            return []

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

            # Robots.txt enforcement
            if not BasicCrawler.is_allowed_by_robots(
                normalized, robots_txt, user_agent=user_agent
            ):
                continue

            candidates.append(normalized)

        unique = BasicCrawler.deduplicate_urls(candidates)
        if max_pages is not None:
            return unique[: max_pages if max_pages > 0 else 0]
        return unique

    @staticmethod
    def save_page_artifacts(
        result: "CrawlResult",
        output_dir: Path,
        max_pages: int | None = None,
        user_agent: str = "*",
        robots_txt: str | None = None,
        current_depth: int = 0,
        max_depth: int | None = None,
        page_timeout_ms: int | None = None,
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
                base_url=result.url,
                links=result.links or [],
                robots_txt=robots_txt,
                user_agent=user_agent,
                max_pages=max_pages,
                current_depth=current_depth,
                max_depth=max_depth,
            )

        # Save metadata
        metadata = {
            "url": result.url,
            "status_code": result.status_code,
            "redirected_url": result.redirected_url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "links": links,
            "title": result.title,
            "page_timeout_ms": page_timeout_ms,
            "headers": getattr(result, "headers", None),
        }
        (output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def save_snapshot(
        self,
        result: "CrawlResult",
        snapshot_dir: Path,
        *,
        user_agent: str = "*",
        robots_txt: str | None = None,
        current_depth: int = 0,
        include_sitemap: bool = True,
        summary: dict | None = None,
    ) -> Path:
        """Save a single page snapshot within a snapshot directory.

        Creates a per-page directory under snapshot_dir/pages using the URL slug.
        """
        pages_dir = snapshot_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        if not result.url:
            raise ValueError("CrawlResult.url is required for snapshot saving")

        slug = slugify_url(result.url)
        page_dir = pages_dir / slug
        page_dir.mkdir(parents=True, exist_ok=True)

        self.save_page_artifacts(
            result,
            page_dir,
            user_agent=user_agent,
            robots_txt=robots_txt,
            current_depth=current_depth,
            page_timeout_ms=self.page_timeout_ms,
        )

        if include_sitemap:
            sitemap_path = snapshot_dir / "sitemap.json"
            pages = BasicCrawler.filter_internal_links(
                result.url,
                result.links or [],
                robots_txt=robots_txt,
                user_agent=user_agent,
                max_pages=self.max_pages,
                current_depth=current_depth,
                max_depth=self.max_depth,
            )
            sitemap = {
                "root": result.url,
                "pages": pages,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
            sitemap_path.write_text(json.dumps(sitemap, indent=2), encoding="utf-8")

        # Write/augment summary
        summary_path = snapshot_dir / "summary.json"
        summary_data = summary or {}
        summary_data.setdefault("generated_at", datetime.utcnow().isoformat() + "Z")
        summary_data.setdefault("total_pages", len(summary_data.get("pages", [])))
        summary_data.setdefault("errors", summary_data.get("errors", []))
        summary_data.setdefault("duration_seconds", summary_data.get("duration_seconds", 0))
        summary_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")

        return page_dir
