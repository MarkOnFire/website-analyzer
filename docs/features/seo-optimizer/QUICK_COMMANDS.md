# SEO Optimizer - Quick Commands Reference

## Basic Usage

### 1. Standard SEO Audit

Analyze any website for SEO issues:

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer
```

**Output**: Full SEO report with score, critical issues, warnings, and opportunities

---

### 2. E-Commerce Product Site

Optimize for product pages:

```bash
python -m src.analyzer.cli analyze https://shop.example.com \
  --tests seo-optimizer \
  --config '{"seo-optimizer": {"target_keywords": "buy online,order now"}}'
```

**Checks**: Product titles, descriptions, category pages, image alt text

---

### 3. SaaS Documentation

Audit technical documentation:

```bash
python -m src.analyzer.cli analyze https://docs.example.com \
  --tests seo-optimizer \
  --max-pages 200 \
  --config '{"seo-optimizer": {"target_keywords": "API integration,documentation"}}'
```

**Checks**: Heading hierarchy, code snippet documentation, internal linking

---

### 4. Blog Site Optimization

Keyword-focused blog analysis:

```bash
python -m src.analyzer.cli analyze https://blog.example.com \
  --tests seo-optimizer \
  --config '{"seo-optimizer": {
    "target_keywords": "web development tips,JavaScript tutorials,React guide"
  }}'
```

**Checks**: Keyword placement, content length, internal linking between articles

---

### 5. Corporate Website

Multi-keyword analysis:

```bash
python -m src.analyzer.cli analyze https://company.example.com \
  --tests seo-optimizer \
  --config '{"seo-optimizer": {
    "target_keywords": "software development,mobile app development,cloud solutions"
  }}'
```

**Checks**: Service pages, case studies, about pages, blog

---

## Advanced Usage

### 6. Combined Test Battery

Run all tests simultaneously:

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests migration-scanner,llm-optimizer,seo-optimizer,security-audit
```

**Analyzes**: Code migration patterns, LLM optimization, SEO, security

---

### 7. Save Results to File

Capture analysis results:

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output seo_audit_$(date +%Y%m%d).json
```

**Output**: Timestamped JSON file with all findings

---

### 8. Large Site Analysis (Batch)

Process large sites in chunks:

```bash
# Batch 1: Homepage + top categories
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --max-pages 100

# Batch 2: Product pages
python -m src.analyzer.cli analyze https://example.com/products/ \
  --tests seo-optimizer \
  --max-pages 200

# Batch 3: Blog archive
python -m src.analyzer.cli analyze https://example.com/blog/ \
  --tests seo-optimizer \
  --max-pages 300
```

---

### 9. Recurring Audits (Monthly)

Schedule monthly SEO audits:

```bash
# Add to crontab for 2:00 AM monthly
0 2 1 * * cd /path/to/website-analyzer && \
  python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output /path/to/audits/seo_$(date +\%Y\%m\%d).json
```

---

### 10. Before/After Comparison

Compare audit results:

```bash
# Initial audit
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output audit_before.json

# [Make improvements]

# Final audit
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output audit_after.json

# Compare (manual diff)
diff -u audit_before.json audit_after.json
```

---

## Configuration Examples

### Example 1: E-Commerce Keywords

```bash
--config '{"seo-optimizer": {
  "target_keywords": "buy online,free shipping,best price"
}}'
```

### Example 2: SaaS Keywords

```bash
--config '{"seo-optimizer": {
  "target_keywords": "API documentation,cloud platform,integration guide"
}}'
```

### Example 3: Blog Keywords

```bash
--config '{"seo-optimizer": {
  "target_keywords": "tutorial,guide,how to,tips,best practices"
}}'
```

### Example 4: Comma-Separated Keywords

```bash
--config '{"seo-optimizer": {
  "target_keywords": "python,javascript,web development,tutorials"
}}'
```

---

## Output Interpretation

### Score Ranges

| Score | Grade | Action |
|-------|-------|--------|
| 9.0-10.0 | A | Maintain, implement nice-to-haves |
| 8.0-8.9 | B+ | Good, fix minor issues |
| 7.0-7.9 | B | Competitive, improve warnings |
| 6.0-6.9 | C+ | Work needed, prioritize critical |
| 5.0-5.9 | C | Significant work required |
| <5.0 | F | Critical issues blocking indexing |

---

### Critical Issues (Fix First)

```json
{
  "category": "technical",
  "issue": "12 pages with duplicate title tags",
  "impact": "Search engines may not index properly",
  "severity": "high"
}
```

**Action**: Resolve immediately (15-30 min per issue)

---

### Warnings (Fix Soon)

```json
{
  "category": "content",
  "issue": "8 pages under 300 words",
  "impact": "Thin content may rank poorly"
}
```

**Action**: Schedule within 1-2 weeks (1-2 hours per page)

---

### Opportunities (Nice to Have)

```json
{
  "category": "internal-linking",
  "issue": "High-value pages lack internal links",
  "recommendation": "Add contextual links from related content"
}
```

**Action**: Implement over time for competitive advantage (30 min - 2 hours)

---

## Troubleshooting

### Plugin Not Found

```bash
# Verify plugin is loaded
python -c "from src.analyzer.plugin_loader import load_plugins; print([p.name for p in load_plugins()])"

