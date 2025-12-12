#!/usr/bin/env python3.11
"""
Run validation scan: Quick 100-page test on current WPR.org.

This tests the complete end-to-end flow:
1. Auto-extract bug from archive.org example
2. Generate patterns
3. Scan current site
4. Report findings
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bug_finder_cli import BugFinderCLI


async def main():
    cli = BugFinderCLI()

    # Example URL from archive (has the bug)
    example_url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"

    # Current site to scan
    site_to_scan = "https://www.wpr.org"

    print("\n🚀 Starting Validation Scan")
    print("=" * 70)
    print(f"Example: {example_url}")
    print(f"Scanning: {site_to_scan}")
    print(f"Max pages: 100 (quick validation)")
    print("=" * 70)
    print()

    results = await cli.find_bugs(
        example_url=example_url,
        site_to_scan=site_to_scan,
        max_pages=100,  # Quick validation
        bug_text=None   # Auto-extract!
    )

    if results:
        print(f"\n🎯 Validation scan found {len(results)} pages with bugs!")
        print("   Recommend running full 5000-page scan.")
    else:
        print(f"\n✅ Validation scan found 0 bugs in first 100 pages.")
        print("   Current site may be clean, or bugs are on pages not yet scanned.")


if __name__ == "__main__":
    asyncio.run(main())
