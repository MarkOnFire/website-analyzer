#!/usr/bin/env python3.11
"""Discover WPR article URLs by parsing HTML directly."""

import asyncio
import re
from crawl4ai import AsyncWebCrawler
from urllib.parse import urljoin
from bs4 import BeautifulSoup

async def main():
    base_url = "https://www.wpr.org"
    section_urls = [
        f"{base_url}/news",
        f"{base_url}/culture",
    ]

    all_article_urls = set()

    async with AsyncWebCrawler() as crawler:
        for section_url in section_urls:
            print(f"\n🔎 Discovering articles from: {section_url}")
            try:
                result = await crawler.arun(section_url)

                if result.html:
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(result.html, 'html.parser')

                    # Find all article links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)

                        # Article URLs typically have /news/, /culture/, or year patterns
                        if any(x in full_url for x in ['/news/', '/culture/', '/shows/']):
                            # Exclude section homepages, just get articles
                            if full_url not in section_urls and len(full_url.split('/')) > 4:
                                all_article_urls.add(full_url)

                    print(f"   Found {len(all_article_urls)} unique article URLs so far")

            except Exception as e:
                print(f"   ⚠️  Error: {e}")

    print(f"\n📊 Total discovered: {len(all_article_urls)} articles")
    print("\n📝 Sample URLs:")
    for url in list(all_article_urls)[:20]:
        print(f"   {url}")

    # Save to file for testing
    with open("wpr_article_urls.txt", "w") as f:
        for url in sorted(all_article_urls):
            f.write(url + "\n")

    print(f"\n✅ Saved {len(all_article_urls)} URLs to wpr_article_urls.txt")

if __name__ == "__main__":
    asyncio.run(main())
