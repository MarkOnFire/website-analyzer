# Projects & Workspaces Guide

Manage multiple website analyses with persistent workspaces.

**See Also:** [Quick Start](../../QUICKSTART.md) | [Main README](../../README.md)

---

## What is a Project?

A project is a persistent workspace for analyzing a single website. It includes:

- **Snapshots**: Historical crawls of the site (can compare over time)
- **Test Results**: Detailed findings from each analysis
- **Issues**: Tracked problems with status (open/in-progress/fixed/verified)
- **Metadata**: Project configuration and tracking

---

## Quick Start

```bash
# Create a project
python -m src.analyzer.cli project new "https://www.example.com"

# Crawl the site
python -m src.analyzer.cli crawl start example-com --max-pages 1000

# Run analyses
python -m src.analyzer.cli test run example-com --test migration-scanner
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com"

# View issues
python -m src.analyzer.cli issues list example-com
```

---

## Project Structure

```
projects/
├── README.md
├── example-com/
│   ├── metadata.json                         # Project metadata
│   ├── issues.json                           # Issue tracking
│   ├── snapshots/
│   │   ├── 2025-12-10T14-30-45.123456Z/     # Snapshot timestamp
│   │   │   ├── pages/example-com/
│   │   │   │   ├── raw.html                 # Original HTML
│   │   │   │   ├── cleaned.html             # Cleaned version
│   │   │   │   └── content.md               # Markdown conversion
│   │   │   ├── sitemap.json                 # All discovered URLs
│   │   │   └── summary.json                 # Crawl statistics
│   │   └── 2025-12-05T09-12-34.567890Z/     # Earlier snapshot
│   ├── test-results/
│   │   ├── results_2025-12-10T14-30-45.json # Migration scanner results
│   │   └── results_2025-12-05T09-12-34.json # Earlier test run
│   └── logs/
│       └── crawl_2025-12-10.log              # Crawl progress
```

### File Descriptions

**metadata.json** - Project information
```json
{
  "slug": "example-com",
  "url": "https://www.example.com",
  "created_at": "2025-12-10T14:30:45.123456Z",
  "last_updated": "2025-12-10T15:45:30.567890Z"
}
```

**issues.json** - Tracked issues across analyses
```json
{
  "issues": [
    {
      "id": "issue-001",
      "title": "131 WordPress embed codes not rendering",
      "status": "open",
      "created_at": "2025-12-10T14:30:45Z",
      "description": "Found via bug-finder scan"
    }
  ]
}
```

