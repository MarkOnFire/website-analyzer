# Bug Finder - Complete Guide

Find visual bugs by example. No complex setup needed.

**See Also:** [Quick Start](../../QUICKSTART.md) | [Main README](../../README.md)

---

## What is Bug Finder?

Bug Finder automatically discovers pages with rendering bugs similar to one example page. Instead of manually checking pages or relying on bug reports, it:

1. **Analyzes** the example page to extract the bug pattern
2. **Generates** flexible search patterns that handle variations
3. **Crawls** your entire site (~0.7 pages/second)
4. **Finds** all pages with similar bugs
5. **Reports** results with professional HTML, CSV, JSON, and Markdown formats

**Perfect for:**
- WordPress/Drupal embed codes appearing as raw JSON
- Missing images or broken CSS
- Malformed HTML from failed migrations
- Any visual rendering inconsistency

---

## Quick Example

```bash
# 1. Find a page with the bug
# Example: https://www.example.com/broken-page

# 2. Run Bug Finder
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://www.example.com/broken-page" \
  --site "https://www.example.com" \
  --max-pages 1000

# 3. Check results
cat projects/example-com/scans/bug_results_*.txt

# 4. Generate professional report
python generate_enhanced_report_v2.py \
  projects/example-com/scans/bug_results_example-com.json

# Open: projects/example-com/reports/enhanced_report_*.html
```

---

## How It Works

### Step 1: Auto Bug Extraction

Bug Finder uses a 4-tier strategy to detect bugs in the example page:

```
Strategy 1: Double bracket patterns [[...]]
           ↓ (if not found)
Strategy 2: JSON in visible elements <p>{"fid":"...}</p>
           ↓ (if not found)
Strategy 3: Escaped HTML patterns %3C%3E...
           ↓ (if not found)
Strategy 4: Anomalous long unbroken strings in text
           ↓ (if not found)
           → Prompt user to provide bug text manually
```

**Example detections:**
- WordPress embeds: `[[{"fid":"1101026″,"view_mode":"full_width"...}}]]`
- Escaped HTML: `%3Cimg%20src%3D%22...%22%3E`
- JSON in text: `{"error":"Image failed to load"}`
- Long strings: `jkdsfjlkdsjflkjsdflkjsdfljksdflkjsdflkjsdf...`

### Step 2: Pattern Generation

Analyzes the bug and generates 6-8 flexible patterns:

```python
{
    'opening_structure': r'\[\[\s*\{',
    'opening_with_field': r'\[\[\s*\{\s*["\']fid["\']',
    'multi_field': r'["\']fid["\'][^}]{0,500}["\']view_mode["\']',
    'type_field': r'["\']type["\']\s*:\s*["\']media["\']',
    'field_fid': r'["\']fid["\']',
    'field_view_mode': r'["\']view_mode["\']',
    'complete_pattern': r'\[\[.{200,1000}?\]\]',
    'field_array': r'\[["\'].*?["\'].*?["\'].*?\]'
}
```

**Smart features:**
- Handles Unicode variations (7 types of quotes)
- Structural patterns instead of exact text
- Field presence over field values
- Non-greedy quantifiers to avoid over-matching

### Step 3: Full-Site Crawling

Intelligently crawls your entire site:

```
Homepage
   ↓
Extract all links (BeautifulSoup)
   ↓
Queue remaining URLs
   ↓
For each page:
  • Fetch with Crawl4AI
  • Extract visible text
  • Test all 8 patterns
  • Skip if already visited
  ↓
Export results (JSON, CSV, HTML, TXT)
```

**Performance:** ~0.7 pages/second
- 100 pages: ~2 minutes
- 1,000 pages: ~20-25 minutes
- 5,000 pages: ~2-3 hours

### Step 4: Pattern Matching

For each page, tests all generated patterns:

```
Page HTML
    ↓
[Test pattern 1: opening_structure] → No match
    ↓
[Test pattern 2: opening_with_field] → No match
    ↓
[Test pattern 3: multi_field] → ✓ MATCH (2 occurrences)
    ↓
[Test pattern 4: type_field] → ✓ MATCH (1 occurrence)
    ↓
Result: This page has bugs (confidence: high)
```

---

## CLI Usage

### Basic Scan

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/broken-page" \
  --site "https://example.com"
```

### Common Options

```bash
# Scan limited pages (quick validation)
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --max-pages 100

# Provide bug text manually (skip auto-extraction)
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --bug-text '[[{"fid":"1101026"...}]]'

# Export specific format
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --format html       # Options: txt, csv, html, json, all

# Custom output path
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --output custom_results.json
```

### Command Reference

```bash
python -m src.analyzer.cli bug-finder scan [OPTIONS]
```

**Required:**
- `--example-url, -e TEXT` - URL of page with the bug
- `--site, -s TEXT` - Base URL to scan

**Optional:**
- `--max-pages, -m INTEGER` - Maximum pages to scan (default: 1000)
- `--bug-text, -b TEXT` - Provide bug text directly
- `--output, -o PATH` - Custom output file path
- `--format, -f TEXT` - Export format: txt, csv, html, json, all

---

## Report Formats

### Enhanced HTML Report (Recommended)

**Best for:** Sharing with stakeholders, documentation, presentations

```bash
python generate_enhanced_report_v2.py \
  projects/example-com/scans/bug_results_example-com.json

