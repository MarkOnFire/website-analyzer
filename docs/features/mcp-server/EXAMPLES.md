# Website-Analyzer MCP Server - Usage Examples

Real-world examples and templates for using the MCP server with Claude Desktop.

## Getting Started

Once your MCP server is configured in Claude Desktop, you can ask Claude to use these tools naturally:

```
Analyze my-site-com for any issues
```

Claude will automatically call the appropriate tools. Here are specific examples you can use.

## Basic Operations

### List All Projects

**You ask Claude:**
```
What projects do I have?
```

**Claude calls:**
```
tool: list_projects
parameters: {}
```

**You'll see:**
```
Available projects:
- example-com (5 snapshots, latest results from 2025-12-11)
- staging-site-com (2 snapshots)
- blog-example-com (8 snapshots, latest results from 2025-12-10)
```

### Quick Scan

**You ask Claude:**
```
Scan example-com with all available tests
```

**Claude calls:**
```
tool: scan_website
parameters: {
  "project_slug": "example-com",
  "background": false,
  "timeout_seconds": 300
}
```

**Results displayed:**
```
Scan Results for example-com

Total Tests: 3

## migration_scanner
Status: pass
Summary: No deprecated jQuery patterns found
Details: Scanned 47 pages, 0 deprecated patterns

## xss_check
Status: pass
Summary: No XSS vulnerabilities detected

## performance
Status: warning
Summary: Found 3 slow pages (> 3s load time)
Details: Pages: /about, /products, /contact
```

## Advanced Scanning

### Background Scan for Large Site

**You ask Claude:**
```
Scan big-site-com in the background since it has 10,000 pages.
Monitor its progress and tell me when it's done.
```

**Claude calls:**
```
tool: scan_website
parameters: {
  "project_slug": "big-site-com",
  "background": true,
  "timeout_seconds": 600
}
```

**Gets scan ID:** `550e8400-e29b-41d4-a716-446655440000`

**Monitors with:**
```
tool: get_scan_status
parameters: {
  "scan_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Claude displays:**
```
Starting background scan of big-site-com...

[After 10 seconds]
Scan Status: running
Project: big-site-com
Progress: 15%

[After 30 seconds]
Scan Status: running
Project: big-site-com
Progress: 42%

[After 120 seconds]
Scan Status: completed
Project: big-site-com
Progress: 100%

Results (5 tests):
- migration_scanner: pass
- xss_check: pass
- security_headers: warning
- performance: pass
- accessibility: pass
```

### Scan with Specific Tests

**You ask Claude:**
```
Run only the migration_scanner and xss_check tests on my-site-com
```

**Claude calls:**
```
tool: scan_website
parameters: {
  "project_slug": "my-site-com",
  "test_names": ["migration_scanner", "xss_check"],
  "background": false
}
```

**Results:**
```
Scan Results for my-site-com

Total Tests: 2

## migration_scanner
Status: pass
Summary: No deprecated jQuery patterns found

## xss_check
Status: pass
Summary: No XSS vulnerabilities detected
```

### Scan Specific Snapshot

**You ask Claude:**
```
Re-analyze the snapshot from December 9th of example-com
```

**Claude calls:**
```
tool: scan_website
parameters: {
  "project_slug": "example-com",
  "snapshot_timestamp": "2025-12-09T14-32-15.123456Z",
  "background": false
}
```

**Results show:**
```
Analyzing snapshot from 2025-12-09T14:32:15Z...
[Results from that point in time]
```

## Pattern Management

### Discover Patterns

**You ask Claude:**
```
What security patterns are available?
```

**Claude calls:**
```
tool: list_patterns
parameters: {
  "tag": "security"
}
```

**Displays:**
```
Found 4 security patterns:

## xss_vulnerability
Description: Detects potential XSS vulnerabilities
Severity: critical
Tags: security, injection
Patterns: 3
Author: Security Team

## csrf_token_missing
Description: Finds missing CSRF tokens
Severity: high
Tags: security, tokens

## sql_injection_risk
Description: Identifies potential SQL injection vectors
Severity: critical
Tags: security, injection

## insecure_headers
Description: Checks for missing security headers
Severity: medium
Tags: security, headers
```

### Find High-Risk Patterns

**You ask Claude:**
```
Show me only the critical severity patterns
```

**Claude calls:**
```
tool: list_patterns
parameters: {
  "severity": "critical"
}
```

**Results:**
```
Critical Severity Patterns:

## xss_vulnerability
- Detects XSS attacks
- 3 regex patterns
- Common vulnerability

## sql_injection_risk
- Finds SQL injection vectors
- 5 regex patterns
```

### Test a Pattern on Your Content

**You ask Claude:**
```
Test the xss_vulnerability pattern against https://my-site.com/contact
```

**Claude calls:**
```
tool: test_pattern
parameters: {
  "pattern_name": "xss_vulnerability",
  "url": "https://my-site.com/contact"
}
```

**Results:**
```
Pattern Test Results: xss_vulnerability

Pattern: Detects potential XSS vulnerabilities
Matches Found: 0 ✓

