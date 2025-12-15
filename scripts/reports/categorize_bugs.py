#!/usr/bin/env python3.11
"""
Categorize bug scan results into actionable buckets for triage.

This script analyzes scan results and groups affected pages by:
- URL patterns (events, shows, news articles, etc.)
- Priority (high/medium/low based on page type)
- Severity (based on number of matches)

Output: Enhanced report with categorization for efficient remediation.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set
from dataclasses import dataclass, asdict


@dataclass
class PageCategory:
    """Category definition for grouping pages."""
    name: str
    pattern: str
    priority: str  # 'high', 'medium', 'low', 'skip'
    description: str


# WPR.org URL pattern categories
CATEGORIES = [
    PageCategory(
        name="Events",
        pattern=r"/events?/",
        priority="skip",
        description="Event pages (ephemeral/disposable content)"
    ),
    PageCategory(
        name="Shows",
        pattern=r"/shows/",
        priority="high",
        description="Show pages (high-value evergreen content)"
    ),
    PageCategory(
        name="News Articles",
        pattern=r"/(news|politics|health|economy|environment|education|culture|history|social-issues|sports|music|art|animals|weather)/",
        priority="medium",
        description="News and topical articles (medium-value content)"
    ),
    PageCategory(
        name="Homepage",
        pattern=r"^https?://[^/]+/?$",
        priority="high",
        description="Homepage (critical high-traffic page)"
    ),
    PageCategory(
        name="Section Pages",
        pattern=r"^https?://[^/]+/[^/]+/?$",
        priority="high",
        description="Top-level section pages (high-traffic pages)"
    ),
    PageCategory(
        name="About/Info",
        pattern=r"/(about|contact|staff|support|donate)/",
        priority="medium",
        description="About and informational pages"
    ),
    PageCategory(
        name="Uncategorized",
        pattern=r".*",  # Catch-all
        priority="medium",
        description="Other pages not matching specific patterns"
    ),
]


class BugCategorizer:
    """Categorize and triage bug scan results."""

    def __init__(self, scan_file: Path):
        """Initialize categorizer with scan results file."""
        self.scan_file = scan_file
        self.data = self._load_scan()
        self.categories: Dict[str, List[dict]] = defaultdict(list)
        self.stats: Dict[str, dict] = {}

    def _load_scan(self) -> dict:
        """Load scan results from JSON file."""
        with open(self.scan_file, 'r') as f:
            return json.load(f)

    def categorize(self) -> None:
        """Categorize all affected pages."""
        results = self.data.get('results', [])

        for page in results:
            url = page['url']
            category = self._match_category(url)
            self.categories[category.name].append({
                'url': url,
                'matches': page.get('total_matches', 0),
                'patterns': page.get('patterns', []),
                'priority': category.priority,
            })

        # Calculate stats for each category
        for cat_name, pages in self.categories.items():
            cat = next(c for c in CATEGORIES if c.name == cat_name)
            self.stats[cat_name] = {
                'count': len(pages),
                'priority': cat.priority,
                'description': cat.description,
                'total_matches': sum(p['matches'] for p in pages),
                'avg_matches': sum(p['matches'] for p in pages) / len(pages) if pages else 0,
            }

    def _match_category(self, url: str) -> PageCategory:
        """Match URL to category."""
        for category in CATEGORIES:
            if re.search(category.pattern, url, re.IGNORECASE):
                return category
        return CATEGORIES[-1]  # Uncategorized fallback

    def generate_report(self, output_file: Path) -> None:
        """Generate categorized report."""
        report = {
            'metadata': {
                'source_scan': str(self.scan_file),
                'total_pages': self.data.get('metadata', {}).get('pages_scanned', 0),
                'total_bugs_found': self.data.get('metadata', {}).get('bugs_found', 0),
                'categories_found': len(self.categories),
            },
            'summary': self._generate_summary(),
            'categories': self._format_categories(),
            'triage_recommendations': self._generate_recommendations(),
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Categorized report saved to: {output_file}")

    def _generate_summary(self) -> Dict:
        """Generate summary statistics."""
        priority_counts = defaultdict(int)
        priority_matches = defaultdict(int)

        for cat_name, stats in self.stats.items():
            priority = stats['priority']
            priority_counts[priority] += stats['count']
            priority_matches[priority] += stats['total_matches']

        return {
            'by_priority': {
                'high': {
                    'pages': priority_counts['high'],
                    'matches': priority_matches['high'],
                    'percentage': round(100 * priority_counts['high'] / sum(priority_counts.values()), 1)
                },
                'medium': {
                    'pages': priority_counts['medium'],
                    'matches': priority_matches['medium'],
                    'percentage': round(100 * priority_counts['medium'] / sum(priority_counts.values()), 1)
                },
                'low': {
                    'pages': priority_counts['low'],
                    'matches': priority_matches['low'],
                    'percentage': round(100 * priority_counts['low'] / sum(priority_counts.values()), 1)
                },
                'skip': {
                    'pages': priority_counts['skip'],
                    'matches': priority_matches['skip'],
                    'percentage': round(100 * priority_counts['skip'] / sum(priority_counts.values()), 1)
                },
            },
            'top_categories': sorted(
                self.stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
        }

    def _format_categories(self) -> Dict:
        """Format category data for output."""
        formatted = {}
        for cat_name, pages in self.categories.items():
            formatted[cat_name] = {
                'stats': self.stats[cat_name],
                'sample_pages': pages[:10],  # First 10 as samples
                'all_urls': [p['url'] for p in pages],
            }
        return formatted

    def _generate_recommendations(self) -> List[Dict]:
        """Generate triage recommendations."""
        recommendations = []

        # High priority items
        high_priority = sum(
            stats['count'] for stats in self.stats.values()
            if stats['priority'] == 'high'
        )
        if high_priority > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'action': f'Fix {high_priority} high-priority pages first',
                'rationale': 'High-traffic pages (homepage, sections, shows) have maximum user impact',
                'pages': high_priority,
            })

        # Medium priority
        medium_priority = sum(
            stats['count'] for stats in self.stats.values()
            if stats['priority'] == 'medium'
        )
        if medium_priority > 0:
            recommendations.append({
                'priority': 'IMPORTANT',
                'action': f'Fix {medium_priority} medium-priority pages next',
                'rationale': 'News articles and info pages have moderate user impact',
                'pages': medium_priority,
            })

        # Skip items
        skip_count = sum(
            stats['count'] for stats in self.stats.values()
            if stats['priority'] == 'skip'
        )
        if skip_count > 0:
            recommendations.append({
                'priority': 'INFO',
                'action': f'Consider ignoring {skip_count} event pages',
                'rationale': 'Ephemeral content with low long-term value',
                'pages': skip_count,
            })

        return recommendations

    def generate_markdown_report(self, output_file: Path) -> None:
        """Generate human-readable markdown report."""
        lines = [
            "# Bug Scan Categorization Report",
            "",
            f"**Source:** `{self.scan_file.name}`",
            f"**Total Pages Scanned:** {self.data.get('metadata', {}).get('pages_scanned', 0):,}",
            f"**Bugs Found:** {self.data.get('metadata', {}).get('bugs_found', 0):,}",
            "",
            "---",
            "",
            "## Priority Summary",
            "",
        ]

        summary = self._generate_summary()

        # Priority breakdown
        for priority in ['high', 'medium', 'low', 'skip']:
            data = summary['by_priority'][priority]
            lines.append(f"### {priority.upper()} Priority")
            lines.append(f"- **Pages:** {data['pages']:,} ({data['percentage']}%)")
            lines.append(f"- **Total Matches:** {data['matches']:,}")
            lines.append("")

        # Triage recommendations
        lines.extend([
            "## Triage Recommendations",
            "",
        ])

        for rec in self._generate_recommendations():
            lines.append(f"### {rec['priority']}: {rec['action']}")
            lines.append(f"- **Rationale:** {rec['rationale']}")
            lines.append(f"- **Pages Affected:** {rec['pages']:,}")
            lines.append("")

        # Category breakdown
        lines.extend([
            "---",
            "",
            "## Category Breakdown",
            "",
        ])

        # Sort by priority, then by count
        priority_order = {'high': 0, 'medium': 1, 'low': 2, 'skip': 3}
        sorted_categories = sorted(
            self.stats.items(),
            key=lambda x: (priority_order.get(x[1]['priority'], 4), -x[1]['count'])
        )

        for cat_name, stats in sorted_categories:
            lines.append(f"### {cat_name} ({stats['priority'].upper()} priority)")
            lines.append(f"- **Description:** {stats['description']}")
            lines.append(f"- **Pages:** {stats['count']:,}")
            lines.append(f"- **Total Matches:** {stats['total_matches']:,}")
            lines.append(f"- **Avg Matches/Page:** {stats['avg_matches']:.1f}")

            # Sample URLs
            if self.categories[cat_name]:
                lines.append("")
                lines.append("**Sample Pages:**")
                for page in self.categories[cat_name][:5]:
                    lines.append(f"- [{page['url']}]({page['url']}) ({page['matches']} matches)")

            lines.append("")

        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))

        print(f"✓ Markdown report saved to: {output_file}")


def main():
    """Run categorization on latest scan."""
    import sys

    # Default to latest Phase 3 scan
    scan_file = Path("projects/wpr-org/scans/scan_20251212_050000_50000p_results.json")

    if len(sys.argv) > 1:
        scan_file = Path(sys.argv[1])

    if not scan_file.exists():
        print(f"Error: Scan file not found: {scan_file}")
        print(f"Usage: {sys.argv[0]} [scan_file.json]")
        sys.exit(1)

    print(f"Categorizing scan results from: {scan_file}")
    print()

    categorizer = BugCategorizer(scan_file)
    categorizer.categorize()

    # Generate reports using naming convention
    # Extract date from scan filename (scan_YYYYMMDD_HHmmss_<pages>p_results.json)
    import re
    match = re.search(r'scan_(\d{8})_\d{6}_(\d+)p', scan_file.stem)
    if match:
        date_str = match.group(1)
        pages = match.group(2)
        base_name = f"report_{date_str}_triage_{pages}p"
    else:
        # Fallback for non-standard filenames
        base_name = scan_file.stem.replace('_results', '') + '_triage'

    output_dir = scan_file.parent.parent / 'reports'
    output_dir.mkdir(exist_ok=True)

    json_output = output_dir / f"{base_name}.json"
    md_output = output_dir / f"{base_name}.md"

    categorizer.generate_report(json_output)
    categorizer.generate_markdown_report(md_output)

    print()
    print("=" * 60)
    print("CATEGORIZATION COMPLETE")
    print("=" * 60)
    print()
    print(f"JSON Report: {json_output}")
    print(f"Markdown Report: {md_output}")


if __name__ == "__main__":
    main()
