# Bug Categorization Tool

Categorizes bug scan results into actionable priority buckets for efficient triage and remediation.

## Overview

The categorization tool analyzes scan results and groups affected pages by:
- **URL patterns** (events, shows, news articles, etc.)
- **Priority levels** (HIGH, MEDIUM, LOW, SKIP)
- **Severity** (based on number of matches per page)

This allows you to focus remediation efforts on high-value pages first and potentially ignore ephemeral content.

## Usage

### Basic Usage

Run on the latest scan in a project directory:

```bash
python3.11 scripts/reports/categorize_bugs.py projects/wpr-org/scans/scan_20251212_050000_50000p_results.json
```

### Output

The script generates two reports following the naming convention:

- **Markdown Report**: `report_YYYYMMDD_triage_<pages>p.md`
  - Human-readable priority breakdown
  - Triage recommendations
  - Sample pages for each category

- **JSON Report**: `report_YYYYMMDD_triage_<pages>p.json`
  - Complete categorization data
  - Full URL lists per category
  - Statistics and metadata

### Example Output Structure

```
projects/wpr-org/
├── scans/
│   └── scan_20251212_050000_50000p_results.json
└── reports/
    ├── report_20251212_triage_50000p.md      ← Markdown report
    └── report_20251212_triage_50000p.json    ← JSON data
```

## Customizing Priority Rules

Priority categorization is **site-specific**. You can customize rules by creating a `triage_config.json` file in your project directory.

### Configuration Format

```json
{
  "site": "example.com",
  "description": "Priority rules for example.com",
  "categories": [
    {
      "name": "Category Name",
      "pattern": "/regex/pattern/",
      "priority": "high|medium|low|skip",
      "description": "What this category represents"
    }
  ],
  "priority_definitions": {
    "high": "Description of high priority",
    "medium": "Description of medium priority",
    "low": "Description of low priority",
    "skip": "Description of skip priority"
  }
}
```

### Priority Level Guidelines

Based on user requirements:

- **HIGH Priority**: Hub pages, homepages, and evergreen content
  - Maximum user impact
  - Fix these first

- **MEDIUM Priority**: News articles, show notes from daily talk shows
  - Moderate user impact
  - Fix after high-priority items

- **LOW Priority**: Content with limited reach
  - Minor impact
  - Fix when convenient

- **SKIP Priority**: Extremely time-related content
  - Events, announcements, ephemeral pages
  - Can safely ignore

### Example: WPR.org Configuration

See `projects/wpr-org/triage_config.json` for a complete example.

Key categories for news/media sites:
- **Events** → SKIP (ephemeral calendar pages)
- **Shows** → HIGH (evergreen podcast/series content)
- **News Articles** → MEDIUM (topical content)
- **Hub Pages** → HIGH (section landing pages)
- **Homepage** → HIGH (highest traffic page)

## Integration with Workflows

### After a Scan

1. Run the bug finder scan
2. Run categorization on scan results
3. Review the triage report
4. Focus remediation on HIGH priority pages first

### Command Sequence

```bash
# 1. Run bug finder scan
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/page-with-bug" \
  --site "https://example.com" \
  --max-pages 50000 \
  --output projects/example-com/scans/bug_results

# 2. Categorize results
python3.11 scripts/reports/categorize_bugs.py \
  projects/example-com/scans/scan_20251212_*.json

# 3. Review triage report
cat projects/example-com/reports/report_20251212_triage_*.md
```

## Report Structure

### Markdown Report Sections

1. **Priority Summary**
   - Breakdown by priority level
   - Page counts and percentages
   - Total matches per priority

2. **Triage Recommendations**
   - Actionable next steps
   - Rationale for each priority
   - Page counts affected

3. **Category Breakdown**
   - Detailed stats per category
   - Sample pages with match counts
   - Average matches per page

### JSON Report Structure

```json
{
  "metadata": {
    "source_scan": "path/to/scan.json",
    "total_pages": 50000,
    "total_bugs_found": 1906,
    "categories_found": 7
  },
  "summary": {
    "by_priority": {
      "high": { "pages": 328, "matches": 1957, "percentage": 17.2 },
      "medium": { "pages": 198, "matches": 1089, "percentage": 10.4 },
      "skip": { "pages": 1380, "matches": 1380, "percentage": 72.4 }
    }
  },
  "categories": {
    "Shows": {
      "stats": { "count": 5, "priority": "high", ... },
      "all_urls": [ "url1", "url2", ... ]
    }
  },
  "triage_recommendations": [ ... ]
}
```

## Tips for Creating Custom Rules

1. **Order matters**: Categories are matched in order, first match wins
2. **Use specific patterns first**: Put specific patterns before generic ones
3. **End with catch-all**: Last category should be `"pattern": ".*"` to catch everything
4. **Test patterns**: Use regex testers to validate URL patterns
5. **Consider site structure**: Align categories with your site's information architecture

## Future Enhancements

Potential improvements:
- CLI flag to specify custom config file path
- Support for multiple config files (per-site presets)
- Interactive mode to help build category rules
- Export filtered URL lists by priority
- Integration with CLI export command

## Related Documentation

- `NAMING_CONVENTION.md` - File naming standards
- `CURRENT_SCAN.md` - Latest scan status and reports
- `bug_finder_cli.py` - Main scanning tool
