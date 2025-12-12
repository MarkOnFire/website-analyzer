#!/usr/bin/env python3.11
"""
Test script demonstrating enhanced HTML export with executive summary and fixes.
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bug_finder_export import export_to_html

# Sample bug data
test_matches = [
    {
        'url': 'https://example.com/blog/post-1',
        'total_matches': 3,
        'priority': 'critical',
        'patterns': {
            'jQuery .live() deprecated': 2,
            'IE8 compatibility issue': 1
        }
    },
    {
        'url': 'https://example.com/about',
        'total_matches': 2,
        'priority': 'high',
        'patterns': {
            'jQuery .live() deprecated': 2
        }
    },
    {
        'url': 'https://example.com/products',
        'total_matches': 1,
        'priority': 'medium',
        'patterns': {
            'Outdated JavaScript API': 1
        }
    },
    {
        'url': 'https://example.com/contact',
        'total_matches': 1,
        'priority': 'low',
        'patterns': {
            'Browser deprecated method': 1
        }
    }
]

# Metadata
test_metadata = {
    'site_scanned': 'example.com',
    'example_url': 'https://example.com/blog/post-1',
    'pages_scanned': 4,
    'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

# Root cause analysis
test_root_causes = {
    'jQuery .live() deprecated': 'The .live() method was deprecated in jQuery 1.7 and removed in jQuery 1.9. This method was used for event delegation before modern .on() method became standard.',
    'IE8 compatibility issue': 'The code includes IE8-specific workarounds that are no longer necessary since IE8 has reached end-of-life. These can be safely removed.',
    'Outdated JavaScript API': 'This code uses older JavaScript APIs that have been superseded by modern equivalents with better performance and browser support.',
    'Browser deprecated method': 'This method has been marked as deprecated by W3C and may be removed from browsers in future versions.'
}

# Proposed fixes
test_fixes = {
    'jQuery .live() deprecated': [
        {
            'title': 'Migrate to .on() method',
            'description': 'Replace all .live() calls with .on() using event delegation. This is the modern standard approach and has identical functionality.',
            'code_sample': '''// Old (deprecated):
$(document).on('click', '.item', function() {
    // legacy .live() emulation
});

// New (recommended):
$(document).on('click', '.item', function() {
    // handler code
});''',
            'language': 'javascript',
            'effort': '2-4 hours',
            'priority': 'critical'
        },
        {
            'title': 'Remove jQuery dependency entirely',
            'description': 'Consider replacing jQuery event delegation with vanilla JavaScript, reducing dependency burden and improving page load performance.',
            'code_sample': '''document.addEventListener('click', function(e) {
    if (e.target.matches('.item')) {
        // handler code
    }
});''',
            'language': 'javascript',
            'effort': '8-16 hours',
            'priority': 'high'
        }
    ],
    'IE8 compatibility issue': [
        {
            'title': 'Remove IE8 polyfills and workarounds',
            'description': 'Safely remove conditional comments and IE8-specific code paths. Modern browser support will improve clarity and maintainability.',
            'code_sample': '''// Remove lines like:
// <!--[if IE 8]><link rel="stylesheet" href="ie8.css"><![endif]-->
// Remove IE8-specific JavaScript polyfills''',
            'language': 'html',
            'effort': '1-2 hours',
            'priority': 'medium'
        }
    ],
    'Outdated JavaScript API': [
        {
            'title': 'Update to modern equivalents',
            'description': 'Replace deprecated APIs with modern JavaScript features. Review MDN documentation for each deprecated method.',
            'code_sample': '''// Check MDN for deprecated method
// Example: use Array.from() instead of custom conversions
const arr = Array.from(nodeList);''',
            'language': 'javascript',
            'effort': '4-6 hours',
            'priority': 'medium'
        }
    ]
}

# Test 1: Export without fixes (backward compatibility)
print("Test 1: Export without fixes (basic report)...")
output_file_basic = Path('/tmp/bug_report_basic.html')
export_to_html(test_matches, output_file_basic, test_metadata)
print(f"  Generated: {output_file_basic}")
print(f"  File size: {output_file_basic.stat().st_size} bytes")

# Test 2: Export with full enhancement (executive summary + fixes)
print("\nTest 2: Export with enhancement (executive summary + fixes)...")
output_file_enhanced = Path('/tmp/bug_report_enhanced.html')
export_to_html(
    test_matches,
    output_file_enhanced,
    test_metadata,
    include_fixes=True,
    root_causes=test_root_causes,
    fixes=test_fixes
)
print(f"  Generated: {output_file_enhanced}")
print(f"  File size: {output_file_enhanced.stat().st_size} bytes")

# Verify files exist and have content
print("\nVerification:")
if output_file_basic.exists() and output_file_basic.stat().st_size > 0:
    print(f"  Basic report: OK ({output_file_basic.stat().st_size} bytes)")
if output_file_enhanced.exists() and output_file_enhanced.stat().st_size > 0:
    print(f"  Enhanced report: OK ({output_file_enhanced.stat().st_size} bytes)")
    # Enhanced should be significantly larger
    size_diff = output_file_enhanced.stat().st_size - output_file_basic.stat().st_size
    print(f"  Enhanced is {size_diff} bytes larger (contains executive summary and fixes)")

print("\nHTML files ready for browser viewing:")
print(f"  Basic: {output_file_basic}")
print(f"  Enhanced: {output_file_enhanced}")
