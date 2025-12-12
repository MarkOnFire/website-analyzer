#!/usr/bin/env python3.11
"""Smart WPR test - discovers article pages and searches for WordPress embed bugs."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler
from urllib.parse import urljoin, urlparse

# Flexible patterns to catch WordPress embed code variations
PATTERNS = {
    "wordpress-media-embed-full": r'\[\[{"fid":"[^"]*".*?"type":"media".*?}}]]',
    "wordpress-fid-opening": r'\[\[{"fid":"[0-9]+[″"]',  # Catches both " and special quote
    "field-deltas-structure": r'"field_deltas":\{[^}]*"format":',
    "view-mode-fields": r'"view_mode":"[^"]*","fields":\{',
}

async def discover_articles(base_url, max_articles=20):
    """Discover article URLs from news/culture sections."""
    print(f"🔎 Discovering article pages from {base_url}...")

    discovered_urls = set()
    section_urls = [
        f"{base_url}/news",
        f"{base_url}/culture",
        f"{base_url}/shows",
    ]

    async with AsyncWebCrawler() as crawler:
        for section_url in section_urls:
            try:
                result = await crawler.arun(section_url)
                if result.links:
                    for link in result.links:
                        # Look for article-like URLs (contain dates or article paths)
                        if re.search(r'/\d{4}/', link) or '/article' in link or len(link.split('/')) > 4:
                            full_url = urljoin(base_url, link)
                            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                                discovered_urls.add(full_url)
                                if len(discovered_urls) >= max_articles:
                                    break
            except Exception as e:
                print(f"   ⚠️  Error discovering from {section_url}: {e}")

            if len(discovered_urls) >= max_articles:
                break

    print(f"   Found {len(discovered_urls)} potential article URLs")
    return list(discovered_urls)[:max_articles]

async def check_url_for_patterns(crawler, url):
    """Check a single URL for WordPress embed patterns."""
    try:
        result = await crawler.arun(url)
        page_matches = {}

        # Try all patterns on both HTML and markdown
        for pattern_name, pattern in PATTERNS.items():
            content_to_search = result.html or result.markdown or ""
            matches = list(re.finditer(pattern, content_to_search, re.IGNORECASE | re.DOTALL))
            if matches:
                page_matches[pattern_name] = matches

        if page_matches:
            # Get a sample of the matched content
            sample_match = list(page_matches.values())[0][0]
            content = result.html or result.markdown or ""
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
        print(f"   ⚠️  Error checking {url}: {e}")
        return None

async def main():
    base_url = "https://www.wpr.org"

    # Phase 1: Discover articles
    article_urls = await discover_articles(base_url, max_articles=30)

    if not article_urls:
        print("\n❌ Could not discover any article URLs. Try adding specific URLs manually.")
        return

    # Phase 2: Check each article for the pattern
    print(f"\n🔍 Scanning {len(article_urls)} articles for WordPress embed bugs...")
    matches_found = []

    async with AsyncWebCrawler() as crawler:
        for i, url in enumerate(article_urls, 1):
            print(f"   [{i}/{len(article_urls)}] Checking: {url[:80]}...")
            result = await check_url_for_patterns(crawler, url)
            if result:
                print(f"      ✅ FOUND {result['total_matches']} match(es)!")
                matches_found.append(result)
            else:
                print(f"      ❌ Clean")

    # Phase 3: Report
    print("\n" + "="*70)
    print(f"📊 SUMMARY: Found WordPress embed bugs on {len(matches_found)}/{len(article_urls)} pages")
    print("="*70)

    if matches_found:
        print("\n🔴 AFFECTED PAGES:\n")
        for i, match in enumerate(matches_found, 1):
            print(f"{i}. {match['url']}")
            print(f"   Patterns matched:")
            for pattern_name, count in match['patterns'].items():
                print(f"      - {pattern_name}: {count} occurrence(s)")
            print(f"\n   Sample of visible bug:")
            # Clean up the sample for readability
            sample = match['sample_context'].replace('\n', ' ').replace('\t', ' ')
            sample = re.sub(r'\s+', ' ', sample)
            print(f"   ...{sample[:250]}...")
            print()
    else:
        print("\n✅ Good news! No WordPress embed artifacts found in tested pages.")
        print("   Either the bug has been fixed, or it exists on different pages.")

if __name__ == "__main__":
    asyncio.run(main())
