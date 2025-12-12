#!/usr/bin/env python3.11
"""
Export utilities for bug finder results.

Supports multiple output formats:
- CSV: Comma-separated values for spreadsheet import
- HTML: Professional report with styling
- JSON: Structured data with full metadata
- TXT: Plain text format (default)
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def _calculate_priority_breakdown(matches: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate the count of bugs by priority level.

    Args:
        matches: List of bug matches

    Returns:
        Dictionary with priority counts
    """
    breakdown = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for match in matches:
        priority = match.get('priority', 'medium')
        if priority in breakdown:
            breakdown[priority] += 1
    return breakdown


def _map_pattern_to_bug_type(pattern_name: str) -> str:
    """Map pattern names to semantic bug types."""
    wordpress_patterns = [
        'opening_structure', 'opening_with_field', 'multi_field',
        'type_field', 'field_fid', 'field_view_mode', 'complete_pattern',
        'field_array'
    ]

    if pattern_name in wordpress_patterns:
        return 'WordPress Embed Bugs'

    return 'Unknown Bug Type'


def _extract_bug_types(matches: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract unique bug types (semantic names, not pattern names) and their page counts.

    Args:
        matches: List of bug matches

    Returns:
        Dictionary mapping bug types to page counts
    """
    bug_types = {}
    for match in matches:
        for pattern_name in match['patterns'].keys():
            bug_type = _map_pattern_to_bug_type(pattern_name)
            bug_types[bug_type] = bug_types.get(bug_type, 0) + 1
    return bug_types


def _generate_executive_summary(
    total_bugs: int,
    pages_scanned: Any,
    scan_date: str,
    priority_breakdown: Dict[str, int]
) -> str:
    """
    Generate HTML for executive summary section.

    Args:
        total_bugs: Total number of bugs found
        pages_scanned: Number of pages scanned
        scan_date: Date of scan
        priority_breakdown: Dictionary with priority counts

    Returns:
        HTML string for executive summary
    """
    # Determine action timeline based on priority
    if priority_breakdown['critical'] > 0:
        timeline = "Immediate action required - critical issues detected"
    elif priority_breakdown['high'] > 0:
        timeline = "Address high-priority issues within 1-2 weeks"
    elif priority_breakdown['medium'] > 0:
        timeline = "Schedule medium-priority fixes in next sprint"
    else:
        timeline = "Monitor low-priority issues for future releases"

    summary_html = f"""
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <div class="summary-cards">
                <div class="summary-card">
                    <div class="card-label">Total Issues</div>
                    <div class="card-value">{total_bugs}</div>
                </div>
                <div class="summary-card critical">
                    <div class="card-label">Critical</div>
                    <div class="card-value critical">{priority_breakdown.get('critical', 0)}</div>
                </div>
                <div class="summary-card high">
                    <div class="card-label">High</div>
                    <div class="card-value high">{priority_breakdown.get('high', 0)}</div>
                </div>
                <div class="summary-card medium">
                    <div class="card-label">Medium</div>
                    <div class="card-value medium">{priority_breakdown.get('medium', 0)}</div>
                </div>
                <div class="summary-card low">
                    <div class="card-label">Low</div>
                    <div class="card-value low">{priority_breakdown.get('low', 0)}</div>
                </div>
            </div>
            <div class="timeline">
                <strong>Recommended Timeline:</strong> {timeline}
            </div>
        </div>
"""
    return summary_html


def _generate_bug_analysis(
    bug_types: Dict[str, int],
    root_causes: Dict[str, str],
    fixes: Dict[str, List[Dict[str, Any]]],
    matches: List[Dict[str, Any]]
) -> str:
    """
    Generate HTML for bug analysis section with root causes and fixes.

    Args:
        bug_types: Dictionary mapping bug types to page counts
        root_causes: Dictionary mapping bug types to root cause descriptions
        fixes: Dictionary mapping bug types to list of fix options
        matches: Original matches list for cross-reference

    Returns:
        HTML string for bug analysis section
    """
    analysis_html = """
        <div class="bug-analysis">
            <h2>Root Cause Analysis & Proposed Fixes</h2>
"""

    for bug_type, page_count in sorted(bug_types.items(), key=lambda x: x[1], reverse=True):
        root_cause = root_causes.get(bug_type, 'No root cause analysis available.')
        bug_fixes = fixes.get(bug_type, [])

        analysis_html += f"""
            <div class="bug-type-section">
                <div class="bug-type-header" onclick="toggleBugType(this)">
                    <h3>{bug_type} <span style="font-weight: normal; color: #999; font-size: 14px;">({page_count} pages)</span></h3>
                </div>
                <div class="bug-type-content">
                    <div class="root-cause">
                        <strong>Root Cause:</strong><br>
                        {root_cause}
                    </div>
"""

        if bug_fixes:
            analysis_html += """
                    <div class="fixes-section">
                        <strong style="display: block; margin-bottom: 15px;">Proposed Fixes:</strong>
"""

            for fix_option in bug_fixes:
                title = fix_option.get('title', 'Fix Option')
                description = fix_option.get('description', '')
                code_sample = fix_option.get('code_sample', '')
                language = fix_option.get('language', 'text')
                effort = fix_option.get('effort', 'Unknown')
                priority = fix_option.get('priority', 'medium')

                analysis_html += f"""
                        <div class="fix-option">
                            <h4>
                                {title}
                                <span class="priority-badge {priority}">{priority.upper()}</span>
                            </h4>
                            <div class="fix-description">
                                {description}
                            </div>
"""

                if code_sample:
                    # Escape HTML in code samples
                    code_sample_escaped = (code_sample
                        .replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
                        .replace('"', '&quot;')
                    )
                    analysis_html += f"""
                            <div class="code-block">
                                <code>{code_sample_escaped}</code>
                            </div>
"""

                analysis_html += f"""
                            <div class="effort">Effort: {effort}</div>
                        </div>
"""

            analysis_html += """
                    </div>
"""

        analysis_html += """
                </div>
            </div>
"""

    analysis_html += """
        </div>
"""

    return analysis_html


def export_to_csv(
    matches: List[Dict[str, Any]],
    output_file: Path,
    metadata: Dict[str, Any]
) -> None:
    """
    Export bug scan results to CSV format.

    Args:
        matches: List of match dictionaries with url, total_matches, patterns
        output_file: Path to output CSV file
        metadata: Scan metadata (site_scanned, example_url, etc.)
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(['URL', 'Total Matches', 'Patterns Matched', 'Pattern Details'])

        # Data rows
        for match in matches:
            url = match['url']
            total_matches = match['total_matches']
            patterns = ', '.join(match['patterns'].keys())

            # Pattern details: pattern_name (count)
            pattern_details = '; '.join([
                f"{name} ({count})"
                for name, count in match['patterns'].items()
            ])

            writer.writerow([url, total_matches, patterns, pattern_details])


def export_to_html(
    matches: List[Dict[str, Any]],
    output_file: Path,
    metadata: Dict[str, Any],
    include_fixes: bool = False,
    root_causes: Dict[str, str] = None,
    fixes: Dict[str, List[Dict[str, Any]]] = None
) -> None:
    """
    Export bug scan results to HTML format with styling.

    Args:
        matches: List of match dictionaries
        output_file: Path to output HTML file
        metadata: Scan metadata
        include_fixes: Whether to include root cause analysis and proposed fixes
        root_causes: Dictionary mapping bug types to root cause descriptions
        fixes: Dictionary mapping bug types to lists of fix options
            Each fix option should have: title, description, code_sample, language, effort, priority
    """
    total_bugs = len(matches)
    scan_date = metadata.get('scan_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    site_scanned = metadata.get('site_scanned', 'Unknown')
    example_url = metadata.get('example_url', 'N/A')
    pages_scanned = metadata.get('pages_scanned', 'Unknown')

    # Initialize optional parameters
    if root_causes is None:
        root_causes = {}
    if fixes is None:
        fixes = {}

    # Generate site logo HTML if provided
    site_logo = metadata.get('site_logo', '')
    if site_logo:
        site_logo_html = f'<img src="{site_logo}" alt="Site Logo" style="max-height: 60px; margin-bottom: 15px; display: block;">'
    else:
        site_logo_html = ''

    # Calculate priority breakdown
    priority_breakdown = _calculate_priority_breakdown(matches)

    # Extract bug types from matches
    bug_types = _extract_bug_types(matches)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bug Scan Results - {site_scanned}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}

        .summary-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}

        .summary-item .label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .summary-item .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}

        .summary-item .value.bugs {{
            color: #e74c3c;
        }}

        .results {{
            padding: 30px;
        }}

        .results h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        thead {{
            background: #f8f9fa;
        }}

        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #e0e0e0;
            cursor: pointer;
            user-select: none;
        }}

        th:hover {{
            background: #e9ecef;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .url-link {{
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }}

        .url-link:hover {{
            text-decoration: underline;
        }}

        .match-count {{
            background: #e74c3c;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }}

        .patterns {{
            font-size: 13px;
            color: #666;
        }}

        .pattern-badge {{
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 4px;
            font-size: 11px;
        }}

        .executive-summary {{
            padding: 30px;
            background: #fff;
        }}

        .executive-summary h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .summary-card {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}

        .summary-card.critical {{
            border-left: 5px solid #e74c3c;
        }}

        .summary-card.high {{
            border-left: 5px solid #e67e22;
        }}

        .summary-card.medium {{
            border-left: 5px solid #f39c12;
        }}

        .summary-card.low {{
            border-left: 5px solid #27ae60;
        }}

        .card-label {{
            font-size: 11px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .card-value {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }}

        .card-value.critical {{
            color: #e74c3c;
        }}

        .card-value.high {{
            color: #e67e22;
        }}

        .card-value.medium {{
            color: #f39c12;
        }}

        .card-value.low {{
            color: #27ae60;
        }}

        .timeline {{
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-size: 13px;
            color: #555;
        }}

        .bug-analysis {{
            padding: 30px;
            background: #fff;
            border-top: 1px solid #e0e0e0;
        }}

        .bug-analysis h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
        }}

        .bug-type-section {{
            margin-bottom: 25px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
        }}

        .bug-type-header {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
            cursor: pointer;
            user-select: none;
        }}

        .bug-type-header:hover {{
            background: #e9ecef;
        }}

        .bug-type-header h3 {{
            font-size: 16px;
            margin: 0;
            color: #333;
        }}

        .bug-type-content {{
            padding: 20px;
            background: white;
            display: none;
        }}

        .bug-type-content.show {{
            display: block;
        }}

        .root-cause {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-size: 14px;
            color: #555;
            line-height: 1.6;
        }}

        .fixes-section {{
            margin-top: 20px;
        }}

        .fix-option {{
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 15px;
            background: #fafbfc;
        }}

        .fix-option h4 {{
            font-size: 15px;
            margin: 0 0 10px 0;
            color: #333;
        }}

        .fix-description {{
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.5;
        }}

        .code-block {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 10px 0;
        }}

        .code-block code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            line-height: 1.4;
        }}

        .effort {{
            display: inline-block;
            margin-top: 10px;
            padding: 5px 10px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 12px;
            color: #555;
        }}

        .priority-badge {{
            display: inline-block;
            margin-left: 10px;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}

        .priority-badge.critical {{
            background: #e74c3c;
        }}

        .priority-badge.high {{
            background: #e67e22;
        }}

        .priority-badge.medium {{
            background: #f39c12;
        }}

        .priority-badge.low {{
            background: #27ae60;
        }}

        .details-toggle {{
            cursor: pointer;
            text-decoration: underline;
            color: #667eea;
        }}

        .priority-column {{
            text-align: center;
            font-weight: 600;
        }}

        .priority-critical {{
            color: #e74c3c;
        }}

        .priority-high {{
            color: #e67e22;
        }}

        .priority-medium {{
            color: #f39c12;
        }}

        .priority-low {{
            color: #27ae60;
        }}

        .fix-indicator {{
            text-align: center;
            font-size: 18px;
        }}

        .fix-available {{
            color: #27ae60;
        }}

        .fix-unavailable {{
            color: #bdc3c7;
        }}

        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {site_logo_html}
            <h1>Bug Scan Results</h1>
            <p>Visual bug detection report for {site_scanned}</p>
        </div>

        <div class="summary">
            <div class="summary-item">
                <div class="label">Bugs Found</div>
                <div class="value bugs">{total_bugs}</div>
            </div>
            <div class="summary-item">
                <div class="label">Pages Scanned</div>
                <div class="value">{pages_scanned}</div>
            </div>
            <div class="summary-item">
                <div class="label">Scan Date</div>
                <div class="value" style="font-size: 14px; margin-top: 5px;">{scan_date}</div>
            </div>
            <div class="summary-item">
                <div class="label">Example URL</div>
                <div class="value" style="font-size: 11px; word-break: break-all; margin-top: 5px;">
                    <a href="{example_url}" class="url-link" target="_blank">{example_url[:50]}...</a>
                </div>
            </div>
        </div>
"""

    # Executive Summary section
    if include_fixes:
        executive_summary_html = _generate_executive_summary(total_bugs, pages_scanned, scan_date, priority_breakdown)
        html_content += executive_summary_html

    html_content += """

        <div class="results">
            <h2>Affected Pages</h2>
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">#</th>
                        <th onclick="sortTable(1)">URL</th>
                        <th onclick="sortTable(2)">Matches</th>
                        <th onclick="sortTable(3)">Patterns</th>
"""

    # Add Priority and Fix columns if fixes are included
    if include_fixes:
        html_content += """
                        <th onclick="sortTable(4)">Priority</th>
                        <th onclick="sortTable(5)">Fix Available</th>
"""

    html_content += """
                    </tr>
                </thead>
                <tbody>
"""

    # Add table rows
    for i, match in enumerate(matches, 1):
        url = match['url']
        total_matches = match['total_matches']
        priority = match.get('priority', 'medium')

        # Pattern badges
        pattern_badges = ''.join([
            f'<span class="pattern-badge">{name} ({count})</span>'
            for name, count in match['patterns'].items()
        ])

        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td><a href="{url}" class="url-link" target="_blank">{url}</a></td>
                        <td><span class="match-count">{total_matches}</span></td>
                        <td class="patterns">{pattern_badges}</td>
"""

        # Add Priority and Fix columns if included
        if include_fixes:
            # Determine if fixes are available for any pattern in this match
            has_fixes = any(pattern_name in fixes for pattern_name in match['patterns'].keys())
            fix_indicator = '<span class="fix-indicator fix-available">✓</span>' if has_fixes else '<span class="fix-indicator fix-unavailable">—</span>'

            html_content += f"""
                        <td class="priority-column priority-{priority}">{priority.upper()}</td>
                        <td class="fix-indicator">{fix_indicator}</td>
"""

        html_content += """
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Bug Analysis section
    if include_fixes and (root_causes or fixes):
        bug_analysis_html = _generate_bug_analysis(bug_types, root_causes, fixes, matches)
        html_content += bug_analysis_html

    html_content += """
        <div class="footer">
            Generated by Bug Finder - Website Analyzer Tool
        </div>
    </div>

    <script>
        function sortTable(column) {
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                let aVal = a.children[column].innerText;
                let bVal = b.children[column].innerText;

                // Numeric sort for # and Matches columns
                if (column === 0 || column === 2) {
                    aVal = parseInt(aVal);
                    bVal = parseInt(bVal);
                }

                return aVal > bVal ? 1 : -1;
            });

            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }

        function toggleBugType(element) {
            const content = element.nextElementSibling;
            content.classList.toggle('show');
        }

        // Auto-expand first bug type section
        document.addEventListener('DOMContentLoaded', function() {
            const firstSection = document.querySelector('.bug-type-header');
            if (firstSection) {
                firstSection.nextElementSibling.classList.add('show');
            }
        });
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def export_to_json(
    matches: List[Dict[str, Any]],
    output_file: Path,
    metadata: Dict[str, Any]
) -> None:
    """
    Export bug scan results to JSON format.

    Args:
        matches: List of match dictionaries
        output_file: Path to output JSON file
        metadata: Scan metadata
    """
    output_data = {
        "metadata": {
            "scan_date": metadata.get('scan_date', datetime.now().isoformat()),
            "site_scanned": metadata.get('site_scanned'),
            "example_url": metadata.get('example_url'),
            "pages_scanned": metadata.get('pages_scanned'),
            "total_bugs_found": len(matches),
        },
        "results": matches
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def export_to_txt(
    matches: List[Dict[str, Any]],
    output_file: Path,
    metadata: Dict[str, Any]
) -> None:
    """
    Export bug scan results to plain text format.

    Args:
        matches: List of match dictionaries
        output_file: Path to output text file
        metadata: Scan metadata
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Bug Scan Results for {metadata.get('site_scanned')}\n")
        f.write(f"Example URL: {metadata.get('example_url')}\n")
        f.write(f"Pages scanned: {metadata.get('pages_scanned')}\n")
        f.write(f"Bugs found: {len(matches)}\n")
        f.write(f"Scan date: {metadata.get('scan_date', 'N/A')}\n")
        f.write("=" * 70 + "\n\n")

        for match in matches:
            f.write(f"{match['url']}\n")
            f.write(f"  Matches: {match['total_matches']}\n")

            # Pattern details
            for pattern_name, count in match['patterns'].items():
                f.write(f"    - {pattern_name}: {count}\n")

            f.write("\n")


def export_results(
    matches: List[Dict[str, Any]],
    output_file: Path,
    metadata: Dict[str, Any],
    format: str = 'txt'
) -> None:
    """
    Export bug scan results in the specified format.

    Args:
        matches: List of match dictionaries
        output_file: Base path for output file (extension may be changed)
        metadata: Scan metadata
        format: Output format - 'txt', 'csv', 'html', 'json', or 'all'
    """
    # Ensure output_file is a Path object
    output_file = Path(output_file)
    base_path = output_file.with_suffix('')  # Remove extension

    if format == 'all':
        # Export to all formats
        export_to_txt(matches, base_path.with_suffix('.txt'), metadata)
        export_to_csv(matches, base_path.with_suffix('.csv'), metadata)
        export_to_html(matches, base_path.with_suffix('.html'), metadata)
        export_to_json(matches, base_path.with_suffix('.json'), metadata)
    elif format == 'csv':
        export_to_csv(matches, base_path.with_suffix('.csv'), metadata)
    elif format == 'html':
        export_to_html(matches, base_path.with_suffix('.html'), metadata)
    elif format == 'json':
        export_to_json(matches, base_path.with_suffix('.json'), metadata)
    else:  # default to txt
        export_to_txt(matches, base_path.with_suffix('.txt'), metadata)
