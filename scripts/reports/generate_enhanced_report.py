#!/usr/bin/env python3
"""
Integration script to generate enhanced bug reports with root causes and fixes.
Combines RootCauseAnalyzer, FixGenerator, and enhanced HTML export.
"""

import json
from pathlib import Path
from typing import Dict, List
from bug_finder_root_cause import RootCauseAnalyzer
from bug_finder_fix_generator import FixGenerator
from bug_finder_export import export_to_html

def load_bug_results(json_path: str) -> dict:
    """Load bug scan results from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)

def analyze_bugs(results: dict) -> tuple[Dict[str, str], Dict[str, List[dict]]]:
    """
    Analyze all bugs and generate root causes and fixes.

    Returns:
        (root_causes, fixes) - Dictionaries mapping URLs/bug_types to analyses
    """
    analyzer = RootCauseAnalyzer()
    fix_gen = FixGenerator()

    root_causes = {}
    bug_types_found = set()

    # Analyze each bug URL
    for result in results.get('results', []):
        url = result['url']

        # For now, assume all bugs are WordPress embeds based on pattern
        # In production, you'd extract actual bug text from the page
        bug_text = '[[{"fid":"...","view_mode":"full_width",...}]]'

        # Analyze root cause
        analysis = analyzer.analyze(bug_text, url)
        root_causes[url] = analysis['hypothesis']
        bug_types_found.add(analysis['bug_type'])

    # Generate fixes for each bug type found
    fixes = {}
    for bug_type in bug_types_found:
        if bug_type == 'wordpress_embed':
            # Generate WordPress embed fixes
            fix_report = fix_gen.generate_wordpress_embed_fix(
                bug_pattern='[[{"fid":"..."}]]'
            )
            fixes['wordpress_embed'] = fix_report['options']
        elif bug_type == 'css_styling':
            # Generate CSS fixes
            fix_report = fix_gen.generate_css_fix(
                selector='.wp-block-social-links',
                property_name='list-style',
                context={'issue': 'bullets appearing'}
            )
            fixes['css_styling'] = [fix_report]

    return root_causes, fixes

def generate_enhanced_report(
    json_path: str,
    output_path: str,
    include_fixes: bool = True
):
    """
    Generate enhanced HTML report with root causes and fixes.

    Args:
        json_path: Path to bug scan JSON results
        output_path: Path for output HTML file
        include_fixes: Whether to include fix recommendations
    """
    print(f"📖 Loading results from {json_path}...")
    results = load_bug_results(json_path)

    print("🔍 Analyzing bugs and generating root causes...")
    root_causes, fixes = analyze_bugs(results)

    print(f"✨ Generating enhanced HTML report...")
    export_to_html(
        matches=results.get('results', []),
        output_file=Path(output_path),
        metadata=results.get('metadata', {}),
        include_fixes=include_fixes,
        root_causes=root_causes,
        fixes=fixes
    )

    print(f"✅ Enhanced report saved to: {output_path}")
    print(f"   Root causes: {len(root_causes)} bugs analyzed")
    print(f"   Fix options: {sum(len(opts) for opts in fixes.values())} total options")

    return output_path

if __name__ == '__main__':
    import sys

    # Default to Phase 1 results
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'bug_results_www_wpr_org.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'bug_report_enhanced_wpr.html'

    if not Path(input_file).exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    generate_enhanced_report(
        json_path=input_file,
        output_path=output_file,
        include_fixes=True
    )

    print(f"\n🌐 Open in browser: file://{Path(output_file).absolute()}")
