#!/usr/bin/env python3.11
"""
Quick example showing how to use FixGenerator with real bug data.

This demonstrates the three main workflows:
1. Generate fixes for a single detected bug
2. Batch process multiple bug types
3. Export results for team sharing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bug_finder_fix_generator import FixGenerator
import json


def example_1_single_wordpress_bug():
    """Example 1: Generate fixes for a WordPress embed bug."""
    print("=" * 70)
    print("EXAMPLE 1: Single WordPress Embed Bug")
    print("=" * 70)
    print()

    generator = FixGenerator()

    # This is what bug_finder_cli would detect
    detected_bug = '''[[{"fid":"1101026″,"view_mode":"full_width"}]]'''

    # Generate fixes
    fixes = generator.generate_wordpress_embed_fix(detected_bug)

    # Show recommendation
    recommended_idx = fixes['recommended']
    recommended_fix = fixes['options'][recommended_idx]

    print(f"Detected bug pattern: {detected_bug[:50]}...")
    print(f"Recommendation: {recommended_fix['name']}")
    print(f"Effort estimate: {recommended_fix['effort_hours']}")
    print()
    print("Implementation (copy-paste ready):")
    print(recommended_fix['code'][:300])
    print("...")
    print()


def example_2_assign_priority():
    """Example 2: Determine priority based on impact."""
    print("=" * 70)
    print("EXAMPLE 2: Priority Assignment")
    print("=" * 70)
    print()

    generator = FixGenerator()

    # After scanning, we found 47 pages with the same bug
    bug_type = "wordpress_malformed_embed"
    affected_pages = 47

    priority = generator.assign_priority(bug_type, affected_pages)

    print(f"Bug type: {bug_type}")
    print(f"Pages affected: {affected_pages}")
    print(f"Priority: {priority.upper()}")
    print()

    if priority == "critical":
        print("Action: This should be fixed ASAP")
        print("- High visibility issue")
        print("- Affects many pages")
        print("- Impacts user experience")
    elif priority == "high":
        print("Action: Schedule fix for next sprint")
    elif priority == "medium":
        print("Action: Add to backlog")
    else:
        print("Action: Monitor but low priority")

    print()


def example_3_compare_options():
    """Example 3: Compare all fix options for informed decision."""
    print("=" * 70)
    print("EXAMPLE 3: Comparing Fix Options")
    print("=" * 70)
    print()

    generator = FixGenerator()
    bug_pattern = '''[[{"fid":"123","view_mode":"full_width"}]]'''

    fixes = generator.generate_wordpress_embed_fix(bug_pattern)

    # Print comparison table
    print("Fix Option Comparison:\n")
    print(f"{'#':<2} {'Option':<30} {'Effort':<12} {'Risk':<8} {'Reversible':<12}")
    print("-" * 70)

    risk_levels = ["SQL Migration: High", "PHP Filter: Low", "Manual: None"]

    for i, option in enumerate(fixes['options'], 1):
        effort = option['effort_hours']
        reversible = "Yes" if i > 1 else "Yes*"
        risk = risk_levels[i - 1]
        print(f"{i:<2} {option['name']:<30} {effort:<12} {risk:<8} {reversible:<12}")

    print()
    print("Recommended: Option " + str(fixes['recommended'] + 1))
    print()


def example_4_export_for_team():
    """Example 4: Export fix report as JSON for sharing with team."""
    print("=" * 70)
    print("EXAMPLE 4: Export Report for Team")
    print("=" * 70)
    print()

    generator = FixGenerator()

    # Generate a complete report
    report = generator.generate_fix_report(
        bug_type="wordpress_malformed_embed",
        bug_pattern='[[{"fid":"1101026″","view_mode":"full_width"}]]',
        page_count=47,
        affected_pages=[
            "https://www.example.com/article-1",
            "https://www.example.com/article-2",
            "https://www.example.com/article-3",
        ]
    )

    # Export as JSON
    json_report = json.dumps(report, indent=2)

    print("JSON Report (for sharing with team):\n")
    print(json_report[:800])
    print("\n... (truncated) ...\n")

    # Could save to file
    # with open('bug_fix_report.json', 'w') as f:
    #     f.write(json_report)
    # print("Saved to: bug_fix_report.json")

    print()


def example_5_batch_multiple_bugs():
    """Example 5: Process multiple bugs found on same site."""
    print("=" * 70)
    print("EXAMPLE 5: Batch Processing Multiple Bugs")
    print("=" * 70)
    print()

    generator = FixGenerator()

    # Simulate findings from site scan
    bugs_found = [
        {
            "type": "wordpress_malformed_embed",
            "pattern": '[[{"fid":"123","view_mode":"full_width"}]]',
            "page_count": 47,
        },
        {
            "type": "css_rendering_issue",
            "selector": "footer ul",
            "property": "list-style",
            "page_count": 15,
        },
    ]

    print(f"Found {len(bugs_found)} bugs on site. Generating fixes...\n")

    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. {bug['type']}: {bug.get('page_count', '?')} pages affected")

        if bug['type'] == "wordpress_malformed_embed":
            fixes = generator.generate_wordpress_embed_fix(bug['pattern'])
        else:
            fixes = generator.generate_css_fix(
                bug['selector'],
                bug['property'],
                {'bug_type': bug['type'], 'issue_count': bug['page_count']}
            )

        priority = generator.assign_priority(bug['type'], bug['page_count'])
        print(f"   Priority: {priority}")
        print(f"   Recommended: {fixes['options'][fixes['recommended']]['name']}")
        print()

    print()


def example_6_full_workflow():
    """Example 6: Complete workflow from detection to fix."""
    print("=" * 70)
    print("EXAMPLE 6: Complete Fix Workflow")
    print("=" * 70)
    print()

    generator = FixGenerator()

    print("Step 1: Bug Detected")
    print("   bug_finder_cli scans website and finds pattern")
    bug_pattern = '''[[{"fid":"1101026″","view_mode":"full_width"}]]'''
    print(f"   Pattern: {bug_pattern[:50]}...")
    print()

    print("Step 2: Analyze Bug")
    fixes = generator.generate_wordpress_embed_fix(bug_pattern)
    priority = generator.assign_priority(fixes['bug_type'], 47)
    print(f"   Bug type: {fixes['bug_type']}")
    print(f"   Severity: {fixes['severity']}")
    print(f"   Priority (47 pages): {priority}")
    print()

    print("Step 3: Review Options")
    rec_idx = fixes['recommended']
    rec_fix = fixes['options'][rec_idx]
    print(f"   Recommended: Option {rec_idx + 1} - {rec_fix['name']}")
    print(f"   Effort: {rec_fix['effort_hours']}")
    print()

    print("Step 4: Implementation")
    print(f"   Copy this code to your environment:")
    print()
    print("   " + "-" * 66)
    for line in rec_fix['code'].split('\n')[:10]:
        print(f"   {line}")
    print("   " + "-" * 66)
    print()

    print("Step 5: Testing")
    print("   [ ] Test on staging environment")
    print("   [ ] Load affected pages")
    print("   [ ] Verify images display correctly")
    print("   [ ] Check error logs")
    print()

    print("Step 6: Deployment")
    print("   [ ] Deploy to production")
    print("   [ ] Monitor for issues")
    print("   [ ] Re-run site scanner to verify fix")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BUG FINDER FIX GENERATOR - USAGE EXAMPLES")
    print("=" * 70)
    print()

    example_1_single_wordpress_bug()
    example_2_assign_priority()
    example_3_compare_options()
    example_4_export_for_team()
    example_5_batch_multiple_bugs()
    example_6_full_workflow()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()
