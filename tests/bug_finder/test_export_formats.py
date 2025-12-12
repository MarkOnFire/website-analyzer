#!/usr/bin/env python3.11
"""
Test export formats with mock data.
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bug_finder_export import export_results

# Mock test data
mock_matches = [
    {
        'url': 'https://www.example.com/page1',
        'total_matches': 3,
        'patterns': {
            'multi_field': 2,
            'opening_with_field': 1,
        }
    },
    {
        'url': 'https://www.example.com/page2',
        'total_matches': 5,
        'patterns': {
            'multi_field': 3,
            'field_fid': 2,
        }
    },
    {
        'url': 'https://www.example.com/page3',
        'total_matches': 1,
        'patterns': {
            'opening_structure': 1,
        }
    },
]

metadata = {
    'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'site_scanned': 'https://www.example.com',
    'example_url': 'https://archive.org/web/.../example-with-bug',
    'pages_scanned': 100,
}

output_file = Path('test_export')

print("Testing export formats...")
print("=" * 70)

# Test each format
for fmt in ['txt', 'csv', 'html', 'json']:
    print(f"\n✓ Generating {fmt.upper()} export...")
    export_results(mock_matches, output_file, metadata, format=fmt)
    ext = f'.{fmt}'
    output_path = output_file.with_suffix(ext)
    print(f"  Created: {output_path} ({output_path.stat().st_size} bytes)")

# Test 'all' format
print(f"\n✓ Generating ALL formats...")
export_results(mock_matches, Path('test_export_all'), metadata, format='all')
for ext in ['.txt', '.csv', '.html', '.json']:
    output_path = Path(f'test_export_all{ext}')
    if output_path.exists():
        print(f"  Created: {output_path} ({output_path.stat().st_size} bytes)")

print("\n" + "=" * 70)
print("✅ All export formats generated successfully!")
print("\nGenerated files:")
print("  - test_export.txt")
print("  - test_export.csv")
print("  - test_export.html  (open in browser to view)")
print("  - test_export.json")
print("  - test_export_all.txt, .csv, .html, .json")
