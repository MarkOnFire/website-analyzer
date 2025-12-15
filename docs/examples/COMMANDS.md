# Bug Finder CLI - Example Commands & Expected Output

This document shows real-world examples of using the new usability features.

---

## 1. Environment Check: `bug-finder doctor`

### Command
```bash
python -m src.analyzer.cli bug-finder doctor
```

### Expected Output
```
Bug Finder Environment Check

┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status ┃ Details        ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Python Version │ OK     │ v3.11.7        │
│ crawl4ai       │ OK     │ v0.3.1         │
│ typer          │ OK     │ v0.12.0        │
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

### If Missing Dependencies
```
Bug Finder Environment Check

┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status  ┃ Details                ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python Version │ OK      │ v3.11.7                │
│ crawl4ai       │ MISSING │ Install with: pip ...  │
│ typer          │ OK      │ v0.12.0                │
└────────────────┴─────────┴────────────────────────┘

Some components need attention

Follow the instructions above to install missing dependencies.

Common fix:
  pip install crawl4ai
  python -m playwright install chromium
```

---

## 2. List Scans: `bug-finder list-scans`

### Command
```bash
python -m src.analyzer.cli bug-finder list-scans
```

### Expected Output (First Time)
```
No scans found. Start your first scan with:

  python -m src.analyzer.cli bug-finder scan \
    --example-url <archived_page> \
    --site <your_website>
```

### Expected Output (With Scans)
```
Recent Bug Finder Scans (8)

┌─────────────────────────┬──────────┬────────┬──────────────┬────────────┬──────────┐
│ Scan ID                 │ Site     │ Pages  │ Status       │ Started    │ Duration │
├─────────────────────────┼──────────┼────────┼──────────────┼────────────┼──────────┤
│ scan_20251211_150000... │ npr.org  │ 1000   │ COMPLETED    │ 2025-12-11 │ 3456s    │
│ scan_20251211_120000... │ bbc.com  │ 500    │ COMPLETED    │ 2025-12-11 │ 1234s    │
│ scan_20251210_180000... │ wpr.org  │ 2000   │ COMPLETED    │ 2025-12-10 │ 7234s    │
│ scan_20251210_100000... │ npr.org  │ 1000   │ ERROR        │ 2025-12-10 │ 892s     │
│ scan_20251209_150000... │ bbc.com  │ 1500   │ COMPLETED    │ 2025-12-09 │ 5123s    │
│ scan_20251209_120000... │ wpr.org  │ 1000   │ COMPLETED    │ 2025-12-09 │ 3456s    │
│ scan_20251208_190000... │ npr.org  │ 2000   │ COMPLETED    │ 2025-12-08 │ 8901s    │
│ scan_20251207_110000... │ example  │ 100    │ COMPLETED_C… │ 2025-12-07 │ 432s     │
└─────────────────────────┴──────────┴────────┴──────────────┴────────────┴──────────┘

Tips:
  - Use scan ID with: bug-finder scan --resume <scan_id>
  - Compare scans with: bug-finder compare --scan1 <id1> --scan2 <id2>
  - Filter by status: --status completed
```

### Filter by Status
```bash
python -m src.analyzer.cli bug-finder list-scans --status error
```

```
Recent Bug Finder Scans (1)

┌─────────────────────────┬──────────┬────────┬────────┬────────────┬──────────┐
│ Scan ID                 │ Site     │ Pages  │ Status │ Started    │ Duration │
├─────────────────────────┼──────────┼────────┼────────┼────────────┼──────────┤
│ scan_20251210_100000... │ npr.org  │ 1000   │ ERROR  │ 2025-12-10 │ 892s     │
└─────────────────────────┴──────────┴────────┴────────┴────────────┴──────────┘
```

---

## 3. Dry-Run: Preview Before Scanning

### Command
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/wpr.org/article" \
  --site "https://www.wpr.org" \
  --max-pages 1000 \
  --dry-run
```

### Expected Output
```
DRY RUN - Preview Mode

Scan Configuration:
  Example URL: https://web.archive.org/web/20250701/wpr.org/article
  Site to scan: https://www.wpr.org
  Max pages: 1000
  Output format: txt
  Incremental: No

What will happen when you run without --dry-run:
  1. Fetch content from example URL
  2. Analyze and extract bug pattern
  3. Generate search patterns
  4. Scan up to 1000 pages from https://www.wpr.org
  5. Report all pages containing similar bugs

Settings look valid!
To run the actual scan, remove --dry-run
```

---

## 4. Compare Scans: Track Progress

### Command (Auto-compare Recent Scans)
```bash
python -m src.analyzer.cli bug-finder compare
```

### Expected Output
```
Scan Comparison Report

Scan 1 (older):
  Date: 2025-12-10 12:00:00
  Site: https://www.npr.org
  Results: 15 pages with bugs

Scan 2 (newer):
  Date: 2025-12-11 15:00:00
  Site: https://www.npr.org
  Results: 8 pages with bugs

┌──────────────┬───────┬────────┐
│ Category     │ Count │ Change │
├──────────────┼───────┼────────┤
│ New bugs     │ 2     │ +2     │
│ Fixed bugs   │ 9     │ -9     │
│ Unchanged    │ 6     │ =6     │
└──────────────┴───────┴────────┘

New Bugs Found:
  1. https://www.npr.org/2025/12/11/new-article-with-bug
  2. https://www.npr.org/sections/culture/breaking-story

Bugs Fixed:
  1. https://www.npr.org/2025/11/old-article-fixed
  2. https://www.npr.org/sections/news/previous-issue-fixed
  ... and 7 more
```

