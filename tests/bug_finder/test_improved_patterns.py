#!/usr/bin/env python3.11
"""Test improved patterns on the known-buggy archived page."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler

# Import patterns from updated scanner - using Unicode escapes
QUOTE_PATTERN = r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]'

PATTERNS = {
    # Catches opening structure with fid (very broad)
    "wordpress_embed_opening": (
        r'\[\[\s*\{\s*' + QUOTE_PATTERN + r'fid' + QUOTE_PATTERN +
        r'\s*:\s*' + QUOTE_PATTERN
    ),

    # Catches fid with numeric value
    "wordpress_fid_numeric": (
        r'\[\[\s*\{\s*' + QUOTE_PATTERN + r'fid' + QUOTE_PATTERN +
        r'\s*:\s*' + QUOTE_PATTERN + r'[0-9]+'
    ),

    # Catches type:media field anywhere in the structure
    "wordpress_media_type": (
        QUOTE_PATTERN + r'type' + QUOTE_PATTERN +
        r'\s*:\s*' + QUOTE_PATTERN + r'media' + QUOTE_PATTERN
    ),

    # Catches field_deltas structure
    "wordpress_field_deltas": (
        QUOTE_PATTERN + r'field_deltas' + QUOTE_PATTERN + r'\s*:\s*\{'
    ),

    # Catches view_mode field
    "wordpress_view_mode": (
        QUOTE_PATTERN + r'view_mode' + QUOTE_PATTERN + r'\s*:\s*' + QUOTE_PATTERN
    ),

    # Catches complete structure (stricter - requires both fid and type:media)
    "wordpress_complete": (
        r'\[\[\s*\{' + QUOTE_PATTERN + r'fid' + QUOTE_PATTERN + r'[^]]{100,}' +
        QUOTE_PATTERN + r'type' + QUOTE_PATTERN + r'\s*:\s*' +
        QUOTE_PATTERN + r'media' + QUOTE_PATTERN + r'[^]]*\]\]'
    ),
}

async def main():
    url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"

    print("🔍 Testing IMPROVED patterns on archived page")
    print(f"URL: {url}\n")
    print("=" * 70)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)

        if not result.html:
            print("❌ Failed to fetch page")
            return

        html = result.html
        print(f"✅ Page fetched ({len(html):,} bytes)\n")

        # Test each pattern
        total_matches = 0
        pattern_results = {}

        for pattern_name, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
            pattern_results[pattern_name] = matches
            total_matches += len(matches)

            status = "✅" if matches else "❌"
            print(f"{status} {pattern_name}: {len(matches)} matches")

        print("\n" + "=" * 70)
        print(f"📊 TOTAL: {total_matches} pattern matches found")
        print("=" * 70)

        # Show details of successful matches
        if total_matches > 0:
            print("\n🎯 VERIFICATION: Pattern matching WORKS!")
            print("\nSample matches:\n")

            for pattern_name, matches in pattern_results.items():
                if matches and len(matches) <= 5:  # Show details for patterns with few matches
                    print(f"\n{pattern_name} ({len(matches)} matches):")
                    for i, match in enumerate(matches[:2], 1):
                        start = max(0, match.start() - 50)
                        end = min(len(html), match.end() + 50)
                        context = html[start:end].replace('\n', ' ')
                        context = re.sub(r'\s+', ' ', context)
                        print(f"  {i}. ...{context[:150]}...")

        else:
            print("\n❌ FAILED: No patterns matched!")
            print("This means the patterns still need adjustment.")

if __name__ == "__main__":
    asyncio.run(main())
