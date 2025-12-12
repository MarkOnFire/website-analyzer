#!/usr/bin/env python3.11
"""Quick test script to search for WordPress embed patterns on specific WPR pages."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Flexible patterns to catch WordPress embed code variations
PATTERNS = {
    "wordpress-media-embed-full": r'\[\[{"fid":"[^"]*".*?"type":"media".*?}}]]',
    "wordpress-fid-opening": r'\[\[{"fid":"[0-9]+[″"]',  # Catches both " and special quote
    "field-deltas-structure": r'"field_deltas":\{[^}]*"format":',
    "view-mode-fields": r'"view_mode":"[^"]*","fields":\{',
}

# Sample URLs to test (add more article URLs here)
TEST_URLS = [
    "https://www.wpr.org",
    "https://www.wpr.org/news",
    "https://www.wpr.org/culture",
    # Add specific article URLs you suspect have the issue
    # Example: "https://www.wpr.org/some-article-with-images"
]

async def main():
    matches_found = []

    async with AsyncWebCrawler() as crawler:
        for url in TEST_URLS:
            print(f"\n🔍 Checking: {url}")
            try:
                result = await crawler.arun(url)
                page_matches = {}

                # Try all patterns
                for pattern_name, pattern in PATTERNS.items():
                    if result.markdown:
                        # Search in markdown content
                        matches = list(re.finditer(pattern, result.markdown, re.IGNORECASE))
                        if matches:
                            page_matches[pattern_name] = matches
                            print(f"   ✅ Pattern '{pattern_name}': {len(matches)} match(es) in markdown")

                    if result.html:
                        # Also search raw HTML
                        html_matches = list(re.finditer(pattern, result.html, re.IGNORECASE))
                        if html_matches and len(html_matches) > len(page_matches.get(pattern_name, [])):
                            page_matches[pattern_name] = html_matches
                            print(f"   ✅ Pattern '{pattern_name}': {len(html_matches)} match(es) in HTML")

                if page_matches:
                    # Get a sample of the matched content
                    sample_match = list(page_matches.values())[0][0]
                    context_start = max(0, sample_match.start() - 100)
                    context_end = min(len(result.html or result.markdown), sample_match.end() + 100)
                    context = (result.html or result.markdown)[context_start:context_end]

                    matches_found.append({
                        'url': url,
                        'patterns': {k: len(v) for k, v in page_matches.items()},
                        'sample_context': context
                    })
                else:
                    print(f"   ❌ No matches for any pattern")

            except Exception as e:
                print(f"   ⚠️  Error: {e}")

    print("\n" + "="*60)
    print(f"📊 SUMMARY: Found issues on {len(matches_found)} page(s)")
    print("="*60)

    if matches_found:
        for match in matches_found:
            print(f"\n🔴 {match['url']}")
            print(f"   Patterns matched:")
            for pattern_name, count in match['patterns'].items():
                print(f"      - {pattern_name}: {count} occurrence(s)")
            print(f"\n   Sample context:")
            print(f"   {match['sample_context'][:300]}...")
    else:
        print("\n✅ No WordPress embed artifacts found in tested pages")

if __name__ == "__main__":
    asyncio.run(main())
