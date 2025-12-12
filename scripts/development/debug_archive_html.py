#!/usr/bin/env python3.11
"""Debug: Search for ANY mention of fid, field_deltas, or similar in archive page."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler

async def main():
    url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"

    print(f"🔍 Searching for ANY fid/field references...\n")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)

        if not result.html:
            print("❌ Failed to fetch page")
            return

        html = result.html
        print(f"✅ Page fetched ({len(html)} bytes)\n")

        # Search for various patterns
        searches = [
            (r'fid["\']?\s*:', 'fid references'),
            (r'\[\[', 'double brackets'),
            (r'field_deltas', 'field_deltas'),
            (r'view_mode', 'view_mode'),
            (r'type["\']?\s*:\s*["\']media', 'type:media'),
        ]

        for pattern, description in searches:
            matches = list(re.finditer(pattern, html, re.IGNORECASE))
            print(f"{description}: {len(matches)} matches")

            if matches and len(matches) < 20:  # Show details if not too many
                for i, match in enumerate(matches[:5], 1):
                    start = max(0, match.start() - 100)
                    end = min(len(html), match.end() + 100)
                    context = html[start:end].replace('\n', ' ')
                    context = re.sub(r'\s+', ' ', context)
                    print(f"  {i}. ...{context}...")
                print()

        # Also search for the specific pattern from the test doc
        print("\n🔎 Searching for pattern from test-project-bug-hunter.md:")
        test_pattern = r'\[\[.*?fid.*?view_mode.*?\]\]'
        test_matches = list(re.finditer(test_pattern, html, re.IGNORECASE | re.DOTALL))
        print(f"Found: {len(test_matches)} matches")

        if test_matches:
            for i, match in enumerate(test_matches[:3], 1):
                print(f"\nMatch {i}:")
                print(match.group(0)[:500])

if __name__ == "__main__":
    asyncio.run(main())
