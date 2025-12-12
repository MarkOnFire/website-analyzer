# Migration Scanner - Complete Guide

Find deprecated code patterns, outdated APIs, and migration candidates across entire websites.

**See Also:** [Quick Start](../../QUICKSTART.md) | [Main README](../../README.md)

---

## What is Migration Scanner?

Migration Scanner is a regex-based pattern matching tool that:

1. **Finds deprecated patterns** across your entire website snapshot
2. **Provides context** around each match (10 lines before/after)
3. **Tracks line numbers** for precise location reporting
4. **Offers suggestions** for modern replacements
5. **Supports custom patterns** for unlimited use cases

**Perfect for:**
- jQuery .live() → .on() migrations
- Flash → HTML5 conversions
- HTTP → HTTPS upgrades
- Deprecated CMS APIs and hooks
- Security vulnerability scanning

---

## Quick Example

```bash
# 1. Create a project
python -m src.analyzer.cli project new "https://www.example.com"

# 2. Crawl the website
python -m src.analyzer.cli crawl start example-com --max-pages 100

# 3. Scan for deprecated jQuery patterns
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_live":"\\.live\\s*\\("
    }
  }'

# 4. Check results
cat projects/example-com/test-results/results_*.json | jq '.details.findings'
```

---

## How It Works

### Step 1: Create a Project

```bash
python -m src.analyzer.cli project new "https://www.example.com"
```

Creates a workspace in `projects/example-com/` with:
- Snapshot storage
- Test results directory
- Issues tracking
- Project metadata

### Step 2: Crawl the Site

```bash
python -m src.analyzer.cli crawl start example-com --max-pages 500
```

**Creates a persistent snapshot** (can be reused for multiple tests):
- Full HTML of each page
- Cleaned text version
- Markdown conversion
- Sitemap data

```
projects/example-com/snapshots/2025-12-10T14-30-45.123456Z/
├── pages/example-com/
│   ├── raw.html
│   ├── cleaned.html
│   └── content.md
├── sitemap.json
└── summary.json
```

### Step 3: Run Migration Scanner

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "pattern_name":"regex_pattern"
    }
  }'
```

**Scans entire snapshot** and:
- Applies all patterns to every page
- Tracks line numbers and character offsets
- Extracts 10 lines of context
- Generates suggestions
- Saves detailed results

### Step 4: Review Results

```bash
# View summary
cat projects/example-com/test-results/results_*.json | jq '.summary'

# View findings with context
cat projects/example-com/test-results/results_*.json | jq '.details.findings[0]'

# Extract just affected URLs
cat projects/example-com/test-results/results_*.json | jq '.details.findings[].url'
```

---

## CLI Usage

### Basic Pattern Scan

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"pattern_name":"regex_pattern"}}'
```

### Multiple Patterns

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_live":"\\.live\\s*\\(",
      "jquery_bind":"\\.bind\\s*\\(",
      "jquery_unbind":"\\.unbind\\s*\\("
    },
    "case_sensitive":false
  }'
```

### Case-Sensitive Matching

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{"document_write":"document\\.write\\s*\\("},
    "case_sensitive":true
  }'
```

### Specific Snapshot

```bash
# List available snapshots
python -m src.analyzer.cli project snapshots example-com

# Run test on specific snapshot
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --snapshot "2025-12-10T14-30-45.123456Z" \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'
```

### Advanced Options

```bash
# Use different timeout (default: 300 seconds)
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --timeout 600 \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'

# Don't save results (quick preview)
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --no-save \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'

# Run multiple tests at once
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --test link-checker \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'
```

### Command Reference

```bash
python -m src.analyzer.cli test run <slug> [OPTIONS]
```

**Required Arguments:**
- `<slug>` - Project slug (e.g., `example-com`)

**Required Options (for migration-scanner):**
- `--config, -c` (TEXT) - Configuration as JSON string
  - Format: `'migration-scanner:{"patterns":{"name":"regex"},"case_sensitive":false}'`

**Optional Arguments:**
- `--test, -t` (TEXT) - Specific test plugin to run
  - Can be repeated: `-t migration-scanner -t link-checker`
  - Default: Run all plugins if not specified

