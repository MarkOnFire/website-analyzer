# Projects Directory

This directory contains all website-specific data, scan results, and reports. Each website gets its own subdirectory organized by site slug (domain with dashes instead of dots).

## Directory Structure

```
projects/
├── <site-slug>/          # e.g., wpr-org for www.wpr.org
│   ├── scans/            # Raw scan results (JSON, HTML, CSV, TXT)
│   ├── reports/          # Enhanced HTML reports with analysis
│   ├── logs/             # Scan logs and debug output
│   └── patterns/         # Custom bug patterns for this site
```

## Why This Structure?

- **Git-ignored**: The entire `projects/` directory is excluded from version control (see `.gitignore`)
- **Organized**: All artifacts for a website stay together
- **Clean repo**: Keeps the tool's codebase separate from website data
- **Scalable**: Easy to manage multiple website investigations

## Usage

### Running a Bug Scan

The bug-finder automatically creates the project directory structure:

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/page-with-bug" \
  --site "https://www.example.com" \
  --max-pages 1000
```

**Output goes to**: `projects/example-com/scans/bug_results_example-com.*`

### Generating Enhanced Reports

Generate an enhanced report from scan results:

```bash
# Auto-detects output path from input file
python generate_enhanced_report_v2.py projects/example-com/scans/bug_results_example-com.json

# Or specify custom output path
python generate_enhanced_report_v2.py \
  projects/example-com/scans/bug_results_example-com.json \
  projects/example-com/reports/my_custom_report.html
```

**Default output**: `projects/example-com/reports/enhanced_report_YYYYMMDD_HHMMSS.html`

### Generating Markdown Summaries

For quick sharing in Slack or email (less formal than the full HTML report):

```bash
# Standard Markdown (all URLs, includes context)
python bug_finder_export_markdown.py projects/example-com/scans/bug_results_example-com.json

# Slack-friendly snippet (20 URLs max, minimal formatting)
python bug_finder_export_markdown.py projects/example-com/scans/bug_results_example-com.json --slack

# Custom output path
python bug_finder_export_markdown.py \
  projects/example-com/scans/bug_results_example-com.json \
  projects/example-com/reports/summary.md
```

**Use cases:**
- **Markdown (.md)**: Complete list of URLs with context - easy to copy-paste and trim as needed
- **Slack snippet (.txt)**: Ultra-concise for pasting into chat - just 20 URLs with one-line context

## File Types

### Scans Directory

- **`.json`**: Complete scan results with metadata (use for report generation)
- **`.html`**: Basic HTML table view of results
- **`.csv`**: Spreadsheet format for analysis
- **`.txt`**: Plain text summary

### Reports Directory

- **`enhanced_report_*.html`**: Full analysis with:
  - Site logo
  - Root cause analysis
  - Fix recommendations with code samples
  - Executive summary
  - Severity breakdown

### Logs Directory

- **`scan_phase*.log`**: Detailed scan progress and debug output

### Patterns Directory

- Custom bug pattern definitions for this specific site
- JSON files defining regex patterns and matching rules

## Example: WPR.org Investigation

```
projects/wpr-org/
├── scans/
│   ├── bug_results_wpr_complete.json      # 15,000 pages, 131 bugs
│   ├── bug_results_wpr_complete.html
│   ├── bug_results_wpr_complete.csv
│   └── bug_results_wpr_complete.txt
├── reports/
│   ├── enhanced_report_20251210_001312.html   # Latest analysis
│   ├── bug_report_wpr_final.html             # Earlier versions
│   └── bug_report_enhanced_wpr_v2.html
└── logs/
    └── scan_phase2.log                       # 7.8MB scan log
```

## Best Practices

1. **Keep scan results**: Don't delete `.json` files - they're needed for report generation
2. **Version reports**: Enhanced reports include timestamps for tracking
3. **Clean up old versions**: Archive or delete old reports when no longer needed
4. **Share reports easily**: HTML reports are standalone (logos embedded as base64)

## Cleanup

To remove all data for a specific website:

```bash
rm -rf projects/<site-slug>
```

To clean up just reports while keeping scan data:

```bash
rm -f projects/<site-slug>/reports/*
```
