#!/usr/bin/env python3.11
"""
Test suite for FixGenerator class.

Demonstrates:
1. WordPress embed fix generation (3 options)
2. CSS fix generation
3. Priority assignment
4. Full fix report generation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bug_finder_fix_generator import FixGenerator
import json


def test_wordpress_embed_fix():
    """Test WordPress embed code fix generation."""
    print("\n" + "=" * 70)
    print("TEST 1: WordPress Embed Code Fix Generation")
    print("=" * 70)

    generator = FixGenerator()

    # Real embed bug from WPR website
    bug_pattern = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A"},"type":"media"}]]'''

    result = generator.generate_wordpress_embed_fix(bug_pattern)

    print(f"Bug Type: {result['bug_type']}")
    print(f"Severity: {result['severity']}")
    print(f"Number of Options: {len(result['options'])}")
    print(f"Recommended: Option {result['recommended'] + 1}")
    print()

    for i, option in enumerate(result['options'], 1):
        print(f"\n--- OPTION {i}: {option['name']} ---")
        print(f"Description: {option['description']}")
        print(f"Effort: {option['effort_hours']}")
        print(f"Language: {option['language']}")
        print()
        print("Pros:")
        for pro in option['pros']:
            print(f"  + {pro}")
        print("Cons:")
        for con in option['cons']:
            print(f"  - {con}")
        print()
        print("Code Preview:")
        code_preview = option['code'][:200]
        print(code_preview + "..." if len(option['code']) > 200 else code_preview)

    return result


def test_css_fix():
    """Test CSS fix generation."""
    print("\n" + "=" * 70)
    print("TEST 2: CSS Fix Generation")
    print("=" * 70)

    generator = FixGenerator()

    context = {
        'bug_type': 'css_rendering_issue',
        'description': 'Footer navigation showing unwanted bullet points on article pages',
        'issue_count': 15
    }

    result = generator.generate_css_fix('footer ul', 'list-style', context)

    print(f"Issue: {result['issue']}")
    print(f"Affected Elements: {result['affected_elements']}")
    print(f"CSS Selector: {result['selector']}")
    print(f"CSS Property: {result['property']}")
    print(f"CSS Value: {result['value']}")
    print()

    for i, option in enumerate(result['options'], 1):
        print(f"\n--- OPTION {i}: {option['name']} ---")
        print(f"Description: {option['description']}")
        print(f"Effort: {option['effort_hours']}")
        print(f"Language: {option['language']}")
        print()
        print("Code:")
        print(option['code'][:400])
        print()

    return result


def test_effort_estimation():
    """Test effort estimation."""
    print("\n" + "=" * 70)
    print("TEST 3: Effort Estimation")
    print("=" * 70)

    generator = FixGenerator()
    bug_pattern = '''[[{"fid":"123","view_mode":"full_width"}]]'''
    result = generator.generate_wordpress_embed_fix(bug_pattern)

    print("Effort estimates by option:\n")
    for i, option in enumerate(result['options'], 1):
        effort = generator.estimate_effort(option)
        print(f"Option {i}: {option['name']:30} -> {effort}")

    return result


def test_priority_assignment():
    """Test priority assignment based on bug type and page count."""
    print("\n" + "=" * 70)
    print("TEST 4: Priority Assignment")
    print("=" * 70)

    generator = FixGenerator()

    test_cases = [
        ("wordpress_malformed_embed", 1, "Single page - should be critical"),
        ("wordpress_malformed_embed", 50, "50 pages - should be critical"),
        ("wordpress_malformed_embed", 150, "150 pages - should be critical"),
        ("css_rendering_issue", 1, "Single CSS issue - should be medium"),
        ("css_rendering_issue", 30, "30 pages CSS issue - should be high"),
        ("missing_images", 5, "5 missing images - should be medium"),
        ("missing_images", 100, "100 missing images - should be critical"),
        ("broken_links", 200, "200 broken links - should be critical"),
        ("unknown_bug", 1, "Unknown bug type - should be low"),
    ]

    print(f"{'Bug Type':<30} {'Pages':<8} {'Description':<40} -> Priority")
    print("-" * 90)

    for bug_type, count, description in test_cases:
        priority = generator.assign_priority(bug_type, count)
        print(f"{bug_type:<30} {count:<8} {description:<40} -> {priority}")

    return test_cases


def test_full_fix_report():
    """Test complete fix report generation."""
    print("\n" + "=" * 70)
    print("TEST 5: Complete Fix Report Generation")
    print("=" * 70)

    generator = FixGenerator()

    bug_pattern = '''[[{"fid":"5001","view_mode":"full_width","fields":{}}]]'''
    affected_pages = [
        "https://www.example.com/article-1",
        "https://www.example.com/article-2",
        "https://www.example.com/article-3",
    ]

    report = generator.generate_fix_report(
        bug_type="wordpress_malformed_embed",
        bug_pattern=bug_pattern,
        page_count=len(affected_pages),
        affected_pages=affected_pages
    )

    print("Report Summary:")
    print(f"  Bug Type: {report['summary']['bug_type']}")
    print(f"  Pages Affected: {report['summary']['pages_affected']}")
    print(f"  Priority: {report['summary']['priority']}")
    print(f"  Estimated Effort: {report['summary']['estimated_effort']}")
    print()

    print(f"Affected Pages:")
    for page in report['affected_pages']:
        print(f"  - {page}")
    print()

    print("Next Steps:")
    for step in report['next_steps']:
        print(f"  {step}")

    return report


def test_output_json():
    """Test JSON serialization of fix report."""
    print("\n" + "=" * 70)
    print("TEST 6: JSON Serialization")
    print("=" * 70)

    generator = FixGenerator()
    bug_pattern = '''[[{"fid":"2022","view_mode":"full_width"}]]'''

    result = generator.generate_wordpress_embed_fix(bug_pattern)

    # Extract just the first option for display
    print("JSON representation of first fix option:")
    print()
    print(json.dumps(result['options'][0], indent=2))

    return result


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BUG FINDER FIX GENERATOR - TEST SUITE")
    print("=" * 70)

    # Run all tests
    test_wordpress_embed_fix()
    test_css_fix()
    test_effort_estimation()
    test_priority_assignment()
    test_full_fix_report()
    test_output_json()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