# Output: projects/example-com/reports/enhanced_report_YYYYMMDD_HHMMSS.html
```

**Includes:**
- Professional header with site logo
- Executive summary
- Root cause analysis hypothesis
- Multiple fix options with:
  - Implementation instructions
  - Code samples (database, PHP, CSS, manual)
  - Effort estimates
  - Pros/cons for each approach
- Severity breakdown
- Complete list of affected URLs
- Timestamp and metadata

**File size:** 80-200 KB (fully self-contained, email-friendly)

### Markdown Export

```bash
# Standard markdown (complete list)
python bug_finder_export_markdown.py \
  projects/example-com/scans/bug_results_example-com.json \
  projects/example-com/reports/summary.md

# Slack-friendly (condensed)
python bug_finder_export_markdown.py \
  projects/example-com/scans/bug_results_example-com.json \
  projects/example-com/reports/slack_summary.txt \
  --slack
```

**Standard Markdown:**
- Complete list of affected pages
- Good for documentation and version control

**Slack Snippet:**
- Condensed format (~1000 chars)
- Up to 20 example URLs
- Good for team chat

### CSV Export

```bash
# Already included in multi-format export
# File: projects/example-com/scans/bug_results_example-com.csv
```

**Best for:** Analysis in spreadsheets, data processing

```csv
URL,Total Matches,Patterns Matched,Pattern Details
https://example.com/article-1,3,"multi_field, opening_with_field","multi_field (2); opening_with_field (1)"
https://example.com/article-2,2,"multi_field","multi_field (2)"
```

### JSON Export

```bash
# Already included
# File: projects/example-com/scans/bug_results_example-com.json
```

**Best for:** Programmatic access, report generation, integration

```json
{
  "metadata": {
    "scan_date": "2025-12-10 19:04:31",
    "site_scanned": "https://www.example.com",
    "example_url": "https://archive.org/web/.../bug-example",
    "total_bugs_found": 131,
    "pages_scanned": 15000,
    "scan_duration_seconds": 1842
  },
  "results": [
    {
      "url": "https://example.com/article-1",
      "total_matches": 3,
      "patterns": {
        "multi_field": 2,
        "opening_with_field": 1
      }
    }
  ]
}
```

### Plain Text Export

```bash
# Already included
# File: projects/example-com/scans/bug_results_example-com.txt
```

**Best for:** Quick reference, email summaries

```
Bug Scan Results for https://www.example.com
Example URL: https://archive.org/web/.../bug-example
Pages scanned: 15000
Bugs found: 131
========================================

https://example.com/article-1
  Matches: 3
    - multi_field: 2
    - opening_with_field: 1
