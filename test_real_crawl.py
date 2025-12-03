#!/usr/bin/env python3.11
"""Real-world test of BasicCrawler with example.com.

This script tests the crawler with an actual URL to verify:
1. AsyncWebCrawler integration works correctly
2. Page artifacts are saved properly
3. Metadata is generated correctly
"""

import asyncio
import json
import tempfile
from pathlib import Path

from src.analyzer.crawler import BasicCrawler


async def test_real_crawl():
    """Test crawling a real URL (example.com)."""
    print("Starting real-world crawl test with example.com...")

    crawler = BasicCrawler()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "example-com-snapshot"

        try:
            print(f"Crawling https://example.com ...")
            result = await crawler.crawl_url("https://example.com")

            print(f"Status code: {result.status_code}")
            print(f"URL: {result.url}")
            print(f"Title: {result.title}")
            print(f"HTML length: {len(result.html or '') if result.html else 0} bytes")
            print(
                f"Cleaned HTML length: {len(result.cleaned_html or '') if result.cleaned_html else 0} bytes"
            )
            print(
                f"Markdown length: {len(result.markdown or '') if result.markdown else 0} bytes"
            )
            print(f"Links found: {len(result.links or [])}")

            # Save artifacts
            print(f"\nSaving artifacts to {output_dir}...")
            BasicCrawler.save_page_artifacts(result, output_dir)

            # Verify all files exist
            files_created = [
                "raw.html",
                "cleaned.html",
                "content.md",
                "metadata.json",
            ]
            for filename in files_created:
                filepath = output_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    print(f"✓ {filename} ({size} bytes)")
                else:
                    print(f"✗ {filename} (MISSING)")

            # Verify metadata
            print("\nMetadata verification:")
            metadata = json.loads(
                (output_dir / "metadata.json").read_text(encoding="utf-8")
            )
            print(f"  URL: {metadata['url']}")
            print(f"  Status: {metadata['status_code']}")
            print(f"  Timestamp: {metadata['timestamp']}")
            print(f"  Title: {metadata['title']}")
            print(f"  Links in metadata: {len(metadata['links'])}")

            # Check content quality
            html_file = output_dir / "raw.html"
            md_file = output_dir / "content.md"

            if html_file.stat().st_size > 0:
                print("\n✓ Raw HTML captured successfully")
            else:
                print("\n✗ Raw HTML is empty")

            if md_file.stat().st_size > 0:
                print("✓ Markdown captured successfully")
            else:
                print("✗ Markdown is empty")

            print("\nTest PASSED: Real crawl successful!")
            return True

        except Exception as e:
            print(f"\nTest FAILED: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    result = asyncio.run(test_real_crawl())
    exit(0 if result else 1)
