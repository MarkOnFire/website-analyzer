#!/usr/bin/env python3.11
"""Test specific archive.org URL for WordPress embed bug."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler

# Flexible patterns to catch WordPress embed code variations
PATTERNS = {
    "wordpress-media-embed-full": r'\[\[{"fid":"[^"]*".*?"type":"media".*?}}]]',
    "wordpress-fid-opening": r'\[\[{"fid":"[0-9]+[″"]',
    "field-deltas-structure": r'"field_deltas":\{[^}]*"format":',
    "view-mode-fields": r'"view_mode":"[^"]*","fields":\{',
}

async def main():
    url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"

    print(f"🔍 Testing archived page for WordPress embed bug...")
    print(f"URL: {url}\n")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)

        if not result.html:
            print("❌ Failed to fetch page")
            return

        print(f"✅ Page fetched ({len(result.html)} bytes)")

        # Check for patterns
        page_matches = {}
        for pattern_name, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, result.html, re.IGNORECASE | re.DOTALL))
            if matches:
                page_matches[pattern_name] = matches

        if page_matches:
            print(f"\n✅ FOUND {sum(len(v) for v in page_matches.values())} MATCH(ES)!\n")

            for pattern_name, matches in page_matches.items():
                print(f"Pattern '{pattern_name}': {len(matches)} matches")

                # Show first match with context
                if matches:
                    match = matches[0]
                    context_start = max(0, match.start() - 200)
                    context_end = min(len(result.html), match.end() + 200)
                    context = result.html[context_start:context_end]

                    # Clean for display
                    clean_context = context.replace('\n', ' ').replace('\t', ' ')
                    clean_context = re.sub(r'\s+', ' ', clean_context)

                    print(f"\nFirst match context:")
                    print(f"...{clean_context[:500]}...")
                    print()
        else:
            print("\n❌ No WordPress embed patterns found")

            # Debug: Show a sample of the HTML
            print("\n📝 HTML sample (first 1000 chars):")
            print(result.html[:1000])

if __name__ == "__main__":
    asyncio.run(main())
