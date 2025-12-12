#!/usr/bin/env python3.11
"""
Test generated patterns against real HTML from archived page.
This validates that the pattern generator creates patterns that work in the wild.
"""

import asyncio
import re
import sys
from pathlib import Path
from crawl4ai import AsyncWebCrawler

# Add project root and scripts/development to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "development"))

from pattern_generator import PatternGenerator


async def main():
    print("=" * 70)
    print("Testing Generated Patterns on Real HTML")
    print("=" * 70)

    # 1. Generate patterns from the example
    bug_example = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"},"type":"media","field_deltas":{"2":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"}},"link_text":false,"attributes":{"alt":"Tom and Jerry milkglass set","title":"Tom and Jerry milkglass set","class":"media-element file-full-width","data-delta":"2″}}]]'''

    generator = PatternGenerator()
    analysis = generator.analyze(bug_example)

    print(f"\n📊 Pattern Generation:")
    print(f"   Confidence: {analysis.confidence}")
    print(f"   Patterns: {len(analysis.patterns)}")
    print(f"   Key fields: {', '.join(analysis.key_fields[:5])}\n")

    # 2. Fetch real HTML from archived page
    url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"
    print(f"🌐 Fetching: {url}\n")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)

        if not result.html:
            print("❌ Failed to fetch page")
            return

        html = result.html
        print(f"✅ Page fetched ({len(html):,} bytes)\n")

        # 3. Test each generated pattern
        print("=" * 70)
        print("Pattern Match Results")
        print("=" * 70)

        total_matches = 0
        successful_patterns = []

        for pattern_name, pattern in analysis.patterns.items():
            matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
            total_matches += len(matches)

            status = "✅" if matches else "❌"
            print(f"{status} {pattern_name}: {len(matches)} matches")

            if matches:
                successful_patterns.append(pattern_name)
                # Show first match context
                if len(matches) <= 3:
                    for i, match in enumerate(matches[:2], 1):
                        start = max(0, match.start() - 50)
                        end = min(len(html), match.end() + 50)
                        context = html[start:end].replace('\n', ' ')
                        context = re.sub(r'\s+', ' ', context)
                        print(f"      Match {i}: ...{context[:100]}...")

        print("\n" + "=" * 70)
        print(f"📈 Results Summary")
        print("=" * 70)
        print(f"   Total pattern matches: {total_matches}")
        print(f"   Successful patterns: {len(successful_patterns)}/{len(analysis.patterns)}")
        print(f"   Success rate: {len(successful_patterns)/len(analysis.patterns)*100:.1f}%")

        if len(successful_patterns) >= len(analysis.patterns) * 0.5:
            print(f"\n✅ SUCCESS: Generated patterns work on real HTML!")
        else:
            print(f"\n❌ NEEDS IMPROVEMENT: Only {len(successful_patterns)} patterns matched")

        # 4. Test if we would catch bugs we know exist
        print("\n" + "=" * 70)
        print("Bug Detection Test")
        print("=" * 70)

        # We know there are 2 bug instances on this page
        expected_bugs = 2

        # Count unique bug instances (use the most specific pattern that matched)
        best_pattern = None
        for pattern_name in ['multi_field', 'opening_with_field', 'type_field']:
            if pattern_name in successful_patterns:
                best_pattern = pattern_name
                break

        if best_pattern:
            matches = list(re.finditer(
                analysis.patterns[best_pattern],
                html,
                re.IGNORECASE | re.DOTALL
            ))
            print(f"   Using pattern '{best_pattern}' for detection")
            print(f"   Bugs found: {len(matches)}")
            print(f"   Expected: {expected_bugs}")

            if len(matches) == expected_bugs:
                print(f"\n   ✅ PERFECT: Found exactly {expected_bugs} bug instances!")
            elif len(matches) > 0:
                print(f"\n   ⚠️  Found bugs but count differs from expected")
            else:
                print(f"\n   ❌ FAILED: No bugs detected")
        else:
            print("   ❌ No suitable detection pattern available")


if __name__ == "__main__":
    asyncio.run(main())
