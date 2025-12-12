#!/usr/bin/env python3.11
"""Test auto-extraction feature on archived WordPress bug page."""

import asyncio
import sys
from pathlib import Path

# Add project root and scripts/development to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "development"))

from bug_finder_cli import BugFinderCLI


async def main():
    print("=" * 70)
    print("Testing Auto Bug Extraction")
    print("=" * 70)
    print()

    cli = BugFinderCLI()

    # Test URL with known WordPress embed bug
    test_url = "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"

    try:
        bug_text, method = await cli.extract_bug_from_url(test_url)

        print("\n" + "=" * 70)
        print("✅ EXTRACTION SUCCESSFUL!")
        print("=" * 70)
        print(f"\nDetection method: {method}")
        print(f"Bug text length: {len(bug_text)} chars")
        print(f"\nExtracted bug text:")
        print("-" * 70)
        print(bug_text[:500])
        if len(bug_text) > 500:
            print(f"... ({len(bug_text) - 500} more chars)")
        print("-" * 70)

        # Verify it contains key markers
        has_fid = '"fid"' in bug_text or "'fid'" in bug_text
        has_brackets = '[[' in bug_text
        has_json = '{' in bug_text

        print(f"\nValidation:")
        print(f"  Contains 'fid': {'✅' if has_fid else '❌'}")
        print(f"  Contains '[[': {'✅' if has_brackets else '❌'}")
        print(f"  Contains '{{': {'✅' if has_json else '❌'}")

        if has_fid and has_brackets and has_json:
            print(f"\n🎉 Auto-extraction is READY for production!")
        else:
            print(f"\n⚠️  Extraction succeeded but may need refinement")

    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED:")
        print(f"   {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