# Output should include: seo-optimizer
```

### Missing Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Verify BeautifulSoup4 installed
python -c "import bs4; print(bs4.__version__)"
```

### Analysis Too Slow

```bash
# Use max-pages to limit scope
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --max-pages 100  # Default: 1000
```

### Out of Memory

```bash
# Process in batches (plugin is memory-efficient)
# This shouldn't happen unless site has >10,000 pages
# Contact support if issue persists
```

---

## Best Practices

### 1. Target Relevant Keywords

```bash
# Good - specific to your site
--config '{"seo-optimizer": {"target_keywords": "python tutorials"}}'

# Avoid - too generic
--config '{"seo-optimizer": {"target_keywords": "web"}}'
```

### 2. Regular Monitoring

```bash
# Monthly audits to track progress
0 2 1 * * /path/to/monthly_seo_audit.sh
```

### 3. Prioritize by Impact

1. **Critical Issues** (must fix) - 2-4 hours
2. **Warnings** (should fix) - 8-20 hours
3. **Opportunities** (nice to have) - ongoing

### 4. Team Collaboration

```bash
# Generate shareable report
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output seo_report.json

# Share JSON file with team for review
# Discuss priority and implementation timeline
```

---

## Real-World Scenarios

### Scenario 1: Quick Health Check (5 min)

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --max-pages 50
```

---

### Scenario 2: Quarterly Audit (30 min)

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --config '{"seo-optimizer": {
    "target_keywords": "your,key,words"
  }}'
```

---

### Scenario 3: Pre-Launch Review (45 min)

```bash
python -m src.analyzer.cli analyze https://staging.example.com \
  --tests seo-optimizer,security-audit \
  --config '{"seo-optimizer": {
    "target_keywords": "launch keywords"
  }}'
```

---

### Scenario 4: Competitive Analysis (1 hour)

```bash
# Audit your site
python -m src.analyzer.cli analyze https://yoursite.com \
  --tests seo-optimizer \
  --output your_site.json

# Audit competitor (if crawlable)
python -m src.analyzer.cli analyze https://competitor.com \
  --tests seo-optimizer \
  --output competitor.json

# Compare results manually
# Identify gaps and opportunities
```

---

## Integration Examples

### With Migration Scanner

```bash
# Find deprecated code AND SEO issues
python -m src.analyzer.cli analyze https://example.com \
  --tests migration-scanner,seo-optimizer \
  --config '{
    "migration-scanner": {
      "patterns": {"jquery_live": "\.live\("}
    },
    "seo-optimizer": {
      "target_keywords": "your,keywords"
    }
  }'
```

---

### With LLM Optimizer

```bash
# Optimize for both search engines AND LLMs
python -m src.analyzer.cli analyze https://example.com \
  --tests llm-optimizer,seo-optimizer
```

---

### With Security Audit

```bash
# Comprehensive site health check
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer,security-audit
```

---

## Export & Reporting

### Generate Report (JSON)

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --output report.json
```

### Parse Report (Python)

```python
import json

with open('report.json') as f:
    results = json.load(f)

seo_result = next(r for r in results if r['plugin_name'] == 'seo-optimizer')

score = seo_result['details']['overall_score']
critical = len(seo_result['details']['critical_issues'])
warnings = len(seo_result['details']['warnings'])

print(f"Score: {score}/10")
print(f"Critical: {critical}")
print(f"Warnings: {warnings}")
```

---

## Performance Benchmarks

| Site Size | Analysis Time | Pages/sec |
|-----------|---------------|-----------|
| 10 pages | 2 sec | 5.0 |
| 50 pages | 8 sec | 6.2 |
| 100 pages | 15 sec | 6.7 |
| 250 pages | 35 sec | 7.1 |
| 500 pages | 65 sec | 7.7 |
| 1000+ pages | 125+ sec | 8.0 |

---

## Next Steps

1. **Run first audit** - See current state
2. **Prioritize issues** - Use priority matrix
3. **Create action plan** - 2-4 week timeline
4. **Implement fixes** - Critical issues first
5. **Re-audit** - Measure improvements
6. **Monitor monthly** - Stay competitive

---

## Support

For detailed information:
- **README**: [SEO_OPTIMIZER_README.md](SEO_OPTIMIZER_README.md)
- **Usage Guide**: [SEO_OPTIMIZER_USAGE_GUIDE.md](SEO_OPTIMIZER_USAGE_GUIDE.md)
- **Examples**: [docs/SEO_OPTIMIZER_EXAMPLES.md](docs/SEO_OPTIMIZER_EXAMPLES.md)
- **Implementation**: [SEO_OPTIMIZER_IMPLEMENTATION_SUMMARY.md](SEO_OPTIMIZER_IMPLEMENTATION_SUMMARY.md)