Your page appears safe from this XSS pattern.
```

### Test Pattern Against Code Snippet

**You ask Claude:**
```
Does the xss_vulnerability pattern match this code:
<img src=x onerror="alert('xss')">
```

**Claude calls:**
```
tool: test_pattern
parameters: {
  "pattern_name": "xss_vulnerability",
  "content": "<img src=x onerror=\"alert('xss')\">"
}
```

**Results:**
```
Pattern Test Results: xss_vulnerability

Pattern: Detects potential XSS vulnerabilities
Matches Found: 1 ⚠️

Matches by Pattern:
- <script|onerror|onload patterns: 1 match
  1. <img src=x onerror="alert('xss')">

This code contains an XSS vulnerability!
```

### Find Patterns by Tag

**You ask Claude:**
```
Show all patterns tagged with 'performance'
```

**Claude calls:**
```
tool: list_patterns
parameters: {
  "tag": "performance"
}
```

## Results Management

### View Latest Results

**You ask Claude:**
```
Show me the latest scan results for example-com
```

**Claude calls:**
```
tool: get_scan_results
parameters: {
  "project_slug": "example-com",
  "summary_only": true
}
```

**Displays:**
```
Results: results_2025-12-11T15-30-45.123456Z.json

## migration_scanner
Status: pass
Summary: No deprecated jQuery patterns found

## xss_check
Status: pass
Summary: No XSS vulnerabilities detected

## performance
Status: warning
Summary: Found 3 slow pages (>3s load time)

[More results...]
```

### Get Full Detailed Results

**You ask Claude:**
```
Give me the complete technical details of the latest scan for my-site-com
```

**Claude calls:**
```
tool: get_scan_results
parameters: {
  "project_slug": "my-site-com",
  "summary_only": false
}
```

**Returns full JSON:**
```json
[
  {
    "plugin_name": "migration_scanner",
    "timestamp": "2025-12-11T15:30:45Z",
    "status": "pass",
    "summary": "No deprecated jQuery patterns found",
    "details": {
      "total_pages": 47,
      "patterns_checked": ["live()", "die()"],
      "matches": [],
      "deprecated_count": 0
    }
  },
  ...
]
```

### View Specific Results File

**You ask Claude:**
```
Show me the results from the scan on December 10th (results_2025-12-10T09-15-22Z.json)
```

**Claude calls:**
```
tool: get_scan_results
parameters: {
  "project_slug": "example-com",
  "results_file": "results_2025-12-10T09-15-22.123456Z.json",
  "summary_only": true
}
```

## Export Operations

### Export as Markdown Report

**You ask Claude:**
```
Create a markdown report of the latest example-com scan results
```

**Claude calls:**
```
tool: export_results
parameters: {
  "project_slug": "example-com",
  "format": "markdown",
  "summary_only": true
}
```

**Produces:**
```markdown
# Website Analysis Report: example-com

**Scan Date:** 2025-12-11T15:30:45Z
**Project:** example-com
**Website:** https://example.com
**Total Tests:** 5
**Passed:** 4 | **Warnings:** 1 | **Failed:** 0

## Executive Summary

Your website passed most checks. One performance issue found on 3 pages.

## Detailed Results

### migration_scanner ✓
- **Status:** Pass
- **Description:** No deprecated jQuery patterns found
- **Details:**
  - Pages checked: 47
  - Deprecated patterns: 0
  - jQuery .live() usage: 0

### xss_check ✓
- **Status:** Pass
- **Description:** No XSS vulnerabilities detected

### performance ⚠️
- **Status:** Warning
- **Description:** Found 3 slow pages
- **Affected Pages:**
  - /about (3.2s)
  - /products (4.1s)
  - /contact (3.5s)

[More sections...]
```

### Export as JSON

**You ask Claude:**
```
Export the example-com results as JSON for archival
```

**Claude calls:**
```
tool: export_results
parameters: {
  "project_slug": "example-com",
  "format": "json"
}
```

**Returns raw JSON data** suitable for scripts/import.

### Export as CSV

**You ask Claude:**
```
Give me the results as CSV so I can import into Excel
```

**Claude calls:**
```
tool: export_results
parameters: {
  "project_slug": "example-com",
  "format": "csv"
}
```

## Complex Workflows

### Complete Site Audit

**You ask Claude:**
```
I want to do a complete audit of my-site-com:
1. List all available security patterns
2. Test the top 3 security patterns against my homepage
3. Run a full scan of the site
4. Export results as markdown
```

**Claude will:**
1. Call `list_patterns` with `severity: "critical"`
2. Call `test_pattern` 3 times (once per pattern)
3. Call `scan_website` for full scan
4. Call `export_results` with `format: "markdown"`
5. Present a comprehensive audit report

**Workflow Output:**
```
Security Pattern Audit for my-site-com

## Available Security Patterns
Found 4 critical severity patterns:
- xss_vulnerability
- sql_injection_risk
- csrf_protection_missing
- insecure_headers

## Pattern Testing Results

