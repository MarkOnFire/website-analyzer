# Bug Finder CLI - Usability Improvements Guide

This guide documents the professional usability enhancements added to the Bug Finder CLI for a polished, user-friendly experience.

## Table of Contents

1. [New Commands](#new-commands)
2. [Enhanced Error Handling](#enhanced-error-handling)
3. [Shell Completion](#shell-completion)
4. [Dry-Run Mode](#dry-run-mode)
5. [Scan Management](#scan-management)
6. [Environment Checking](#environment-checking)
7. [Example Workflows](#example-workflows)

---

## New Commands

### 1. `bug-finder list-scans`

List all recent scans and their status with a formatted table.

**Purpose**: Never lose track of your scans. See scan history, identify which scans completed successfully, and find scan IDs for resuming or comparing.

**Usage**:
```bash
# List the 20 most recent scans
python -m src.analyzer.cli bug-finder list-scans

# Show only the last 10 scans
python -m src.analyzer.cli bug-finder list-scans --limit 10

# Filter by status
python -m src.analyzer.cli bug-finder list-scans --status completed
python -m src.analyzer.cli bug-finder list-scans --status error
```

**Output Example**:
```
Recent Bug Finder Scans (5)

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Scan ID           ┃ Site     ┃ Pages ┃ Status  ┃ Started ┃Duration┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ scan_20251211_... │ wpr.org  │ 1000  │ COMPLE… │ 2025-12 │ 3456s  │
│ scan_20251210_... │ npr.org  │ 500   │ ERROR   │ 2025-12 │ 892s   │
│ scan_20251209_... │ bbc.com  │ 2000  │ COMPLE… │ 2025-12 │ 7234s  │
└───────────────────┴──────────┴───────┴─────────┴─────────┴────────┘

Tips:
  - Use scan ID with: bug-finder scan --resume <scan_id>
  - Compare scans with: bug-finder compare --scan1 <id1> --scan2 <id2>
  - Filter by status: --status completed
```

**Status Values**:
- `running`: Scan currently in progress
- `completed`: Scan finished, bugs found
- `completed_clean`: Scan finished, no bugs found
- `error`: Scan encountered an error

---

### 2. `bug-finder doctor`

Check your environment setup and verify all dependencies are installed.

**Purpose**: Ensure your system is properly configured for Bug Finder. Run this if you're having issues or after updating.

**Usage**:
```bash
python -m src.analyzer.cli bug-finder doctor
```

**Output Example**:
```
Bug Finder Environment Check

┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status ┃ Details        ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Python Version │ OK     │ v3.11.2        │
│ crawl4ai       │ OK     │ v0.3.1         │
│ typer          │ OK     │ v0.9.1         │
│ rich           │ OK     │ v13.7.0        │
│ beautifulsoup4 │ OK     │ installed      │
│ requests       │ OK     │ installed      │
│ Playwright     │ OK     │ Chromium ready │
└────────────────┴────────┴────────────────┘

All systems ready!

You can start using Bug Finder:
  python -m src.analyzer.cli bug-finder scan \
    --example-url <url> \
    --site <website>
```

**Checks Performed**:
- Python version (3.11+ required)
- All required Python packages
- Playwright/Chromium availability
- File permissions

---

### 3. `bug-finder compare`

Compare results between two scans to see what changed.

**Purpose**: Track bug fix progress over time. See new bugs introduced, bugs that were fixed, and unchanged issues.

**Usage**:
```bash
# Compare the two most recent scans
python -m src.analyzer.cli bug-finder compare

# Compare specific scans by ID
python -m src.analyzer.cli bug-finder compare \
  --scan1 scan_20251210_120000_1234 \
  --scan2 scan_20251211_150000_5678

# Compare scan results from files
python -m src.analyzer.cli bug-finder compare \
  --file1 projects/site/scans/bug_results_site.json \
  --file2 projects/site/scans/bug_results_site_2.json
```

**Output Example**:
```
Scan Comparison Report

Scan 1 (older):
  Date: 2025-12-10 12:00:00
  Site: https://www.example.com
  Results: 15 pages with bugs

Scan 2 (newer):
  Date: 2025-12-11 15:00:00
  Site: https://www.example.com
  Results: 8 pages with bugs

┏━━━━━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Category ┃ Count ┃ Change┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━━┩
│ New bugs │ 2    │ +2    │
│ Fixed    │ 9    │ -9    │
│ Unchanged│ 6    │ =6    │
└──────────┴──────┴───────┘

New Bugs Found:
  1. https://example.com/new-article-123
  2. https://example.com/news/breaking-story

Bugs Fixed:
  1. https://example.com/old-broken-page
  ... and 8 more
```

---

## Enhanced Error Handling

Error messages now include helpful suggestions for common issues.

**Examples**:

### URL Not Found
```
Error: Could not fetch page: Connection refused

Suggestions:
The URL might be inaccessible. Try:
  - Check the URL is correct and public
  - Use web.archive.org for historical pages
  - Try --dry-run to preview without fetching
```

### Timeout Issues
```
Error: Request timed out after 30 seconds

Suggestions:
The page took too long to load. Try:
  - Reduce --max-pages to test with fewer pages
  - Use --dry-run to check if settings are valid
  - Check your internet connection
```

### Pattern Errors
```
Error: Invalid regex pattern in bug text

Suggestions:
Pattern error in your bug text. Try:
  - Check for special regex characters (. * + ? [ ])
  - Use simpler text patterns
  - Test with: bug-finder patterns test
```

---

## Dry-Run Mode

Preview what a scan would do without actually running it.

**Purpose**: Validate your settings, check URLs are accessible, and plan your scan before committing time and resources.

**Usage**:
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/broken-page" \
  --site "https://example.com" \
  --max-pages 1000 \
  --dry-run
```

**Output Example**:
```
DRY RUN - Preview Mode

Scan Configuration:
  Example URL: https://example.com/broken-page
  Site to scan: https://example.com
  Max pages: 1000
  Output format: txt
  Incremental: No

What will happen when you run without --dry-run:
  1. Fetch content from example URL
  2. Analyze and extract bug pattern
  3. Generate search patterns
  4. Scan up to 1000 pages from https://example.com
  5. Report all pages containing similar bugs

Settings look valid!
To run the actual scan, remove --dry-run
```

**Benefits**:
- Validate configuration before long scans
- Check URL accessibility
- No resources consumed (no crawling, no processing)
- Fast feedback on settings

---

## Scan Management

### Automatic Scan ID Generation

Every scan automatically gets a unique ID for tracking and resuming:

```
scan_20251211_120000_1234
├─ Date: 2025-12-11
├─ Time: 12:00:00
└─ Unique suffix: 1234
```

### Scan Registry

Scans are recorded in `~/.bug-finder/scans.json`:

```json
{
  "scans": [
    {
      "id": "scan_20251211_120000_1234",
      "site_url": "https://www.example.com",
      "example_url": "https://web.archive.org/web/.../page",
      "max_pages": 1000,
      "status": "completed",
      "output_file": "projects/example-com/scans/bug_results_example-com",
      "started_at": "2025-12-11T12:00:00.000000",
      "completed_at": "2025-12-11T12:45:30.000000"
    }
  ]
}
```

### Resume Interrupted Scans

Resume a scan that was interrupted:

```bash
# The --resume flag is planned for future versions
# For now, use the original command with same parameters
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/broken" \
  --site "https://example.com" \
  --max-pages 1000 \
  --incremental  # Use incremental mode for resumability
```

---

## Environment Checking

### Doctor Command Benefits

```bash
python -m src.analyzer.cli bug-finder doctor
```

Automatically:
1. Checks Python version
2. Verifies all dependencies installed
3. Tests Playwright/Chromium
4. Reports detailed installation instructions for missing components
5. Suggests next steps

### Installation Helpers

Doctor provides one-line installation commands:

```
Missing Components:
  - crawl4ai: pip install crawl4ai
  - Playwright: pip install playwright && python -m playwright install chromium
```

---

## Shell Completion

### Installation

Install shell completion for bash or zsh:

```bash
# Install both bash and zsh completion
bash scripts/install_completion.sh

# Install only bash
bash scripts/install_completion.sh --shell bash

# Install only zsh
bash scripts/install_completion.sh --shell zsh
```

### Bash Completion

Once installed, press TAB to complete:

```bash
$ bug-finder scan --[TAB]
--example-url  --site  --max-pages  --bug-text  --output  --format  --dry-run  ...

$ bug-finder scan --format [TAB]
txt  csv  html  json  all

$ bug-finder scan --site [TAB]
(shell file completion)
```

### Zsh Completion

Zsh provides more intelligent completion:

```bash
$ bug-finder scan --[TAB]
scan options:
  --example-url  [URL of a page showing the bug]
  --site         [Base URL of site to scan]
  --max-pages    [Maximum number of pages to scan]
  --format       [Output format: txt, csv, html, json, all]
  --dry-run      [Preview what scan would do]
  ...

$ bug-finder compare --scan1 [TAB]
scan_001  scan_002  scan_003
```

---

## Example Workflows

### Workflow 1: Quick Test with Dry Run

Before running a long scan, validate your settings:

```bash
# Test with dry-run to validate configuration
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/example.com/page" \
  --site "https://example.com" \
  --max-pages 100 \
  --dry-run

# Once validated, run the actual scan
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/example.com/page" \
  --site "https://example.com" \
  --max-pages 100
```

### Workflow 2: Check Environment After Update

After updating Bug Finder:

```bash
# Verify everything is working
python -m src.analyzer.cli bug-finder doctor

# Install shell completion
bash scripts/install_completion.sh
```

### Workflow 3: Track Bug Progress Over Time

Run scans periodically and compare results:

```bash
# First scan (baseline)
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../broken" \
  --site "https://mysite.com" \
  --max-pages 1000

# Later, check if bugs are fixed
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../broken" \
  --site "https://mysite.com" \
  --max-pages 1000

# Compare the two scans
python -m src.analyzer.cli bug-finder list-scans
python -m src.analyzer.cli bug-finder compare
```

### Workflow 4: Share Results Across Team

```bash
# Run scan with all output formats
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../broken" \
  --site "https://mysite.com" \
  --format all

# Export to Slack-friendly format
python -m src.analyzer.cli bug-finder export \
  --input projects/mysite-com/scans/bug_results_mysite-com.json \
  --format slack

# Share with team
cat projects/mysite-com/scans/bug_results_mysite-com_slack.txt
```

### Workflow 5: Handle Errors Gracefully

When things go wrong:

```bash
# Run scan
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://broken-url.example.com" \
  --site "https://mysite.com"

# If it fails, CLI provides suggestions
# Error: Could not fetch page
# Suggestions:
# - Check the URL is correct and public
# - Use web.archive.org for historical pages
# - Try --dry-run to preview without fetching

# Check environment
python -m src.analyzer.cli bug-finder doctor

# Fix issues based on recommendations
```

---

## Help System

All commands include comprehensive help:

```bash
# Show main help
python -m src.analyzer.cli bug-finder --help

# Show command-specific help
python -m src.analyzer.cli bug-finder scan --help
python -m src.analyzer.cli bug-finder list-scans --help
python -m src.analyzer.cli bug-finder doctor --help
python -m src.analyzer.cli bug-finder compare --help
```

---

## Configuration Tips

### For Frequent Users

1. Create an alias:
```bash
alias bf='python -m src.analyzer.cli bug-finder'

# Then use:
bf scan --example-url <url> --site <site>
bf list-scans
bf doctor
```

2. Use config files:
```bash
# Generate example config
python -m src.analyzer.cli bug-finder config-example --output my-config.json

# Edit my-config.json with your defaults

# Use config in scans
python -m src.analyzer.cli bug-finder scan --config my-config.json --site <site>
```

3. Enable shell completion:
```bash
bash scripts/install_completion.sh
```

### For CI/CD Integration

Use flags for scripting:

```bash
# Non-interactive, minimal output
python -m src.analyzer.cli bug-finder scan \
  --example-url "$EXAMPLE_URL" \
  --site "$SITE_URL" \
  --max-pages 500 \
  --format json \
  --quiet

# Check environment before running
python -m src.analyzer.cli bug-finder doctor || exit 1

# Run scan
python -m src.analyzer.cli bug-finder scan ...
```

---

## Summary of Improvements

| Feature | Benefit | Usage |
|---------|---------|-------|
| `list-scans` | Never lose scan history | `bug-finder list-scans` |
| `doctor` | Fix setup issues | `bug-finder doctor` |
| `compare` | Track progress | `bug-finder compare` |
| Dry-run | Validate before running | `--dry-run` |
| Smart errors | Get helpful suggestions | Automatic on errors |
| Shell completion | Faster typing | `bash scripts/install_completion.sh` |
| Scan registry | Resume and track | Automatic, stored in `~/.bug-finder/` |

---

## Feedback & Support

These improvements make Bug Finder more professional and user-friendly. If you have suggestions or encounter issues:

1. Check environment: `bug-finder doctor`
2. Look for suggestions in error messages
3. Review this guide for specific workflows
4. Use `--help` for detailed command documentation

Happy scanning!