**Optional Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--snapshot, -s` (TEXT) | Latest | Specific snapshot timestamp to use |
| `--save / --no-save` | `--save` | Whether to save results to disk |
| `--timeout` (INT) | 300 | Maximum execution time per plugin (seconds) |

---

## Available Patterns

### jQuery Deprecations

| Pattern Name | Regex | Detects | Replacement |
|---|---|---|---|
| `jquery_live` | `\$\([^)]+\)\.live\s*\(` | jQuery .live() calls | `.on()` with event delegation |
| `jquery_bind` | `\$\([^)]+\)\.bind\s*\(` | jQuery .bind() calls | `.on()` |
| `jquery_unbind` | `\$\([^)]+\)\.unbind\s*\(` | jQuery .unbind() calls | `.off()` |
| `jquery_delegate` | `\$\([^)]+\)\.delegate\s*\(` | jQuery .delegate() calls | `.on()` |

### JavaScript Deprecations

| Pattern Name | Regex | Detects |
|---|---|---|
| `document_write` | `document\.write\s*\(` | Synchronous document.write() |
| `sync_xhr` | `XMLHttpRequest.*?async\s*:\s*false` | Synchronous AJAX requests |
| `eval_usage` | `\beval\s*\(` | eval() calls |

### Content/Embed Patterns

| Pattern Name | Regex | Detects |
|---|---|---|
| `wordpress_embed` | `\[\[\s*\{.*?"fid"` | Drupal/WordPress media codes |
| `flash_object` | `<object[^>]*swf` | Flash object tags |
| `flash_embed` | `<embed[^>]*swf` | Flash embed tags |
| `http_link` | `href="http://[^s]` | Non-HTTPS links |

### Legacy Browser Support

| Pattern Name | Regex | Notes |
|---|---|---|
| `ie_conditional` | `<!--\[if\s+.*?IE\s*\d*.*?\]>` | IE conditional comments |
| `ie_specific_code` | `if\s*\(\s*navigator\.userAgent\.match.*?IE` | IE-specific JavaScript |

### CMS-Specific Patterns

| Pattern Name | Regex | Detection |
|---|---|---|
| `drupal_deprecated_api` | `(drupal_get_form\|drupal_render_form)` | Drupal 6/7 APIs |
| `wordpress_old_hook` | `do_action\s*\(\s*['\"].*?_deprecated` | Deprecated WordPress hooks |

---

## Creating Custom Patterns

### Step 1: Identify the Pattern

What code are you looking for?

```javascript
// Example: Old Lodash.js version checking
var _ = require('lodash');
if (_.VERSION < 3) { ... }

// The pattern we need to detect:
// Regex: \._VERSION\s*<\s*[\d]+
```

### Step 2: Build the Regex

Test your regex against sample code:

```python
import re

pattern = r'\._VERSION\s*<\s*[\d]+'
test_code = 'if (_.VERSION < 3) { console.log("old"); }'

if re.search(pattern, test_code, re.IGNORECASE):
    print("✓ Pattern matches!")
else:
    print("✗ Pattern doesn't match")
```

### Step 3: Run the Scanner

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "lodash_version_check":"\._VERSION\s*<\s*[\d]+"
    },
    "case_sensitive":false
  }'
```

### Step 4: Refine the Pattern

If you get false positives or miss matches, adjust the regex and try again.

---

## Pattern Tips & Tricks

### Escape Special Characters

Backslashes must be escaped in JSON:

```bash
# ❌ Wrong - single backslash not escaped
--config 'migration-scanner:{"patterns":{"test":"\d+"}}'

# ✓ Correct - properly escaped
--config 'migration-scanner:{"patterns":{"test":"\\d+"}}'
```

### Use Character Classes

```bash
# Match both jQuery syntaxes
\$\(.*?\)\.(live|bind)\s*\(

# Match both single and double quotes
(href|src)\s*=\s*[\"']https
```

### Use Non-Greedy Quantifiers

```bash
# ✓ Good - stops at first }
\[\[.*?\}\]

# ❌ Bad - matches entire file if multiple patterns
\[\[.*\}\]
```

### Test with Real Page Content

```bash
# Extract a page's HTML
python -c "
import json
with open('projects/example-com/snapshots/*/pages/*/raw.html') as f:
    html = f.read()
    # Test your regex
    import re
    matches = re.findall(r'YOUR_PATTERN', html)
    print(f'Found {len(matches)} matches')
"
```

### Common Regex Patterns Reference

```regex
# Match HTML tags
<(script|object|embed|applet)[^>]*>

# Match JavaScript function calls
(document\.write|eval|with)\s*\(

# Match deprecated jQuery methods
\$(selector)\.(live|bind|unbind|delegate|undelegate)\s*\(

# Match old HTML
<(font|center|marquee|blink)

# Match Flash
(\.swf|swf\?|application/x-shockwave-flash)

# Match HTTP (non-HTTPS)
(http|ftp)://[^\s"'>]+

# Match synchronous XHR
(async\s*:\s*false|XMLHttpRequest)

# Match old Python 2
(xrange|unicode|basestring|iteritems|has_key)
```

---

## Storing Patterns for Reuse

Create a JSON file with your patterns:

```json
{
  "jquery_deprecations": {
    "jquery_live": "\\.live\\s*\\(",
    "jquery_bind": "\\.bind\\s*\\(",
    "jquery_unbind": "\\.unbind\\s*\\("
  },
  "flash": {
    "flash_object": "<object[^>]*swf",
    "flash_embed": "<embed[^>]*swf"
  },
  "deprecated_apis": {
    "document_write": "document\\.write\\s*\\(",
    "eval": "\\beval\\s*\\("
  }
}
```

Then use them:
```bash
# Load and use patterns from file
PATTERNS=$(jq -r '.jquery_deprecations | to_entries | map("\(.key):\(.value)") | join(",")' migration_patterns.json)
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config "migration-scanner:{\"patterns\":{...}}"
```

---

## Output Format

### Test Results File Location

Results are saved to: `projects/<slug>/test-results/results_<timestamp>.json`

Example: `projects/example-com/test-results/results_2025-12-10T14-30-45.123456Z.json`

### Results Structure

```json
{
  "plugin_name": "migration-scanner",
  "status": "fail",
  "summary": "Found 45 migration-related patterns across 12 unique pages.",
  "details": {
    "findings": [
      {
        "url": "https://example.com/article-1",
        "match": "$(document).live('click', handler)",
        "start": 2341,
        "end": 2380,
        "page_slug": "article-1",
        "context": "...10 lines of HTML/code before and after match...",
        "line_number": 145,
        "pattern_name": "jquery_live_event",
        "suggestion": "jQuery .live() is deprecated. Consider using .on() instead..."
      }
    ],
    "patterns": {
      "jquery_live_event": "\\$\\([^)]+\\)\\.live\\s*\\(",
      "deprecated_api_call": "old_api_pattern"
    },
    "case_sensitive": false
  }
}
```

### Understanding Each Field

| Field | Type | Purpose |
|-------|------|---------|
| `plugin_name` | string | Always "migration-scanner" |
| `status` | string | "pass" (no matches) or "fail" (matches found) |
| `summary` | string | Human-readable count of findings |
| `findings[].url` | string | Full URL where match was found |
| `findings[].match` | string | Exact text that matched the pattern |
| `findings[].start` | int | Character offset where match begins |
| `findings[].end` | int | Character offset where match ends |
| `findings[].page_slug` | string | Directory name of the page snapshot |
| `findings[].context` | string | 10 lines before and after match |
| `findings[].line_number` | int | Line number in source (1-based) |
| `findings[].pattern_name` | string | Name of the pattern that matched |
| `findings[].suggestion` | string | Recommended fix or migration path |

### Parsing Results Examples

**Python - Extract URLs with matches:**
```python
import json

with open('projects/example-com/test-results/results_*.json') as f:
    data = json.load(f)

affected_urls = set(f['url'] for f in data['details']['findings'])
print(f"Affected pages: {len(affected_urls)}")
for url in sorted(affected_urls):
    print(f"  - {url}")
```

**Bash - Count matches by pattern:**
```bash
jq '.details.findings | group_by(.pattern_name) | map({pattern: .[0].pattern_name, count: length})' \
  projects/example-com/test-results/results_*.json
```

**JSON - Find matches on specific pages:**
```bash
jq '.details.findings[] | select(.page_slug == "article-1")' \
  projects/example-com/test-results/results_*.json
```

---

## Real-World Use Cases

### WordPress Plugin Migration

**Scenario:** Upgrading WordPress plugin with deprecated hooks

```bash
# 1. Create project
python -m src.analyzer.cli project new "https://myblog.com"
python -m src.analyzer.cli crawl start myblog-com --max-pages 500

# 2. Find deprecated hooks
python -m src.analyzer.cli test run myblog-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "old_add_meta":"add_meta_box\\s*\\(\\s*[\"'"'"']meta_['"'"\"]*,",
      "old_get_option":"get_option\\s*\\(\\s*[\"'"'"']option_['"'"\"]*,.*?[Dd]efault",
      "filter_deprecated":"add_filter\\s*\\(\\s*[\"'"'"'].*?_deprecated"
    }
  }'

# 3. Review results
cat projects/myblog-com/test-results/results_*.json | jq '.summary'
```

### jQuery to Vanilla JavaScript

**Scenario:** Removing jQuery dependency, tracking remaining jQuery usage

```bash
# Phase 1: Identify all jQuery
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_init":"\\$\\(.*?\\)\\.(ready|load|each|map|filter|reduce)",
      "jquery_dom":"\\$\\(['"'"\"]*\\w+['"'"\"]*\\)\\.(html|text|val|attr|css)",
      "jquery_events":"\\$.*?\\.(on|off|click|hover|submit)"
    }
  }' \
  --no-save

# Phase 2: After conversion, verify cleanup
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_remaining":"\\$\\s*\\(|jQuery\\s*\\("
    }
  }'
```

### Flash to HTML5 Migration

**Scenario:** Tracking progress of Flash removal

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "flash_object":"<object[^>]*?type\\s*=\\s*['"'"\"]*application/x-shockwave-flash",
      "flash_embed":"<embed[^>]*?src\\s*=\\s*['"'"\"]*[^'"'"\"]*\\.swf",
      "swf_reference":"\\.swf['"'"\"\\s/)]",
      "flashvars":"flashvars\\s*=\\s*['"'"\"]*[^'"'"\"]*",
      "swobject":"swfobject\\.embedSWF\\s*\\("
    }
  }'
```

### Legacy Code Cleanup

**Scenario:** Audit and cleanup before modernization sprint

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "var_declarations":"\\bvar\\s+\\w+\\s*=",
      "function_declarations":"function\\s+\\w+\\s*\\(",
      "html5_doctype":"<!DOCTYPE[^>]*HTML[^>]*4",
      "inline_styles":"style\\s*=\\s*['"'"\"]*[^'"'"\"]*",
      "table_layout":"<table[^>]*.*?<tr.*?<td",
      "document_write":"document\\.write\\s*\\(",
      "eval_usage":"\\beval\\s*\\(",
      "with_statement":"\\bwith\\s*\\("
    },
    "case_sensitive":false
  }'
```

### Security & Compliance Audit

**Scenario:** Find insecure patterns that need fixing

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "http_links":"href\\s*=\\s*['"'"\"]*http://[^s]",
      "insecure_cookies":"document\\.cookie\\s*=.*?secure",
      "xss_risk":"innerHTML\\s*=",
      "sql_injection":"SELECT.*?FROM.*?WHERE.*?\\+",
      "hardcoded_credentials":"(password|apikey|secret)\\s*[:=]\\s*['"'"\"]*\\w+",
      "no_csp":"<meta.*?http-equiv\\s*=\\s*['"'"\"]*Content-Security-Policy"
    }
  }'
```

---

## Troubleshooting

### "Invalid config format"

**Issue:** Configuration string not properly formatted

**Solution:** Ensure JSON is valid:
```bash
# ❌ Wrong - incomplete JSON
--config 'migration-scanner:{"patterns":{"test"}'

# ✓ Correct - valid JSON
--config 'migration-scanner:{"patterns":{"test":"regex"}}'

# Test JSON validity
python3 -c "import json; json.loads('{\"patterns\":{\"test\":\"regex\"}}')"
```

### "Invalid regex pattern"

**Issue:** Regex has a syntax error

**Solution:** Test the regex in Python first:
```python
import re

try:
    re.compile(r'your_pattern_here')
    print("✓ Valid regex")
except re.error as e:
    print(f"✗ Invalid: {e}")
```

**Common mistakes:**
- Missing backslash escapes: `\.` not `.`
- Unmatched parentheses: `(pattern` should be `(pattern)`
- Invalid character class: `[z-a]` should be `[a-z]`

### No matches found

**Checklist:**
1. Verify the pattern exists in your snapshot:
   ```bash
   grep -r "your_pattern" projects/example-com/snapshots/*/pages/*/raw.html
   ```

2. Test pattern on actual HTML:
   ```python
   import re
   html = open('projects/example-com/snapshots/*/pages/*/raw.html').read()
   if re.search(r'your_pattern', html):
       print("Found!")
   ```

3. Check case sensitivity setting (default: `case_sensitive: false`)

4. Verify snapshot exists and is recent:
   ```bash
   python -m src.analyzer.cli project snapshots example-com
   ```

### Too many matches (false positives)

**Solutions:**
- **Be more specific**: `\.live\(` instead of `live`
- **Use anchors**: `^pattern` or `pattern$`
- **Add context**: `function.*?pattern` instead of just `pattern`
- **Use word boundaries**: `\blive\b` to match whole words only

Example refinement:
```bash
# ❌ Too broad - matches "olive", "alive", etc.
--config 'migration-scanner:{"patterns":{"jquery":"\\.live"}}'

# ✓ Better - matches .live() calls specifically
--config 'migration-scanner:{"patterns":{"jquery":"\\.live\\s*\\("}}'
```

### Timeout error

**Issue:** Scan took too long

**Solution:** Increase timeout or reduce pages:
```bash
# Increase timeout
--timeout 600  # 10 minutes instead of default 5

# Or run on older snapshot with fewer pages
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --snapshot "specific-old-snapshot"
```

### Memory issues on large sites

**Issue:** Process runs out of memory with 10,000+ pages

**Solution:** Run separate scans for different pattern groups:
```bash
# Run 1: jQuery patterns
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"jquery_live":"\\.live"}}'

# Run 2: Deprecation patterns
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"document_write":"document\\.write"}}'
```

---

## Performance & Scalability

### Scan Speed

Performance varies with:
- Number of pages in snapshot
- Complexity of regex patterns
- Size of each page's HTML

**Typical performance:**

| Pages | Patterns | Time | Rate |
|-------|----------|------|------|
| 100 | 1 simple | ~10 sec | 10 p/s |
| 100 | 5 complex | ~30 sec | 3 p/s |
| 1,000 | 3 simple | ~2 min | 8 p/s |
| 1,000 | 10 complex | ~5 min | 3 p/s |

### Memory Usage

- Pattern compilation: <1 MB (regardless of pattern count)
- Per 1000 pages: ~20-30 MB
- Results data: ~1-5 MB per 10k matches

### Optimization Tips

1. **Use simpler patterns** when possible:
   - `\.live\(` is faster than `jQuery\s*\([^)]*\)\.live\s*\(`

2. **Avoid catastrophic backtracking**:
   - `(a+)+` ← Bad, can hang
   - `(a+)?b` ← Better

3. **Split large pattern sets**:
   - Run 5 patterns × 2 = 10 seconds
   - Run 10 patterns × 1 = 30 seconds (sublinear scaling)

4. **Use `case_sensitive: true`** if possible:
   - Faster pattern matching

---

## FAQ

**Q: Can I exclude certain pages from scanning?**
A: Not directly in migration-scanner. Workaround: Run on a specific snapshot, or filter results afterward.

**Q: Can I scan files other than HTML?**
A: Currently scans HTML content from snapshots. For other file types, save them as HTML or use standalone regex tools.

**Q: How do I export results to CSV or other formats?**
A: Results are saved as JSON. Use `jq` or Python to convert:
```bash
# Convert to CSV
jq -r '.details.findings[] | [.url, .pattern_name, .match, .line_number] | @csv' results.json > findings.csv
```

**Q: Can patterns be used recursively or with dependencies?**
A: No, each pattern is evaluated independently. For complex multi-stage detection, run multiple scanner calls.

**Q: How do I version control patterns?**
A: Store in JSON file and commit to git:
```bash
git add migration_patterns.json
git commit -m "Add pattern definitions for jQuery migration"
```

**Q: Can I run scanners on live websites without crawling first?**
A: No, migration-scanner works on snapshots created by the crawl command. Use `crawl start` first.

**Q: What if my website has JavaScript-rendered content?**
A: The crawler uses Crawl4AI which includes JavaScript rendering. Dynamic content should be captured.

**Q: How often should I run scans?**
A: Depends on your needs:
- **During migration**: After each code change
- **Quality gate**: Before each release
- **Maintenance**: Monthly to catch new issues
- **Audit**: Quarterly full analysis

---

## See Also

- [Quick Start Guide](../../QUICKSTART.md)
- [Main README](../../README.md)
- [Bug Finder Guide](BUG_FINDER.md)
- [Project Workspace Guide](PROJECTS.md)
- [Architecture Reference](../reference/ARCHITECTURE.md)
