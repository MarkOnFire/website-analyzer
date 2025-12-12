# Quick Start - 2 Minutes to Your First Scan

Get analyzing in under 2 minutes. No complex setup required.

## Installation (30 seconds)

```bash
git clone https://github.com/yourusername/website-analyzer.git
cd website-analyzer
./init.sh
source .venv/bin/activate
```

Done! The `init.sh` script handles all setup.

---

## Find Visual Bugs (1 minute)

**What**: Find pages with the same bug as one broken example page.

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://www.example.com/page-with-bug" \
  --site "https://www.example.com" \
  --max-pages 100
```

**Check results:**
```bash
# View results
cat projects/example-com/scans/bug_results_*.txt

# Generate a professional report
python generate_enhanced_report_v2.py \
  projects/example-com/scans/bug_results_example-com.json

# View the report
open projects/example-com/reports/enhanced_report_*.html
```

---

## Find Deprecated Code Patterns (1 minute)

**What**: Find outdated JavaScript, CSS, or deprecated APIs across your site.

```bash
# 1. Create a project
python -m src.analyzer.cli project new "https://www.example.com"

# 2. Crawl the site
python -m src.analyzer.cli crawl start example-com --max-pages 100

# 3. Find jQuery .live() calls (deprecated, use .on() instead)
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_live":"\\.live\\s*\\("
    }
  }'

# 4. View results
cat projects/example-com/test-results/results_*.json | jq '.summary'
```

**Or find multiple patterns at once:**

```bash
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "jquery_live":"\\.live\\s*\\(",
      "flash":"<embed[^>]*\\.swf",
      "http_links":"href=[\"'"'"']http://[^s]"
    }
  }'
```

---

## That's It!

You've completed your first analysis. Here's what you can do next:

### Learn More
- [Bug Finder Full Guide](docs/guides/BUG_FINDER.md) - Advanced bug scanning
- [Migration Scanner Full Guide](docs/guides/MIGRATION_SCANNER.md) - Deep dive into patterns
- [Project Workspace Guide](docs/guides/PROJECTS.md) - Managing multiple sites

### Example Use Cases

**Find WordPress embed bugs:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://www.myblog.com/article-with-broken-image" \
  --site "https://www.myblog.com"
```

**Find Flash embeds to convert to HTML5:**
```bash
python -m src.analyzer.cli test run myblog-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "flash_object":"<object[^>]*swf",
      "flash_embed":"<embed[^>]*swf"
    }
  }'
```

**Find insecure HTTP links:**
```bash
python -m src.analyzer.cli test run myblog-com \
  --test migration-scanner \
  --config 'migration-scanner:{
    "patterns":{
      "http_links":"href=[\"'"'"']http://[^s]"
    }
  }'
```

**Scan a large site (5,000+ pages):**
```bash
# First: quick validation (100 pages)
python -m src.analyzer.cli crawl start myblog-com --max-pages 100
python -m src.analyzer.cli test run myblog-com --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'

# Then: full scan overnight
python -m src.analyzer.cli crawl start myblog-com --max-pages 5000
python -m src.analyzer.cli test run myblog-com --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"pattern":"regex"}}'
```

---

## Command Cheat Sheet

```bash
# Projects
python -m src.analyzer.cli project new "https://example.com"
python -m src.analyzer.cli project list
python -m src.analyzer.cli project info example-com

# Crawling
python -m src.analyzer.cli crawl start example-com --max-pages 500
python -m src.analyzer.cli crawl list example-com
python -m src.analyzer.cli crawl status example-com

# Bug Finder
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com"

# Migration Scanner
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --config 'migration-scanner:{"patterns":{"name":"regex"}}'

# Issues
python -m src.analyzer.cli issues list example-com
python -m src.analyzer.cli issues show example-com ISSUE_ID
```

---

## Troubleshooting

**Installation failed?**
```bash
# Verify Python 3.11+
python3 --version

# Try manual setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

**Scan timing out?**
```bash
# Reduce page count for quick testing
--max-pages 50

# Or increase timeout
python -m src.analyzer.cli test run example-com \
  --test migration-scanner \
  --timeout 600 \
  --config '...'
```

**JSON parse error?**
```bash
# Ensure your config JSON is valid
python3 -c "import json; json.loads('{\"patterns\":{\"test\":\"regex\"}}')"
```

---

## Next Steps

1. **Run a scan** with one of the examples above
2. **Check the results** in `projects/*/test-results/` or `projects/*/scans/`
3. **Read the guides** for your use case
4. **Customize patterns** to find your specific issues
5. **Share results** with your team

**Need help?** Open an issue on GitHub or check the full documentation in `docs/guides/`.

---

**Tip:** Bookmark the [Bug Finder Guide](docs/guides/BUG_FINDER.md) and [Migration Scanner Guide](docs/guides/MIGRATION_SCANNER.md) for quick reference while scanning.

Happy scanning! 🚀
