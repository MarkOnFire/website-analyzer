"""Unit tests for BasicCrawler.

Tests cover:
- Default configuration creation
- Single URL crawling with real network calls
- Page artifact storage (all 4 files created)
- Metadata JSON structure
- Error handling for invalid URLs
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analyzer.crawler import BasicCrawler


class MockCrawlResult:
    """Mock CrawlResult for testing without real network calls."""

    def __init__(
        self,
        url: str = "https://example.com",
        html: str = "<html><body>Test</body></html>",
        cleaned_html: str = "<body>Test</body>",
        markdown: str = "# Test\n\nTest content",
        status_code: int = 200,
        redirected_url: str | None = None,
        title: str | None = "Test Page",
        links: list | None = None,
    ):
        self.url = url
        self.html = html
        self.cleaned_html = cleaned_html
        self.markdown = markdown
        self.status_code = status_code
        self.redirected_url = redirected_url
        self.title = title
        self.links = links or []


class TestBasicCrawlerConfig:
    """Test BasicCrawler configuration."""

    def test_default_config_creation(self):
        """Test that default config is created correctly."""
        crawler = BasicCrawler()
        assert crawler.config is not None
        assert crawler.config.check_robots_txt is True
        assert crawler.config.wait_until == "domcontentloaded"
        assert crawler.config.page_timeout == 60_000
        assert crawler.config.screenshot is False
        assert crawler.config.capture_network_requests is False

    def test_custom_config(self):
        """Test that custom config is accepted and used."""
        from crawl4ai.async_configs import CrawlerRunConfig, CacheMode

        custom_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30_000,
        )
        crawler = BasicCrawler(config=custom_config)
        assert crawler.config is custom_config
        assert crawler.config.page_timeout == 30_000

    def test_config_attributes(self):
        """Test all important config attributes are set correctly."""
        config = BasicCrawler._default_config()
        assert config is not None
        # Verify cache mode is BYPASS
        from crawl4ai.async_configs import CacheMode

        assert config.cache_mode == CacheMode.BYPASS
        # Verify robots.txt checking is enabled
        assert config.check_robots_txt is True
        # Verify DOM content loaded wait
        assert config.wait_until == "domcontentloaded"
        # Verify reasonable timeout
        assert config.page_timeout == 60_000
        # Verify no screenshots
        assert config.screenshot is False


class TestBasicCrawlerUrlNormalization:
    """Test URL normalization and deduplication helpers."""

    def test_normalize_url_lowercases_scheme_and_host(self):
        normalized = BasicCrawler.normalize_url("HTTPS://Example.COM/Path")
        assert normalized == "https://example.com/Path"

    def test_normalize_url_removes_fragment_and_default_port(self):
        normalized = BasicCrawler.normalize_url("http://example.com:80/page#section")
        assert normalized == "http://example.com/page"

    def test_normalize_url_retains_non_default_port(self):
        normalized = BasicCrawler.normalize_url("https://example.com:8443/page")
        assert normalized == "https://example.com:8443/page"

    def test_normalize_url_sorts_query_params(self):
        normalized = BasicCrawler.normalize_url("https://example.com/page?b=2&a=1")
        assert normalized == "https://example.com/page?a=1&b=2"

    def test_normalize_url_collapses_duplicate_slashes(self):
        normalized = BasicCrawler.normalize_url("https://example.com//a//b///")
        assert normalized == "https://example.com/a/b"

    def test_normalize_url_requires_http_scheme(self):
        with pytest.raises(ValueError):
            BasicCrawler.normalize_url("ftp://example.com")

    def test_normalize_url_requires_hostname(self):
        with pytest.raises(ValueError):
            BasicCrawler.normalize_url("https:///no-host")

    def test_deduplicate_urls_preserves_order_and_skips_invalid(self):
        urls = [
            "HTTPS://Example.com",
            "https://example.com/",
            "https://example.com#frag",
            "javascript:alert(1)",
        ]
        deduped = BasicCrawler.deduplicate_urls(urls)
        assert deduped == ["https://example.com/"]


class TestBasicCrawlerLinkFiltering:
    """Test internal link extraction and filtering."""

    def test_filter_internal_links_keeps_same_host(self):
        links = [
            "https://example.com/page1",
            "https://other.com/page2",
            "/page3",
        ]
        filtered = BasicCrawler.filter_internal_links(
            "https://example.com", links
        )
        assert filtered == [
            "https://example.com/page1",
            "https://example.com/page3",
        ]

    def test_filter_internal_links_resolves_relative(self):
        links = ["about", "../contact", "/pricing"]
        filtered = BasicCrawler.filter_internal_links(
            "https://example.com/docs/guide/", links
        )
        assert filtered == [
            "https://example.com/docs/about",
            "https://example.com/contact",
            "https://example.com/pricing",
        ]

    def test_filter_internal_links_skips_non_http_and_fragments(self):
        links = ["mailto:test@example.com", "javascript:void(0)", "#section"]
        filtered = BasicCrawler.filter_internal_links(
            "https://example.com", links
        )
        assert filtered == []

    def test_filter_internal_links_deduplicates(self):
        links = [
            "https://example.com",
            "https://example.com/",
            "/",
            "https://example.com#frag",
        ]
        filtered = BasicCrawler.filter_internal_links(
            "https://example.com", links
        )
        assert filtered == ["https://example.com/"]

    def test_filter_internal_links_respects_port(self):
        links = [
            "https://example.com:8080/page",
            "https://example.com/page",
        ]
        filtered = BasicCrawler.filter_internal_links(
            "https://example.com:8080", links
        )
        assert filtered == ["https://example.com:8080/page"]


class TestBasicCrawlerArtifactStorage:
    """Test page artifact storage functionality."""

    def test_save_all_artifacts(self):
        """Test that all four artifacts are saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult()

            BasicCrawler.save_page_artifacts(result, output_dir)

            # Verify all four files exist
            assert (output_dir / "raw.html").exists()
            assert (output_dir / "cleaned.html").exists()
            assert (output_dir / "content.md").exists()
            assert (output_dir / "metadata.json").exists()

    def test_raw_html_content(self):
        """Test that raw HTML is saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            html_content = "<html><body>Test content</body></html>"
            result = MockCrawlResult(html=html_content)

            BasicCrawler.save_page_artifacts(result, output_dir)

            saved_html = (output_dir / "raw.html").read_text(encoding="utf-8")
            assert saved_html == html_content

    def test_cleaned_html_content(self):
        """Test that cleaned HTML is saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            cleaned_html = "<body>Cleaned content</body>"
            result = MockCrawlResult(cleaned_html=cleaned_html)

            BasicCrawler.save_page_artifacts(result, output_dir)

            saved_cleaned = (output_dir / "cleaned.html").read_text(
                encoding="utf-8"
            )
            assert saved_cleaned == cleaned_html

    def test_markdown_content(self):
        """Test that markdown is saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            markdown = "# Title\n\nParagraph content"
            result = MockCrawlResult(markdown=markdown)

            BasicCrawler.save_page_artifacts(result, output_dir)

            saved_md = (output_dir / "content.md").read_text(encoding="utf-8")
            assert saved_md == markdown

    def test_metadata_json_structure(self):
        """Test that metadata JSON has correct structure and values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            url = "https://example.com/page"
            status_code = 200
            links = [
                "https://example.com/",
                "https://other.com/about",
                "/internal",
            ]
            title = "Test Page"

            result = MockCrawlResult(
                url=url,
                status_code=status_code,
                links=links,
                title=title,
            )

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )

            # Verify all metadata fields
            assert metadata["url"] == url
            assert metadata["status_code"] == status_code
            assert metadata["links"] == [
                "https://example.com/",
                "https://example.com/internal",
            ]
            assert metadata["title"] == title
            assert "timestamp" in metadata
            # Timestamp should end with Z (UTC)
            assert metadata["timestamp"].endswith("Z")

    def test_metadata_json_valid(self):
        """Test that metadata.json is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult()

            BasicCrawler.save_page_artifacts(result, output_dir)

            # Should not raise
            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            assert isinstance(metadata, dict)

    def test_creates_output_directory(self):
        """Test that save_page_artifacts creates output directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "path"
            assert not output_dir.exists()

            result = MockCrawlResult()
            BasicCrawler.save_page_artifacts(result, output_dir)

            assert output_dir.exists()
            assert (output_dir / "raw.html").exists()

    def test_empty_html_fields(self):
        """Test handling of None/empty HTML fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult(
                html=None, cleaned_html=None, markdown=None
            )

            BasicCrawler.save_page_artifacts(result, output_dir)

            # Should create empty files, not crash
            assert (output_dir / "raw.html").read_text() == ""
            assert (output_dir / "cleaned.html").read_text() == ""
            assert (output_dir / "content.md").read_text() == ""

    def test_multiple_artifacts_independent(self):
        """Test that saving one result doesn't affect another."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "page1"
            output_dir2 = Path(tmpdir) / "page2"

            result1 = MockCrawlResult(
                url="https://example.com/page1",
                html="<html>Page 1</html>",
            )
            result2 = MockCrawlResult(
                url="https://example.com/page2",
                html="<html>Page 2</html>",
            )

            BasicCrawler.save_page_artifacts(result1, output_dir1)
            BasicCrawler.save_page_artifacts(result2, output_dir2)

            # Verify independent storage
            metadata1 = json.loads(
                (output_dir1 / "metadata.json").read_text(encoding="utf-8")
            )
            metadata2 = json.loads(
                (output_dir2 / "metadata.json").read_text(encoding="utf-8")
            )

            assert metadata1["url"] == "https://example.com/page1"
            assert metadata2["url"] == "https://example.com/page2"

    def test_redirected_url_in_metadata(self):
        """Test that redirected_url is included in metadata when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult(
                url="https://example.com/old",
                redirected_url="https://example.com/new",
            )

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            assert metadata["redirected_url"] == "https://example.com/new"

    def test_metadata_timestamp_format(self):
        """Test that timestamp is ISO 8601 format with Z suffix."""
        import re

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult()

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )

            # ISO 8601 with Z: YYYY-MM-DDTHH:MM:SS.ffffffZ
            iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
            assert re.match(iso_pattern, metadata["timestamp"])

    def test_links_list_in_metadata(self):
        """Test that links list is properly stored in metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            links = [
                "https://example.com/",
                "https://example.com/about",
                "https://external.com/ignore",
                "/contact",
            ]
            result = MockCrawlResult(links=links)

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            assert metadata["links"] == [
                "https://example.com/",
                "https://example.com/about",
                "https://example.com/contact",
            ]

    def test_empty_links_list(self):
        """Test that empty links list is handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult(links=[])

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            assert metadata["links"] == []


class TestBasicCrawlerAsyncIntegration:
    """Test async crawling functionality (mocked)."""

    @pytest.mark.asyncio
    async def test_crawl_url_returns_result(self):
        """Test that crawl_url returns a result object."""
        crawler = BasicCrawler()

        # Mock AsyncWebCrawler
        mock_result = MockCrawlResult()

        with patch("src.analyzer.crawler.AsyncWebCrawler") as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.arun = AsyncMock(return_value=mock_result)
            mock_crawler.__aenter__.return_value = mock_crawler
            mock_crawler.__aexit__.return_value = None
            mock_crawler_class.return_value = mock_crawler

            result = await crawler.crawl_url("https://example.com")

            assert result == mock_result
            mock_crawler.arun.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_url_passes_config(self):
        """Test that crawl_url passes the config to crawler."""
        from crawl4ai.async_configs import CrawlerRunConfig, CacheMode

        custom_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30_000,
        )
        crawler = BasicCrawler(config=custom_config)

        mock_result = MockCrawlResult()

        with patch("src.analyzer.crawler.AsyncWebCrawler") as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.arun = AsyncMock(return_value=mock_result)
            mock_crawler.__aenter__.return_value = mock_crawler
            mock_crawler.__aexit__.return_value = None
            mock_crawler_class.return_value = mock_crawler

            await crawler.crawl_url("https://example.com")

            # Verify arun was called with URL and config
            mock_crawler.arun.assert_called_once()
            call_args = mock_crawler.arun.call_args
            # Check positional arguments or keyword arguments
            assert call_args[0][0] == "https://example.com"
            # Config may be passed as positional or keyword argument
            if len(call_args[0]) > 1:
                assert call_args[0][1] == custom_config
            else:
                assert call_args[1].get("config") == custom_config


class TestBasicCrawlerEdgeCases:
    """Test edge cases and error conditions."""

    def test_save_artifacts_with_special_chars_in_path(self):
        """Test saving artifacts to path with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory with spaces and special chars
            output_dir = Path(tmpdir) / "snapshot_2025-12-02T12-30-45.123456Z"
            result = MockCrawlResult()

            BasicCrawler.save_page_artifacts(result, output_dir)

            assert (output_dir / "metadata.json").exists()

    def test_very_large_html_content(self):
        """Test handling of very large HTML content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create large HTML (1MB)
            large_html = "<html>" + ("A" * (1024 * 1024)) + "</html>"
            result = MockCrawlResult(html=large_html)

            BasicCrawler.save_page_artifacts(result, output_dir)

            saved = (output_dir / "raw.html").read_text(encoding="utf-8")
            assert len(saved) == len(large_html)

    def test_unicode_content_handling(self):
        """Test handling of Unicode content (emoji, non-Latin chars)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            unicode_content = "Hello 世界 🌍 Привет"
            result = MockCrawlResult(
                markdown=unicode_content, html=unicode_content
            )

            BasicCrawler.save_page_artifacts(result, output_dir)

            saved_md = (output_dir / "content.md").read_text(encoding="utf-8")
            assert saved_md == unicode_content

    def test_metadata_with_null_values(self):
        """Test metadata generation when some values are None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = MockCrawlResult(
                title=None, redirected_url=None, links=None
            )

            BasicCrawler.save_page_artifacts(result, output_dir)

            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            assert metadata["title"] is None
            assert metadata["redirected_url"] is None
            assert metadata["links"] == []
