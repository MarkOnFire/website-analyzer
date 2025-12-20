# User Guide

Complete guide for using the Website Analyzer with Claude Code and other AI assistants.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Using with Claude](#using-with-claude)
6. [Common Workflows](#common-workflows)
7. [Test Plugins](#test-plugins)
8. [Interpreting Results](#interpreting-results)
9. [Troubleshooting](#troubleshooting)

## Overview

Website Analyzer is a comprehensive tool for analyzing website health, security, SEO, and migration readiness. It crawls websites, stores snapshots, runs analysis tests, and tracks issues over time.

Key features:
- Crawl4AI-powered website crawling with snapshot management
- Pluggable test framework (migration scanner, SEO optimizer, LLM optimizer, security audit)
- Issue tracking and resolution detection
- MCP server integration for AI assistant workflows
- Scheduled scans and notifications
- Web dashboard for result visualization

## Installation

### Requirements

- Python 3.11 or higher
- Node.js 18+ (for MCP server)
- Chromium (installed via Playwright)

### Basic Installation

```bash
# Clone repository
git clone <repository-url>
cd website-analyzer

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

### MCP Server Installation (for Claude integration)

```bash
# Install Node.js dependencies
cd mcp-server
npm install
npm run build
cd ..
```

### Verify Installation

```bash
# Check environment
python -m src.analyzer.cli --help

# View available tests
python -m src.analyzer.cli test list-plugins
```

## Quick Start

### 1. Create a Project

```bash
# Create workspace for a website
python -m src.analyzer.cli project new https://example.com

# List projects
python -m src.analyzer.cli project list
```

### 2. Crawl the Website

```bash
# Crawl website (uses project slug from URL)
python -m src.analyzer.cli crawl site example-com

# Crawl with options
python -m src.analyzer.cli crawl site example-com --max-pages 100
```

### 3. Run Tests

```bash
# Run all tests on latest snapshot
python -m src.analyzer.cli test run example-com

# Run specific test
python -m src.analyzer.cli test run example-com --test seo-optimizer

# Run multiple tests
python -m src.analyzer.cli test run example-com --test migration-scanner --test security-audit
```

### 4. View Results

```bash
# View issues found
python -m src.analyzer.cli test view-issues example-com

# Export results
python -m src.analyzer.cli test export example-com --format json --output results.json
```

## Core Concepts

### Projects and Workspaces

A **project** represents a single website being analyzed. Each project has:
- A unique **slug** (derived from the URL, e.g., `example-com`)
- A workspace directory in `projects/<slug>/`
- Metadata tracking creation time, last crawl, etc.

Directory structure:
```
projects/
└── example-com/
    ├── metadata.json         # Project metadata
    ├── issues.json          # Tracked issues
    ├── snapshots/           # Timestamped crawl snapshots
    │   └── 2025-12-20T10-30-45.123456Z/
    │       ├── pages/       # Per-page HTML/markdown
    │       ├── sitemap.json # Discovered URLs
    │       └── summary.json # Crawl statistics
    └── test-results/        # Test execution results
```

### Snapshots

A **snapshot** is a point-in-time capture of a website, created during crawling. Each snapshot contains:
- All crawled pages (HTML, cleaned HTML, markdown)
- Page metadata (URLs, status codes, timestamps, headers)
- Sitemap of discovered internal links
- Crawl summary (pages crawled, errors, duration)

Snapshots are timestamped and immutable, allowing historical comparison.

### Test Plugins

**Test plugins** analyze snapshots and generate findings. Built-in plugins:
- **migration-scanner**: Find deprecated code patterns (jQuery .live(), old APIs, etc.)
- **seo-optimizer**: Check meta tags, title tags, headings, alt text, sitemaps
- **llm-optimizer**: Analyze schema.org markup, content clarity, meta quality for AI discovery
- **security-audit**: Check HTTPS usage, security headers, cookie flags, exposed files

### Issues

**Issues** are structured findings extracted from test results. Features:
- Unique IDs with sequential numbering
- Priority levels (high, medium, low)
- Status tracking (open, investigating, fixed, verified)
- Automatic resolution detection when issues disappear
- History tracking (when detected, when resolved)

### Test Results

**Test results** are JSON files containing:
- Plugin name and execution timestamp
- Status (pass, fail, warning, error)
- Summary of findings
- Structured details (affected pages, matches, suggestions)

Results are timestamped and stored in `projects/<slug>/test-results/`.

## Using with Claude

### Setup MCP Server

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "node",
      "args": ["/absolute/path/to/website-analyzer/mcp-server/build/index.js"],
      "cwd": "/absolute/path/to/website-analyzer"
    }
  }
}
```

Restart Claude Desktop after adding the configuration.

### Basic Workflow with Claude

1. **Ask Claude to analyze a website:**
   ```
   Please analyze https://example.com for SEO and security issues
   ```

2. **Claude will:**
   - Use `start_analysis` tool to create project and run tests
   - Use `check_status` to monitor progress
   - Use `view_issues` to retrieve findings
   - Present results in a readable format

3. **Request specific tests:**
   ```
   Scan https://example.com for deprecated jQuery patterns
   ```

4. **Rerun tests after fixes:**
   ```
   Rerun SEO tests on example.com to check if issues are fixed
   ```

### Advanced Claude Interactions

**Compare snapshots:**
```
Compare the latest two snapshots of example.com and tell me what changed
```

**Schedule recurring scans:**
```
Set up a weekly SEO scan for example.com and notify me via email
```

**Export results:**
```
Export the latest security audit results to HTML format
```

## Common Workflows

### Workflow 1: One-Time Site Analysis

```bash
# Create project and crawl
python -m src.analyzer.cli project new https://example.com
python -m src.analyzer.cli crawl site example-com

# Run all tests
python -m src.analyzer.cli test run example-com

# View issues
python -m src.analyzer.cli test view-issues example-com
```

### Workflow 2: Migration Pattern Scanning

```bash
# Create config file with patterns
cat > migration-config.json << EOF
{
  "migration-scanner": {
    "patterns": {
      "jquery_live": "\\.live\\s*\\(",
      "deprecated_api": "oldApiCall\\s*\\("
    },
    "case_sensitive": false
  }
}
EOF

# Run scan with config
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config-file migration-config.json
```

### Workflow 3: Continuous Monitoring

```bash
# Schedule daily SEO scans
python -m src.analyzer.cli schedule add \
  --project example-com \
  --cron "0 9 * * *" \
  --tests seo-optimizer \
  --recrawl

# Start scheduler daemon
python -m src.analyzer.cli daemon start

# View scheduled scans
python -m src.analyzer.cli schedule list
```

### Workflow 4: Issue Resolution Tracking

```bash
# Initial scan
python -m src.analyzer.cli test run example-com

# View issues
python -m src.analyzer.cli test view-issues example-com --status open

# After fixing issues, recrawl and retest
python -m src.analyzer.cli crawl site example-com
python -m src.analyzer.cli test run example-com

# View resolved issues
python -m src.analyzer.cli test view-issues example-com --status resolved
```

## Test Plugins

### Migration Scanner

Finds deprecated code patterns using regex.

**Configuration:**
```json
{
  "migration-scanner": {
    "patterns": {
      "pattern_name": "regex_pattern"
    },
    "case_sensitive": false
  }
}
```

**Common patterns:**
- jQuery .live(): `\\.live\\s*\\(`
- document.write(): `document\\.write\\s*\\(`
- Sync XHR: `new\\s+XMLHttpRequest\\(\\).*\\.open\\([^,]*,[^,]*,\\s*false`

### SEO Optimizer

Checks on-page SEO factors.

**Checks performed:**
- Title tag presence, length (50-60 chars), uniqueness
- Meta description presence, length (150-160 chars)
- H1 tag presence and count (should be 1)
- Image alt text coverage
- Internal linking structure
- robots.txt and sitemap.xml validation
- Duplicate content detection

**Results include:**
- Overall SEO score (0-10)
- Critical issues (blocking)
- Warnings (should fix)
- Opportunities (nice to have)

### LLM Optimizer

Analyzes content structure for AI discovery.

**Checks performed:**
- Meta tag quality (description, keywords, Open Graph, Twitter Cards)
- Schema.org markup presence and validation
- Heading structure (H1-H6 hierarchy)
- Content clarity and readability
- Internal link structure

**Results include:**
- LLM optimization score (0-10)
- Quick wins (easy fixes)
- Strategic recommendations (larger improvements)

### Security Audit

Identifies security vulnerabilities.

**Checks performed:**
- HTTPS usage and mixed content
- Security headers (CSP, X-Frame-Options, HSTS, etc.)
- Cookie security flags (Secure, HttpOnly, SameSite)
- Exposed sensitive files (/.git, /.env, /admin)
- Information disclosure (HTML comments, error messages)
- Third-party script sources
- Subresource Integrity (SRI) hashes

**Results include:**
- Severity classification (high, medium, low)
- OWASP Top 10 mapping
- Hardening recommendations

## Interpreting Results

### Test Result Format

```json
{
  "plugin_name": "seo-optimizer",
  "timestamp": "2025-12-20T10:30:45.123456Z",
  "status": "fail",
  "summary": "Found 12 SEO issues across 5 pages",
  "details": {
    "score": 6.5,
    "critical": [...],
    "warnings": [...],
    "opportunities": [...]
  }
}
```

### Status Values

- **pass**: No issues found, all checks passed
- **fail**: Issues found that need attention
- **warning**: Potential issues detected, review recommended
- **error**: Test execution failed (configuration error, timeout, exception)

### Issue Format

```json
{
  "id": "ISS-001",
  "test": "seo-optimizer",
  "priority": "high",
  "status": "open",
  "title": "Missing meta description",
  "affected_urls": ["https://example.com/page1"],
  "details": {...},
  "detected_at": "2025-12-20T10:30:45Z",
  "resolved_at": null
}
```

### Priority Levels

- **high**: Critical issues affecting functionality, security, or major SEO
- **medium**: Important issues that should be fixed soon
- **low**: Minor improvements or optimizations

## Troubleshooting

### Common Issues

#### "Workspace not found for slug: example-com"

**Cause:** Project doesn't exist.

**Solution:**
```bash
# List projects to verify slug
python -m src.analyzer.cli project list

# Create project if missing
python -m src.analyzer.cli project new https://example.com
```

#### "No snapshots found for project example-com"

**Cause:** Project exists but hasn't been crawled yet.

**Solution:**
```bash
# Crawl the website first
python -m src.analyzer.cli crawl site example-com
```

#### "No matching tests found for: test-name"

**Cause:** Test plugin name is incorrect or plugin not installed.

**Solution:**
```bash
# List available plugins
python -m src.analyzer.cli test list-plugins

# Use exact plugin name from list
python -m src.analyzer.cli test run example-com --test seo-optimizer
```

#### "Failed to load snapshot: sitemap.json not found"

**Cause:** Incomplete or corrupted snapshot.

**Solution:**
```bash
# Recrawl to create fresh snapshot
python -m src.analyzer.cli crawl site example-com
```

#### "Test timed out after 300s"

**Cause:** Test took too long (large site, slow LLM API, etc.).

**Solution:**
```bash
# Increase timeout
python -m src.analyzer.cli test run example-com --timeout 600

# Or reduce crawl scope
python -m src.analyzer.cli crawl site example-com --max-pages 100
```

#### Crawler errors: "Could not fetch URL"

**Cause:** URL inaccessible, network issue, or blocked by robots.txt.

**Solution:**
```bash
# Verify URL is accessible in browser
# Check robots.txt: https://example.com/robots.txt
# Try with increased timeout
python -m src.analyzer.cli crawl site example-com --page-timeout 120000
```

### Configuration Issues

#### "Unsupported config format"

**Cause:** Config file extension not recognized.

**Solution:** Use `.json` or `.yaml` extension.

```bash
# Create JSON config
cat > config.json << EOF
{
  "migration-scanner": {
    "patterns": {"name": "pattern"}
  }
}
EOF

python -m src.analyzer.cli test run example-com --config-file config.json
```

#### "Invalid JSON in config file"

**Cause:** Malformed JSON syntax.

**Solution:** Validate JSON syntax.

```bash
# Use online validator or
python -m json.tool config.json
```

### MCP Server Issues

#### Claude doesn't see the analyzer tools

**Cause:** MCP server not configured or not running.

**Solution:**
1. Verify config in `claude_desktop_config.json`
2. Use absolute paths in config
3. Restart Claude Desktop
4. Check Claude's MCP server status in settings

#### "Failed to spawn Python CLI"

**Cause:** Python environment or module not found.

**Solution:**
- Ensure absolute path to Python interpreter in MCP server
- Verify `src.analyzer.cli` module is importable
- Check MCP server logs in Claude's settings

### Getting More Help

1. **Check environment:**
   ```bash
   python -m src.analyzer.cli --version
   python -m src.analyzer.cli test list-plugins
   ```

2. **Enable verbose output:**
   ```bash
   # Most commands support --verbose flag
   python -m src.analyzer.cli crawl site example-com --verbose
   ```

3. **Review logs:**
   - Crawl logs: Check terminal output during crawl
   - Test results: `projects/<slug>/test-results/`
   - Issue tracking: `projects/<slug>/issues.json`

4. **Consult documentation:**
   - [Developer Guide](developer-guide.md) for plugin development
   - [Feature docs](features/) for advanced features
   - [CLI Reference](reference/CLI_QUICK_REFERENCE.md) for all commands

5. **Report bugs:**
   - Include command run, error message, and `--verbose` output
   - Provide sample URLs if possible (or anonymized structure)
   - Check existing issues on GitHub first
