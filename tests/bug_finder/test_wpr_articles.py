#!/usr/bin/env python3.11
"""Test discovered WPR articles for WordPress embed bugs."""

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

async def check_url(crawler, url):
    """Check a single URL for WordPress embed patterns."""
    try:
        result = await crawler.arun(url)
        page_matches = {}

        content = result.html or result.markdown or ""
        if not content:
            return None

        # Try all patterns
        for pattern_name, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
            if matches:
                page_matches[pattern_name] = matches

        if page_matches:
            # Get a sample
            sample_match = list(page_matches.values())[0][0]
            context_start = max(0, sample_match.start() - 150)
            context_end = min(len(content), sample_match.end() + 150)
            context = content[context_start:context_end]

            return {
                'url': url,
                'patterns': {k: len(v) for k, v in page_matches.items()},
                'sample_context': context,
                'total_matches': sum(len(v) for v in page_matches.values())
            }
        return None
    except Exception as e:
        return None

async def main():
    # Load URLs
    try:
        with open("wpr_article_urls.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Run discover_wpr_articles.py first to generate article URLs")
        return

    print(f"🔍 Testing {len(urls)} article URLs for WordPress embed bugs...\n")

    matches_found = []
    async with AsyncWebCrawler() as crawler:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url[:70]}...", end=" ")
            result = await check_url(crawler, url)
            if result:
                print(f"✅ FOUND!")
                matches_found.append(result)
            else:
                print("❌")

    # Report
    print("\n" + "="*70)
    print(f"📊 RESULT: Found bugs on {len(matches_found)}/{len(urls)} pages ({len(matches_found)/len(urls)*100:.1f}%)")
    print("="*70)

    if matches_found:
        print("\n🔴 AFFECTED PAGES:\n")
        for i, match in enumerate(matches_found, 1):
            print(f"{i}. {match['url']}")
            print(f"   Total matches: {match['total_matches']}")
            print(f"   Patterns:")
            for pattern_name, count in match['patterns'].items():
                print(f"      - {pattern_name}: {count}x")

            # Show sample
            sample = match['sample_context'].replace('\n', ' ').replace('\t', ' ')
            sample = re.sub(r'\s+', ' ', sample)
            print(f"\n   Sample bug text:")
            print(f"   ...{sample[:300]}...\n")

        # Save results
        with open("wpr_bugs_found.txt", "w") as f:
            f.write(f"WordPress Embed Bug Report - {len(matches_found)} pages affected\n")
            f.write("="*70 + "\n\n")
            for match in matches_found:
                f.write(f"{match['url']}\n")
                f.write(f"  Matches: {match['total_matches']}\n\n")

        print(f"✅ Detailed results saved to wpr_bugs_found.txt")

    else:
        print("\n✅ Good news! No WordPress embed bugs found.")

if __name__ == "__main__":
    asyncio.run(main())
