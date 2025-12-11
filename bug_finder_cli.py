#!/usr/bin/env python3.11
"""
Bug Finder CLI - User-friendly interface for finding visual bugs across a website.

User provides:
1. URL of a page with the bug
2. Optional: Description of what looks wrong
3. Optional: Screenshot (future feature)

Tool outputs:
- List of all pages with similar bugs
- Confidence scores
- Sample context from each affected page
"""

import asyncio
import sys
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from pattern_generator import PatternGenerator
from full_site_scanner import SiteScanner


class BugFinderCLI:
    """Interactive CLI for finding visual bugs across a website."""

    def __init__(self):
        self.generator = PatternGenerator()

    async def extract_bug_from_url(self, url: str) -> tuple[str, str]:
        """
        Fetch a page and extract potential bug text from HTML.

        This looks for common visual bug patterns:
        - JSON-like structures in visible text
        - Embed codes that aren't rendered
        - Escaped HTML/URLs in content

        Returns:
            (bug_text, detection_method) tuple
        """
        print(f"📥 Fetching example page: {url}")

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)

            if not result.html:
                raise ValueError("Failed to fetch page")

            html = result.html
            print(f"✅ Fetched {len(html):,} bytes")

            import re

            # Strategy 1: Look for [[ or {{ patterns (common in embed bugs)
            print("🔍 Searching for embed code patterns...")

            embed_patterns = [
                # Complete patterns with closing brackets
                (r'\[\[.{100,}?\]\]', 'complete-double-bracket'),  # [[...]] (non-greedy)
                (r'\{\{.{100,}?\}\}', 'complete-double-brace'),  # {{...}} (non-greedy)
                # Unclosed patterns (take up to 2000 chars or end of line)
                (r'\[\[.{100,2000}', 'unclosed-double-bracket'),  # [[ without closing
            ]

            for pattern, method in embed_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    # Sort by length, take longest (most likely to be real bug)
                    matches.sort(key=len, reverse=True)
                    bug_text = matches[0][:2000]  # Max 2000 chars

                    print(f"   ✅ Found pattern: {method}")
                    print(f"   Length: {len(bug_text)} chars")
                    return bug_text, method

            # Strategy 2: Look for JSON structures in paragraph/div tags
            print("🔍 Searching for JSON in visible elements...")

            json_pattern = r'<(?:p|div)[^>]*>([^<]*\{["\']fid["\'][^<]{100,})</(?:p|div)>'
            matches = re.findall(json_pattern, html, re.IGNORECASE | re.DOTALL)

            if matches:
                bug_text = matches[0][:2000]
                print(f"   ✅ Found JSON in visible element")
                return bug_text, 'json-in-visible-tag'

            # Strategy 3: Look for escaped characters (common in rendering bugs)
            print("🔍 Searching for escaped HTML patterns...")

            escaped_pattern = r'%[0-9A-F]{2}[^%\s]{50,}'  # URL-encoded content
            matches = re.findall(escaped_pattern, html)

            if matches:
                # Find the longest escaped sequence
                matches.sort(key=len, reverse=True)
                bug_text = matches[0][:2000]
                print(f"   ✅ Found escaped content")
                return bug_text, 'escaped-html'

            # Strategy 4: Generic long strings that look like bugs
            # Look for very long unbroken strings in paragraph tags (unusual)
            print("🔍 Searching for anomalous long strings...")

            anomaly_pattern = r'<p[^>]*>([^\s<]{200,})</p>'
            matches = re.findall(anomaly_pattern, html)

            if matches:
                bug_text = matches[0][:2000]
                print(f"   ✅ Found anomalous long string")
                return bug_text, 'anomalous-string'

            raise ValueError(
                "\n❌ Could not automatically detect bug pattern in HTML.\n"
                "   Strategies tried:\n"
                "   - Double bracket patterns [[...]]\n"
                "   - JSON in visible tags\n"
                "   - Escaped HTML\n"
                "   - Anomalous strings\n\n"
                "   Please provide the bug text directly using --bug-text"
            )

    async def find_bugs(
        self,
        example_url: str,
        site_to_scan: str,
        max_pages: int = 1000,
        bug_text: str = None,
        incremental: bool = False,
        output_file: str = None
    ):
        """
        Main workflow: Find all pages with similar bugs.

        Args:
            example_url: URL of page showing the bug
            site_to_scan: Base URL to scan (e.g., https://www.wpr.org)
            max_pages: Maximum pages to scan
            bug_text: Optional - provide bug text directly instead of extracting
            incremental: Enable incremental output to .partial.json
            output_file: Output file path for incremental mode
        """
        print("=" * 70)
        print("Bug Finder - Visual Bug Scanner")
        print("=" * 70)
        print()

        # Step 1: Get bug example
        detection_method = "manual"
        if bug_text:
            print("📝 Using provided bug text")
            example = bug_text
        else:
            print("🔎 Extracting bug pattern from example URL...\n")
            example, detection_method = await self.extract_bug_from_url(example_url)

        print(f"\n📋 Bug example extracted ({len(example)} chars)")
        print(f"   Detection method: {detection_method}")
        print(f"   Preview: {example[:150]}...")
        print()

        # Step 2: Generate patterns
        print("🧠 Analyzing bug and generating search patterns...")
        analysis = self.generator.analyze(example)

        print(f"   Confidence: {analysis.confidence}")
        print(f"   Patterns generated: {len(analysis.patterns)}")
        print(f"   Key fields: {', '.join(analysis.key_fields[:3])}...")

        if analysis.unicode_chars:
            print(f"   Special characters: {len(analysis.unicode_chars)} found")
        print()

        # Step 3: Scan the site
        print(f"🌐 Scanning {site_to_scan} (max {max_pages} pages)...")
        if incremental:
            print(f"   Incremental output: ENABLED")
            if output_file:
                print(f"   Progress file: {output_file}.partial.json")
        print("   This may take several minutes to hours depending on site size.")
        print()

        # Create scanner with generated patterns
        scanner = SiteScanner(site_to_scan, max_pages=max_pages, incremental=incremental, output_file=output_file)

        # Override patterns with our generated ones
        import full_site_scanner
        full_site_scanner.PATTERNS = analysis.patterns

        # Run scan
        matches = await scanner.scan()

        # Step 4: Report results
        print("\n" + "=" * 70)
        print("📊 RESULTS")
        print("=" * 70)

        if matches:
            print(f"\n🔴 Found {len(matches)} pages with similar bugs:\n")

            for i, match in enumerate(matches[:20], 1):
                print(f"{i}. {match['url']}")
                print(f"   Matches: {match['total_matches']} pattern(s)")
                print(f"   Patterns: {', '.join(match['patterns'].keys())}")
                print()

            if len(matches) > 20:
                print(f"   ... and {len(matches) - 20} more\n")

            # Save results
            output_file = f"bug_results_{Path(site_to_scan).name.replace('.', '_')}.txt"
            with open(output_file, 'w') as f:
                f.write(f"Bug Scan Results for {site_to_scan}\n")
                f.write(f"Example URL: {example_url}\n")
                f.write(f"Pages scanned: {len(scanner.visited)}\n")
                f.write(f"Bugs found: {len(matches)}\n")
                f.write("=" * 70 + "\n\n")

                for match in matches:
                    f.write(f"{match['url']}\n")
                    f.write(f"  Matches: {match['total_matches']}\n\n")

            print(f"✅ Full results saved to: {output_file}")
        else:
            print("\n✅ No bugs found!")
            print("   Either the bug has been fixed, or it exists on pages not yet scanned.")

        return matches


async def main():
    """Demo: Interactive bug finder."""
    cli = BugFinderCLI()

    # Example usage
    example_url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"
    site_to_scan = "https://www.wpr.org"

    # For demo, we'll provide the bug text directly
    bug_text = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"},"type":"media","field_deltas":{"2":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"}},"link_text":false,"attributes":{"alt":"Tom and Jerry milkglass set","title":"Tom and Jerry milkglass set","class":"media-element file-full-width","data-delta":"2″}}]]'''

    print("DEMO MODE - Quick validation scan (100 pages)\n")

    results = await cli.find_bugs(
        example_url=example_url,
        site_to_scan=site_to_scan,
        max_pages=100,  # Quick test
        bug_text=bug_text
    )


if __name__ == "__main__":
    asyncio.run(main())
