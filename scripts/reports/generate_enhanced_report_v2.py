#!/usr/bin/env python3
"""
Enhanced integration script with logo fetching and proper bug type mapping.
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from bug_finder_root_cause import RootCauseAnalyzer
from bug_finder_fix_generator import FixGenerator
from bug_finder_export import export_to_html

def fetch_site_logo(site_url: str) -> str:
    """
    Fetch the site's favicon or logo.

    Returns:
        Base64 encoded image data URL or empty string if not found
    """
    try:
        parsed = urlparse(site_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Try common logo locations
        logo_urls = [
            f"{base_url}/favicon.ico",
            f"{base_url}/apple-touch-icon.png",
            f"{base_url}/logo.png",
            f"{base_url}/images/logo.png",
        ]

        for logo_url in logo_urls:
            try:
                response = requests.get(logo_url, timeout=5)
                if response.status_code == 200:
                    import base64
                    content_type = response.headers.get('content-type', 'image/png')
                    encoded = base64.b64encode(response.content).decode('utf-8')
                    return f"data:{content_type};base64,{encoded}"
            except:
                continue

        return ""
    except:
        return ""

def map_pattern_to_bug_type(pattern_name: str) -> str:
    """Map pattern names to actual bug types."""
    # All our current patterns are for WordPress embeds
    wordpress_patterns = [
        'opening_structure', 'opening_with_field', 'multi_field',
        'type_field', 'field_fid', 'field_view_mode', 'complete_pattern',
        'field_array'
    ]

    if pattern_name in wordpress_patterns:
        return 'wordpress_embed'

    return 'unknown'

def analyze_bugs_by_type(results: dict) -> Tuple[Dict[str, str], Dict[str, List[dict]]]:
    """
    Analyze bugs and group by bug type (not pattern name).

    Returns:
        (bug_type_descriptions, fixes) - Dictionaries for root causes and fixes
    """
    analyzer = RootCauseAnalyzer()
    fix_gen = FixGenerator()

    # Map bug types to their descriptions
    bug_type_descriptions = {}
    bug_types_found = set()

    # Get unique bug types from results
    for result in results.get('results', []):
        # Extract patterns that matched
        patterns = result.get('patterns', {})
        for pattern_name in patterns.keys():
            bug_type = map_pattern_to_bug_type(pattern_name)
            bug_types_found.add(bug_type)

    # Generate root cause description for each bug type
    for bug_type in bug_types_found:
        if bug_type == 'wordpress_embed':
            # Analyze a sample WordPress embed
            bug_text = '[[{"fid":"1101026","view_mode":"full_width","fields":{"format":"full_width"},"type":"media"}]]'
            analysis = analyzer.analyze(bug_text, results.get('metadata', {}).get('site_scanned', ''))
            bug_type_descriptions['WordPress Embed Bugs'] = analysis['hypothesis']
        elif bug_type == 'css_styling':
            bug_type_descriptions['CSS Styling Issues'] = (
                "Visual styling bugs caused by CSS conflicts, missing styles, or specificity issues. "
                "These typically result from theme updates, plugin conflicts, or global CSS changes."
            )

    # Generate fixes for each bug type
    fixes = {}
    for bug_type in bug_types_found:
        if bug_type == 'wordpress_embed':
            fix_report = fix_gen.generate_wordpress_embed_fix(
                bug_pattern='[[{"fid":"..."}]]'
            )
            fixes['WordPress Embed Bugs'] = fix_report['options']
        elif bug_type == 'css_styling':
            fix_report = fix_gen.generate_css_fix(
                selector='.wp-block-social-links',
                property_name='list-style',
                context={'issue': 'bullets appearing'}
            )
            fixes['CSS Styling Issues'] = [fix_report]

    return bug_type_descriptions, fixes

def generate_enhanced_report(
    json_path: str,
    output_path: str,
    include_fixes: bool = True,
    fetch_logo: bool = True
):
    """
    Generate enhanced HTML report with root causes, fixes, and site logo.
    """
    print(f"📖 Loading results from {json_path}...")
    results = load_bug_results(json_path)

    site_url = results.get('metadata', {}).get('site_scanned', '')

    # Fetch site logo
    logo_url = ""
    if fetch_logo and site_url:
        print(f"🎨 Fetching logo from {site_url}...")
        logo_url = fetch_site_logo(site_url)
        if logo_url:
            print("   ✅ Logo fetched successfully")
        else:
            print("   ⚠️  Logo not found, using default header")

    print("🔍 Analyzing bugs and generating root causes...")
    bug_type_descriptions, fixes = analyze_bugs_by_type(results)

    print(f"✨ Generating enhanced HTML report...")

    # Add logo to metadata if available
    metadata = results.get('metadata', {}).copy()
    if logo_url:
        metadata['site_logo'] = logo_url

    export_to_html(
        matches=results.get('results', []),
        output_file=Path(output_path),
        metadata=metadata,
        include_fixes=include_fixes,
        root_causes=bug_type_descriptions,
        fixes=fixes
    )

    print(f"✅ Enhanced report saved to: {output_path}")
    print(f"   Root causes: {len(bug_type_descriptions)} bug types analyzed")
    print(f"   Fix options: {sum(len(opts) for opts in fixes.values())} total options")
    if logo_url:
        print(f"   Logo: Included")

    return output_path

def load_bug_results(json_path: str) -> dict:
    """Load bug scan results from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    import sys
    from urllib.parse import urlparse
    from datetime import datetime

    input_file = sys.argv[1] if len(sys.argv) > 1 else 'bug_results_www_wpr_org.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    # Auto-determine output path if not specified
    if not output_file:
        # Load results to get site URL
        results = load_bug_results(input_file)
        site_url = results.get('metadata', {}).get('site_scanned', '')

        if site_url:
            # Create project-based output path
            parsed = urlparse(site_url)
            site_slug = parsed.netloc.replace('www.', '').replace('.', '-')
            project_dir = Path("projects") / site_slug
            reports_dir = project_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = str(reports_dir / f"enhanced_report_{timestamp}.html")
        else:
            output_file = 'bug_report_enhanced.html'

    generate_enhanced_report(
        json_path=input_file,
        output_path=output_file,
        include_fixes=True,
        fetch_logo=True
    )

    print(f"\n🌐 Open in browser: file://{Path(output_file).absolute()}")
