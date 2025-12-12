# Full Site Scanning Guide

## Recent Updates

**Pattern Improvements (Dec 2025)**: Scanner now handles Unicode quote variations (", ', ″, ‴, ", ", ', ') that appear in WordPress embed bugs. Previous scans may have missed bugs due to special character encoding.

## Quick Start

```bash
# Activate environment
source .venv/bin/activate

# Run comprehensive scan (default: 5000 pages)
python full_site_scanner.py

# For a REALLY thorough scan, edit the script first:
# Change MAX_PAGES = 5000 to MAX_PAGES = 10000 (or more)
```

## Configuration Options

Edit these lines in `full_site_scanner.py`:

```python
START_URL = "https://www.wpr.org"  # Change to any website
MAX_PAGES = 1000                    # Increase for deeper scans
```

### Recommended Settings

**Quick Test** (5-10 minutes)
```python
MAX_PAGES = 100
```

**Standard Scan** (15-30 minutes)
```python
MAX_PAGES = 1000
```

**Deep Scan** (1-2 hours)
```python
MAX_PAGES = 5000
```

**Complete Site** (2-6 hours depending on site size)
```python
MAX_PAGES = 10000  # Or remove the limit entirely
```

## How It Works

1. **Starts at homepage**: Begins crawling from START_URL
2. **Discovers links**: Extracts ALL links from each page using BeautifulSoup
3. **Breadth-first crawl**: Systematically visits every page on the site
4. **Tests each page**: Checks every page against your bug patterns
5. **Saves results**: Creates JSON report + simple URL list

## Output Files

After scan completes:

- `bug_scan_results_YYYYMMDD_HHMMSS.json` - Detailed results with pattern matches
- `affected_urls.txt` - Simple list of URLs with bugs
- `failed_urls.txt` - Any pages that couldn't be scanned (if any)

## Customizing Bug Patterns

To search for different bugs, edit the `PATTERNS` dict:

```python
PATTERNS = {
    "your-bug-name": r'your-regex-pattern-here',
    "another-pattern": r'another-regex',
}
```

### Example Patterns

**WordPress Embed Bug** (current):
```python
"wordpress-fid": r'\[\[{"fid":"[0-9]+"'
```

**Broken image tags**:
```python
"broken-img": r'<img[^>]*src=""'
```

**Exposed email addresses**:
```python
"email-leak": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

**Old jQuery patterns**:
```python
"jquery-live": r'\$\([^)]+\)\.live\('
```

## Performance Tips

1. **Start small**: Test with MAX_PAGES=100 first
2. **Run overnight**: Large scans (5000+ pages) can take hours
3. **Check progress**: Look for "📊 Progress" updates every 50 pages
4. **Save & resume**: Currently scans from scratch each time (resumable scanning = future feature)

## Interpreting Results

### If bugs are found:
```
✅ Detailed results saved to: bug_scan_results_20251205_123456.json
```

Open the JSON file to see:
- Exact URLs with bugs
- Number of matches per page
- Sample context showing the bug
- Which patterns matched

### If no bugs found:
```
✅ No bugs found across the scanned pages.
```

This means either:
- Bug doesn't exist (or was fixed)
- Bug is on pages deeper than MAX_PAGES
- Try increasing MAX_PAGES or different patterns

## Troubleshooting

**"Too slow"**
- Scans ~1-3 pages/second depending on site
- This is normal for thorough scanning
- Run overnight for 5000+ page sites

**"Many failed URLs"**
- Check `failed_urls.txt` for details
- Usually timeout or connection errors
- These pages were skipped, scan continues

**"Memory usage high"**
- Normal for large scans (tracks all visited URLs)
- For 10,000+ page sites, consider multiple smaller scans

## Advanced: Multiple Pattern Sets

Create different scanners for different bug types:

```bash
# Scan for WordPress bugs
python full_site_scanner.py  # (default patterns)

# Edit patterns in script, then scan for email leaks
python full_site_scanner.py  # (with email patterns)
```

## Integration with Main Tool

This standalone scanner will be integrated into the main CLI tool once we:
1. Fix the recursive crawler bug
2. Add the issue tracking system

For now, use this script for immediate comprehensive scanning needs.