### Command (Compare Specific Scans)
```bash
python -m src.analyzer.cli bug-finder compare \
  --scan1 scan_20251210_120000_1234 \
  --scan2 scan_20251211_150000_5678
```

```
[Same output as above, comparing specific scans]
```

---

## 5. Smart Error Messages

### Example 1: Invalid URL

#### Command
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://definitely-not-a-real-website-xyz.fake" \
  --site "https://example.com"
```

#### Output
```
Error: Could not fetch page: HTTP 404 - Not Found

Suggestions:
The URL might be inaccessible. Try:
  - Check the URL is correct and public
  - Use web.archive.org for historical pages
  - Try --dry-run to preview without fetching
```

### Example 2: Missing Required Arguments

#### Command
```bash
python -m src.analyzer.cli bug-finder scan --site "https://example.com"
```

#### Output
```
Error: --example-url is required

You need to provide a URL showing the bug.
  - Use --example-url with a page that shows the bug
  - Archive pages work great: web.archive.org/web/...
```

### Example 3: Timeout

#### Command
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://slow-server.example.com/page" \
  --site "https://example.com" \
  --max-pages 10000
```

#### Output
```
Error: Request timed out after 30 seconds on: https://slow-server.example.com/page

Suggestions:
The page took too long to load. Try:
  - Reduce --max-pages to test with fewer pages
  - Use --dry-run to check if settings are valid
  - Check your internet connection
```

---

## 6. Shell Completion

### Bash Completion

After running `bash scripts/install_completion.sh`:

```bash
# Complete commands
$ bug-finder [TAB]
scan        list-scans  doctor      compare     export      patterns    config-example

# Complete options
$ bug-finder scan --[TAB]
--example-url     --site            --max-pages       --bug-text
--output          --format          --config          --incremental
--pattern-file    --load-all        --quiet           --verbose
--dry-run         --help

# Complete values
$ bug-finder scan --format [TAB]
txt   csv   html  json  all

# Complete status values
$ bug-finder list-scans --status [TAB]
running          completed        completed_clean  error
```

### Zsh Completion

```bash
$ bug-finder scan --[TAB]
scan options:
  --example-url              [URL of a page showing the bug]
  --site                     [Base URL of site to scan]
  --max-pages                [Maximum number of pages to scan]
  --bug-text                 [Provide bug text directly]
  --output                   [Output file path]
  --format                   [Output format]
  --config                   [Configuration file]
  --incremental              [Enable incremental output]
  --pattern-file             [Load custom pattern]
  --load-all-patterns        [Load all available patterns]
  --quiet                    [Minimal output]
  --verbose                  [Detailed debug output]
  --dry-run                  [Preview without running]
  --help                     [Show help]
```

---

## 7. Real-World Workflow

### Step 1: Check Environment
```bash
$ python -m src.analyzer.cli bug-finder doctor
All systems ready!
```

### Step 2: Preview Scan
```bash
$ python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/wpr.org/article" \
  --site "https://www.wpr.org" \
  --max-pages 500 \
  --dry-run

DRY RUN - Preview Mode
Settings look valid!
To run the actual scan, remove --dry-run
```

### Step 3: Run Actual Scan
```bash
$ python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/wpr.org/article" \
  --site "https://www.wpr.org" \
  --max-pages 500

Scan ID: scan_20251211_140000_1234
Bug Finder - Visual Bug Scanner
...
Found 8 pages with bugs!

Top 10 affected pages:
  1. https://www.wpr.org/article-123
  2. https://www.wpr.org/news/story-456
  ...

Results saved in all formats:
  - projects/wpr-org/scans/bug_results_wpr-org.txt
  - projects/wpr-org/scans/bug_results_wpr-org.csv
  - projects/wpr-org/scans/bug_results_wpr-org.html
  - projects/wpr-org/scans/bug_results_wpr-org.json

Next steps:
  1. Review results: projects/wpr-org/scans/bug_results_wpr-org.txt
  2. Compare with another scan: bug-finder compare
  3. Resume if needed: bug-finder scan --resume scan_20251211_140000_1234
```

### Step 4: View Scan History
```bash
$ python -m src.analyzer.cli bug-finder list-scans

Recent Bug Finder Scans (3)
[Table showing three scans with the new one at top]

Tips:
  - Use scan ID with: bug-finder scan --resume <scan_id>
  - Compare scans with: bug-finder compare --scan1 <id1> --scan2 <id2>
  - Filter by status: --status completed
```

### Step 5: Compare Results (Next Day)
```bash
$ python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250701/wpr.org/article" \
  --site "https://www.wpr.org" \
  --max-pages 500

[Scan completes...]

$ python -m src.analyzer.cli bug-finder compare

Scan Comparison Report

Scan 1 (older):
  Date: 2025-12-11 14:00:00
  Results: 8 pages with bugs

Scan 2 (newer):
  Date: 2025-12-12 15:00:00
  Results: 5 pages with bugs

┌──────────────┬───────┬────────┐
│ Category     │ Count │ Change │
├──────────────┼───────┼────────┤
│ New bugs     │ 0     │ +0     │
│ Fixed bugs   │ 3     │ -3     │
│ Unchanged    │ 5     │ =5     │
└──────────────┴───────┴────────┘

Bugs Fixed:
  1. https://www.wpr.org/article-789
  2. https://www.wpr.org/news/story-456
  3. https://www.wpr.org/section/article-999
```

---

## Summary

These examples show how the new features:
1. **doctor**: Ensures your system is ready
2. **list-scans**: Tracks all your scans
3. **compare**: Measures progress
4. **dry-run**: Tests before committing
5. **Smart errors**: Helps troubleshoot
6. **Completion**: Makes typing easier

Together, they create a professional, user-friendly CLI experience.