### xss_vulnerability
Tested against: https://my-site.com
Matches: 0 ✓

### sql_injection_risk
Tested against: https://my-site.com
Matches: 0 ✓

### csrf_protection_missing
Tested against: https://my-site.com
Matches: 1 ⚠️
Found in: POST /api/contact

## Full Site Scan
[Running all tests...]
Completed in 45 seconds

Total Tests: 5
Passed: 4
Warnings: 1
Failed: 0

## Summary Report

### Strengths
✓ No XSS vulnerabilities detected
✓ No SQL injection risks found
✓ Performance acceptable

### Areas for Improvement
⚠️ CSRF tokens missing on one endpoint
→ Recommendation: Add CSRF token validation to POST endpoints

### Full Report
[Markdown report generated...]
```

### Comparative Analysis

**You ask Claude:**
```
Compare the scan results from December 10th vs today for example-com.
Did our security improve?
```

**Claude will:**
1. Call `get_scan_results` with old results file
2. Call `get_scan_results` with latest results
3. Compare the data
4. Present findings

**Analysis Output:**
```
Scan Comparison: December 10 vs December 11

### migration_scanner
Dec 10: 5 deprecated jQuery patterns found
Dec 11: 0 deprecated patterns found
Result: ✓ IMPROVED

### xss_check
Dec 10: 0 vulnerabilities
Dec 11: 0 vulnerabilities
Result: MAINTAINED

### performance
Dec 10: 5 slow pages
Dec 11: 2 slow pages
Result: ✓ IMPROVED

Overall: Security posture improved significantly!
```

### Batch Test Multiple Patterns

**You ask Claude:**
```
Test these 5 patterns against https://my-site.com and tell me which ones match:
- jquery_live_deprecated
- xss_vulnerability
- sql_injection_risk
- insecure_headers
- missing_csp_header
```

**Claude will call `test_pattern` 5 times** and present results:

```
Pattern Test Results for https://my-site.com

1. jquery_live_deprecated - 0 matches ✓
2. xss_vulnerability - 0 matches ✓
3. sql_injection_risk - 0 matches ✓
4. insecure_headers - 2 matches ⚠️
   - Missing Security-Headers
   - Missing X-Frame-Options
5. missing_csp_header - 1 match ⚠️
   - Content-Security-Policy not set
```

## Tips and Tricks

### Faster Scans
Use `test_names` to run only relevant tests:
```
Run just migration_scanner on my-site-com
```

### Background Scanning for Production
Always use background mode for large sites:
```
Scan my-large-production-site in the background
```

### Pattern Discovery Workflow
1. Start with `list_patterns`
2. Filter by severity or tag
3. Test promising patterns with `test_pattern`
4. Include in full scan with `scan_website`

### Exporting for Stakeholders
Export as markdown or HTML for non-technical stakeholders:
```
Create a nice markdown report for my boss showing today's scan
```

### Tracking Progress
Use `get_scan_status` to monitor long-running scans:
```
Check the status of scan 550e8400-e29b-41d4-a716-446655440000
```

## Troubleshooting Examples

### "Project not found" Error

**Problem:**
```
Claude: Error: Project not found: typo-site-com
```

**Solution:**
```
You: List all my projects first
Claude: [Shows available projects]
You: Now scan example-com (correct name)
```

### Scan Timeout

**Problem:**
```
Claude: Error: Test timed out after 300s
```

**Solution:**
```
You: Scan example-com with a longer timeout (900 seconds) in the background
Claude: [Starts with increased timeout]
```

### Pattern Not Found

**Problem:**
```
Claude: Error: Pattern not found: typo_pattern
```

**Solution:**
```
You: Show me all available patterns
Claude: [Lists all patterns]
You: Test the misspelled_detector pattern against my site
```

## Advanced Scenarios

### Continuous Monitoring Setup

**You ask:**
```
I want to monitor example-com weekly. Set up a routine where:
1. Scan the site every Monday
2. Export results as markdown
3. Compare to previous week
4. Alert if any new issues found
```

**Claude can help by providing:**
- A schedule template
- MCP calls needed for each step
- Comparison logic
- Alert conditions

### CI/CD Integration

**You ask:**
```
How would I integrate MCP scans into my CI/CD pipeline?
```

**Claude explains:**
- MCP server can run as background service
- Each commit could trigger `scan_website`
- Results checked programmatically
- Integration with GitHub Actions, etc.

### Custom Reporting

**You ask:**
```
Create a detailed weekly report showing:
- Pass/fail summary table
- Trend analysis vs last month
- Top 3 areas needing improvement
- Recommended actions
```

**Claude generates:**
- Comprehensive report template
- MCP calls needed for data
- Analysis and recommendations

## Next Steps

Once you're comfortable with these examples:

1. Explore your own projects with `list_projects`
2. Start with simple scans on one site
3. Graduate to background scans for larger sites
4. Set up regular pattern testing
5. Build automated workflows

For more details, see:
- [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md) - Setup instructions
- [MCP_SERVER_README.md](MCP_SERVER_README.md) - Complete API reference