```

---

## Project Organization

Results are stored in `projects/<site-slug>/`:

```
projects/
├── README.md
├── example-com/
│   ├── scans/
│   │   ├── bug_results_example-com.json      # Feed to generate_enhanced_report_v2.py
│   │   ├── bug_results_example-com.csv       # Spreadsheet format
│   │   ├── bug_results_example-com.html      # Basic table
│   │   └── bug_results_example-com.txt       # Plain text summary
│   ├── reports/
│   │   ├── enhanced_report_20251210_001312.html  # Professional report
│   │   ├── bug_summary.md                        # Markdown version
│   │   └── bug_summary_slack.txt                 # Slack format
│   ├── logs/
│   │   └── scan_phase2.log                       # Debug output
│   └── patterns/
│       └── custom_patterns.json                  # Site-specific overrides (future)
```

### File Types Summary

**In `scans/` directory:**
- `.json` - Full bug details (use as input to `generate_enhanced_report_v2.py`)
- `.csv` - For data analysis in spreadsheets
- `.txt` - Quick reference summary
- `.html` - Basic sortable table (not the enhanced report)

**In `reports/` directory:**
- `enhanced_report_*.html` - Professional report (recommended for sharing)
- `.md` files - Markdown for documentation
- `*_slack.txt` - Condensed format for chat

**In `logs/` directory:**
- `scan_phase*.log` - Progress output and debug info

---

## Real-World Case Study: WPR.org

### The Problem

Wisconsin Public Radio (WPR.org) had **131 pages** with unrendered WordPress embed codes:

```
Instead of: [image of Tom and Jerry]
Users saw: [[{"fid":"1101026″,"view_mode":"full_width"...}}]]
```

Root cause: Failed Drupal-to-WordPress migration left codes in the HTML but not rendering.

### The Solution

```bash
# 1. Identify example page
https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail

# 2. Run Bug Finder
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail" \
  --site "https://www.wpr.org" \
  --max-pages 15000

# 3. Generate report
python generate_enhanced_report_v2.py \
  projects/wpr-org/scans/bug_results_wpr_complete.json
```

### Results

- **Scan Time**: 35 minutes (15,000 pages)
- **Bugs Found**: 131 pages
- **Report Generated**: 192 KB (fully self-contained)
- **Fix Options**: 3 approaches with effort estimates

**Report Content:**
1. Root cause hypothesis: Content migration issue
2. Fix options:
   - Database migration (2-4 hours) - Permanent
   - PHP filter hook (1-2 hours) **[RECOMMENDED]** - Safe, reversible
   - Manual editing (5-10 hours) - Full control, not scalable
3. Severity: Critical
4. Priority: High (131 pages is significant)

---

## Advanced Usage

### Using Archive.org Pages

```bash
# Use a snapshot from archive.org as the example
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250101000000/https://www.example.com/page" \
  --site "https://www.example.com"
```

### Configuration Files

```bash
# Use defaults from config file
python -m src.analyzer.cli bug-finder scan \
  --config config.json \
  --example-url "https://example.com/bug" \
  --site "https://example.com"
```

See [CONFIG.md](../../CONFIG.md) for configuration file documentation.

### Providing Bug Text Directly

When auto-extraction fails, provide the exact bug text:

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/page" \
  --site "https://example.com" \
  --bug-text 'YOUR_BUG_TEXT_HERE'
```

This skips auto-detection and uses your exact text as the first pattern.

### Quick Validation Scan

For large sites, start with a quick test:

```bash
# Scan first 50-100 pages to verify the pattern
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --max-pages 50

# Review results
cat projects/example-com/scans/bug_results_*.txt

# If satisfied, run full scan
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --max-pages 5000
```

---

## Troubleshooting

### "Could not automatically detect bug pattern"

**Issue:** Auto-extraction failed - no bug detected in the example page

**Solutions:**
1. Verify the URL actually contains the bug (manually visit it)
2. Check if the bug only appears under certain conditions (logged in, specific viewport)
3. Provide bug text manually:
   ```bash
   python -m src.analyzer.cli bug-finder scan \
     --example-url "https://example.com/page" \
     --site "https://example.com" \
     --bug-text 'YOUR_BUG_TEXT_HERE'
   ```

### Scan is very slow (< 0.7 pages/sec)

**Solutions:**
1. Limit to quick validation:
   ```bash
   --max-pages 100
   ```
2. Check internet connection
3. Check if site is rate-limiting requests
4. Run during off-peak hours

### Report generation fails

**Errors & fixes:**

```bash
# FileNotFoundError: JSON file not found
# Fix: Verify exact path
ls -la projects/*/scans/*.json

# JSONDecodeError: Invalid JSON
# Fix: Ensure scan completed successfully
tail -50 projects/site-slug/scans/bug_results*.txt

# Logo fetch fails (non-fatal warning)
# Fix: Report still generates, just won't have logo
```

### No bugs found (but you expected some)

**Checklist:**
1. Bug was already fixed (manually verify)
2. Bug only on pages not yet crawled (increase `--max-pages`)
3. Auto-extraction grabbed wrong text (use `--bug-text` with exact pattern)
4. Site structure prevents crawling (check logs)

**Manual verification:**
```bash
# Check the example page manually
curl "https://example.com/page" | grep "bug_text_here"

# Check scan logs
tail projects/site-slug/logs/scan_phase2.log
```

---

## Performance & Scalability

### Crawl Speed

| Pages | Time | Rate |
|-------|------|------|
| 100 | ~2 min | 0.7 p/s |
| 1,000 | ~20-25 min | 0.7 p/s |
| 5,000 | ~2 hours | 0.7 p/s |
| 15,000 | ~5-7 hours | 0.7 p/s |

### Memory Usage

- Pattern generator: <1 MB
- Scanner (per 1000 URLs): ~100 KB
- Total for 5000-page scan: <50 MB

### Accuracy

- Pattern generation: 75% match rate, 100% bug detection
- Auto-extraction success: 100% on WordPress bugs
- False positive rate: 0 in testing (all matches verified)

---

## FAQ

**Q: How long does a scan take?**
A: ~0.7 pages/second. A 1000-page site takes ~20-25 minutes.

**Q: Can it handle large sites (10,000+ pages)?**
A: Yes, but start with 1000 pages for validation, then do full scans overnight.

**Q: Do I need the exact bug text?**
A: No! Auto-extraction works from example page. Use `--bug-text` if it fails.

**Q: Can it find variations of the same bug?**
A: Yes! Generates 6-8 flexible patterns that handle Unicode and variations.

**Q: Is the HTML report mobile-friendly?**
A: Yes, fully responsive with embedded styles.

**Q: Can I use archived pages?**
A: Yes! archive.org URLs work as example URLs.

**Q: What if my site requires authentication?**
A: Current version doesn't support auth. Open an issue if needed.

**Q: How do I choose which fix option to implement?**
A: The report recommends an option based on risk/effort/impact. PHP filter hooks are usually safest for CMS bugs.

---

## See Also

- [Quick Start Guide](../../QUICKSTART.md)
- [Main README](../../README.md)
- [Migration Scanner Guide](MIGRATION_SCANNER.md)
- [Configuration Guide](../reference/CONFIG.md)
- [Architecture Reference](../reference/ARCHITECTURE.md)