**snapshots/** - Historical site crawls
- Can have multiple snapshots (from different dates)
- Each snapshot is independent and can be analyzed separately
- Useful for comparing changes over time

**test-results/** - All test outputs
- One file per test run with timestamp
- Includes all findings, patterns, and suggestions
- Can be exported to CSV, HTML, etc.

---

## Project Commands

### Create a Project

```bash
python -m src.analyzer.cli project new "https://www.example.com"
```

Creates `projects/example-com/` with metadata.

### List Projects

```bash
python -m src.analyzer.cli project list
```

Shows all projects and their status.

### View Project Info

```bash
python -m src.analyzer.cli project info example-com
```

Shows project details, recent snapshots, and test results.

### List Snapshots

```bash
python -m src.analyzer.cli project snapshots example-com
```

Shows all historical snapshots with dates and page counts.

---

## Crawl Commands

### Start a Crawl

```bash
# Basic crawl (1000 pages default)
python -m src.analyzer.cli crawl start example-com

# Crawl limited pages
python -m src.analyzer.cli crawl start example-com --max-pages 500

# Crawl with specific depth
python -m src.analyzer.cli crawl start example-com --max-depth 3
```

Creates a new snapshot in `projects/example-com/snapshots/`.

### List Crawls

```bash
python -m src.analyzer.cli crawl list example-com
```

Shows all snapshots with timestamps and page counts.

### Crawl Status

```bash
python -m src.analyzer.cli crawl status example-com
```

Shows status of any in-progress crawls.

---

## Running Tests

### Run Migration Scanner

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "pattern_name":"regex_pattern"
    }
  }'
```

### Run Bug Finder on Snapshot

```bash
python -m src.analyzer.cli test run example-com \
  --test bug-finder \
  --config 'bug-finder:{
    "example_url":"https://example.com/bug",
    "site":"https://example.com"
  }'
```

### Run Multiple Tests

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --test link-checker \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'
```

### Use Specific Snapshot

```bash
python -m src.analyzer.cli test run example-com \
  --snapshot "2025-12-05T09-12-34.567890Z" \
  --test migration-scanner \
  --config '...'
```

Runs test on an earlier snapshot instead of the latest.

---

## Issue Tracking

### List Issues

```bash
# All issues
python -m src.analyzer.cli issues list example-com

# By status
python -m src.analyzer.cli issues list example-com --status open
python -m src.analyzer.cli issues list example-com --status in-progress
python -m src.analyzer.cli issues list example-com --status fixed

# By test type
python -m src.analyzer.cli issues list example-com --test migration-scanner
```

### Show Issue Details

```bash
python -m src.analyzer.cli issues show example-com ISSUE_ID
```

### Update Issue Status

```bash
python -m src.analyzer.cli issues update example-com ISSUE_ID --status in-progress
python -m src.analyzer.cli issues update example-com ISSUE_ID --status fixed
```

### Compare Results Over Time

```bash
# Compare two snapshots
python -m src.analyzer.cli issues compare example-com \
  --from "2025-12-01" --to "2025-12-08"

# This shows:
# - New issues found in second snapshot
# - Issues that were fixed
# - Issues that got worse or better
```

---

## Workflow Examples

### Weekly Regression Testing

```bash
#!/bin/bash

SITE="example-com"
SITE_URL="https://www.example.com"

# 1. Crawl the site
echo "Crawling $SITE_URL..."
python -m src.analyzer.cli crawl start $SITE --max-pages 1000

# 2. Run standard tests
echo "Running migration scanner..."
python -m src.analyzer.cli test run $SITE \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "http_links":"http://[^s]",
      "flash":"\.swf"
    }
  }'

# 3. View summary
echo "Results:"
cat projects/$SITE/test-results/results_*.json | jq '.summary'

# 4. Compare with previous week
echo "Comparing with previous week..."
python -m src.analyzer.cli issues compare $SITE \
  --from "$(date -d '7 days ago' +%Y-%m-%d)" \
  --to "$(date +%Y-%m-%d)"
```

### Bug Fix Verification

```bash
#!/bin/bash

SITE="wpr-org"
BUG_PAGE="https://www.wpr.org/food/article"

echo "1. Baseline crawl before fix..."
python -m src.analyzer.cli crawl start $SITE --max-pages 5000
python -m src.analyzer.cli bug-finder scan \
  --example-url "$BUG_PAGE" \
  --site "https://www.wpr.org"

echo "2. Make your fix..."
echo "3. Wait and crawl again..."
sleep 3600  # Wait 1 hour for cache to clear

python -m src.analyzer.cli crawl start $SITE --max-pages 5000
python -m src.analyzer.cli bug-finder scan \
  --example-url "$BUG_PAGE" \
  --site "https://www.wpr.org"

echo "4. Compare results..."
python -m src.analyzer.cli issues compare $SITE --from "2025-12-10" --to "2025-12-11"
```

### Migration Project Tracking

```bash
#!/bin/bash

SITE="mysite-com"

# Phase 1: Find all jQuery
echo "Finding all jQuery patterns..."
python -m src.analyzer.cli crawl start $SITE --max-pages 2000
python -m src.analyzer.cli test run $SITE \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_live":"\\.live\\s*\\(",
      "jquery_bind":"\\.bind\\s*\\(",
      "jquery_ajax":"\\.ajax\\s*\\("
    }
  }'

BASELINE=$(cat projects/$SITE/test-results/results_*.json | jq '.summary')
echo "Baseline: $BASELINE"

# Phase 2-N: After each code change
for i in {1..10}; do
  echo "Iteration $i..."
  sleep 86400  # Wait 1 day
  python -m src.analyzer.cli crawl start $SITE --max-pages 2000
  python -m src.analyzer.cli test run $SITE \
    --test migration-scanner \
    --config 'migration-scanner:{...}'

  CURRENT=$(cat projects/$SITE/test-results/results_*.json | jq '.summary')
  echo "Current: $CURRENT"

  # Check if done
  if [[ "$CURRENT" == *"Found 0"* ]]; then
    echo "✅ All jQuery patterns migrated!"
    break
  fi
done
```

---

## Export & Sharing

### Export Test Results

```bash
# JSON (already saved)
cat projects/example-com/test-results/results_*.json

# Convert to CSV
jq -r '.details.findings[] | [.url, .pattern_name, .line_number] | @csv' \
  projects/example-com/test-results/results_*.json > findings.csv

# Convert to HTML report
python generate_enhanced_report_v2.py \
  projects/example-com/scans/bug_results_example-com.json
```

### Share Issues

```bash
# Export as markdown
python -c "
import json
with open('projects/example-com/issues.json') as f:
    issues = json.load(f)
    for issue in issues['issues']:
        print(f\"## {issue['title']}\")
        print(f\"Status: {issue['status']}\")
        print(f\"Description: {issue['description']}\")
        print()
" > issues_report.md

# Export as CSV
jq -r '.issues[] | [.id, .title, .status, .created_at] | @csv' \
  projects/example-com/issues.json > issues.csv
```

---

## Maintenance

### Archive Old Snapshots

```bash
# List old snapshots
ls -la projects/example-com/snapshots/ | head -20

# Remove specific snapshot (careful!)
rm -rf projects/example-com/snapshots/2025-11-01T*

# Or just keep last N snapshots
cd projects/example-com/snapshots/
ls -t | tail -n +4 | xargs rm -rf
```

### Clean Up Results

```bash
# Keep results but remove logs
find projects/example-com -name "*.log" -delete

# Or archive old test results
tar -czf projects/example-com/test-results/archive-2025-11.tar.gz \
  projects/example-com/test-results/results_2025-11*.json
```

### Reset Project

```bash
# Remove entire project workspace
rm -rf projects/example-com

# Create fresh project
python -m src.analyzer.cli project new "https://www.example.com"
```

---

## Tips & Best Practices

1. **Use meaningful project slugs**: `wpr-org` is better than `site1`
2. **Archive old snapshots**: Don't let the projects/ directory get too large
3. **Version control configs**: Save your test configs in git
4. **Document findings**: Add notes to issues for team context
5. **Batch similar tests**: Run multiple patterns in one command to save time
6. **Use specific snapshots**: Reference old snapshots by timestamp to compare over time

---

## See Also

- [Quick Start Guide](../../QUICKSTART.md)
- [Bug Finder Guide](BUG_FINDER.md)
- [Migration Scanner Guide](MIGRATION_SCANNER.md)
- [Main README](../../README.md)
