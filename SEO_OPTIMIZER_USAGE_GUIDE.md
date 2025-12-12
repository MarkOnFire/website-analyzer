# SEO Optimizer - Quick Start Guide

## Overview

The SEO Optimizer plugin analyzes websites for search engine optimization opportunities across three dimensions:

1. **Technical SEO**: Meta tags, heading structure, images, links, robots.txt, sitemap
2. **Content SEO**: Word count, keyword usage, internal linking, duplicate detection
3. **Overall Scoring**: 0-10 scale with categorized findings

## Quick Examples

### Example 1: Basic SEO Audit

Run a standard SEO analysis on any website:

```bash
# Analyze a site
python -m src.analyzer.runner seo-optimizer https://example.com

# The plugin will:
# - Crawl all pages
# - Check technical SEO elements
# - Analyze content quality
# - Generate a comprehensive report
```

### Example 2: Keyword-Focused Analysis

Optimize content for specific keywords:

```bash
python -m src.analyzer.runner seo-optimizer https://example.com \
  --target-keywords "python tutorial,web development,REST API"

# The plugin will:
# - Track keyword usage across pages
# - Identify pages missing target keywords
# - Suggest where to add keywords naturally
# - Measure keyword density (2% optimal)
```

### Example 3: Interpret Results

A sample output from a 50-page site:

```json
{
  "overall_score": 6.8,
  "critical_issues": [
    {
      "category": "technical",
      "issue": "15 pages with duplicate title tags",
      "impact": "Search engines may not index properly",
      "affected_urls": 15,
      "severity": "high"
    }
  ],
  "warnings": [
    {
      "category": "content",
      "issue": "12 pages under 300 words",
      "impact": "Thin content may rank poorly",
      "affected_urls": 12
    },
    {
      "category": "technical",
      "issue": "28 pages missing meta descriptions",
      "impact": "Can't generate accurate search snippets",
      "affected_urls": 28
    }
  ],
  "opportunities": [
    {
      "category": "internal-linking",
      "issue": "8 high-traffic pages lack internal links",
      "recommendation": "Add contextual links from related content",
      "affected_urls": 8
    }
  ]
}
```

## Scoring Guide

| Score | Grade | Status | Action |
|-------|-------|--------|--------|
| 9.0-10.0 | A | Excellent | Maintain; implement minor opportunities |
| 8.0-8.9 | B+ | Very Good | Good foundation; fix any warnings |
| 7.0-7.9 | B | Good | Competitive; address warnings for improvement |
| 6.0-6.9 | C+ | Fair | Some improvements needed; fix critical issues first |
| 5.0-5.9 | C | Poor | Significant work required |
| Below 5.0 | F | Very Poor | Critical issues blocking proper indexing |

## Common Issues & Fixes

### Critical Issues (Fix Immediately)

**Missing Title Tags** (5 min per page)
```html
<!-- ✗ Bad -->
<head>
  <title></title>
</head>

<!-- ✓ Good -->
<head>
  <title>Python Tutorial - Learn Python Programming | Example</title>
</head>
```

**Duplicate Titles** (15-30 min)
- Use unique titles reflecting page content
- Include primary keyword for each page
- Example: Page 1 = "Beginners Guide", Page 2 = "Advanced Topics"

**Missing H1 Tags** (5 min per page)
```html
<!-- ✗ Bad -->
<body>
  <h2>Section Title</h2>
</body>

<!-- ✓ Good -->
<body>
  <h1>Main Page Topic</h1>
  <h2>Section Title</h2>
</body>
```

### Warnings (Fix Soon)

**Thin Content** (30 min - 2 hours per page)
- Expand pages under 300 words
- Add value through examples, guides, references
- Target 1,500-2,500 words for comprehensive guides

**Missing Meta Descriptions** (5 min per page)
```html
<!-- ✓ Good -->
<head>
  <meta name="description"
    content="Learn Python programming with hands-on examples.
    Complete guide from basics to advanced concepts.
    Free tutorials and best practices.">
</head>
```

**Missing Alt Text** (2 min per image)
```html
<!-- ✗ Bad -->
<img src="logo.png">

<!-- ✓ Good -->
<img src="logo.png" alt="Python programming language logo">
```

### Opportunities (Nice to Have)

**Broken Heading Hierarchy**
- Fix: Ensure H1 → H2 → H3 progression
- Don't skip levels (H1 → H3 is broken)

**Missing Internal Links**
- Add contextual links to related pages
- Link high-authority pages to new/important pages
- Use descriptive anchor text

**Duplicate Content**
- Use canonical tags if intentional
- Consolidate near-duplicate pages
- Use robots.txt to manage crawl budget

## Implementation Priority Matrix

```
                    Effort
                Low    Medium   High
          ┌─────────┬─────────┬──────┐
High      │ URGENT  │ PLAN    │ PLAN │
Impact    │ Missing │ Duplicate│Restructure
          │ Meta    │ Content │
          ├─────────┼─────────┼──────┤
Medium    │ QUICK   │ IMPROVE │ NICE │
Impact    │ Alt     │ Hierarchy│ To   │
          │ Text    │         │ Have │
          ├─────────┼─────────┼──────┤
Low       │ POLISH  │ NICE    │SKIP  │
Impact    │ External│ To Have │      │
          │ Links   │         │      │
          └─────────┴─────────┴──────┘
```

## Testing Your Improvements

### Before & After Comparison

1. **Initial Scan**
   ```bash
   python -m src.analyzer.runner seo-optimizer \
     https://example.com --output initial_audit.json
   ```

2. **Make Improvements**
   - Add missing meta descriptions
   - Expand thin content
   - Fix duplicate titles
   - Add alt text to images

3. **Rescan**
   ```bash
   python -m src.analyzer.runner seo-optimizer \
     https://example.com --output final_audit.json
   ```

4. **Compare Results**
   ```bash
   # Score improvement: Initial 5.8 → Final 7.2 (+1.4 points)
   # Critical issues: 15 → 0 (100% resolved)
   # Warnings: 28 → 12 (57% improved)
   ```

## Configuration Reference

### Target Keywords

```python
# Single keyword
"target_keywords": "python tutorial"

# Multiple keywords (array)
"target_keywords": ["python tutorial", "web development", "REST API"]

# Multiple keywords (comma-separated)
"target_keywords": "python tutorial,web development,REST API"
```

### Customizing Thresholds

Edit `src/analyzer/plugins/seo_optimizer.py`:

```python
class SeoOptimizer(TestPlugin):
    # Modify these constants
    MIN_CONTENT_LENGTH = 300  # Increase to 500 for stricter content rules
    MIN_TITLE_LENGTH = 30     # Minimum title length
    MAX_TITLE_LENGTH = 60     # Maximum title length (truncated in search)
    MIN_META_DESC_LENGTH = 120
    MAX_META_DESC_LENGTH = 160
```

## Integration with Search Tools

### Google Search Console

1. Identify critical issues in SEO report
2. Fix issues on your site
3. Submit "Inspect URL" in Google Search Console
4. Request re-indexing for top pages
5. Monitor "Core Web Vitals" report

### Other Integrations

- **SEMrush**: Validate keyword difficulty for target keywords
- **Ahrefs**: Check backlink profile to understand authority
- **Screaming Frog**: Deep technical SEO audit
- **Lighthouse**: Performance and Core Web Vitals

## Best Practices

### Title Tags
- 30-60 characters (60 max before truncation)
- Include primary keyword
- Make compelling for CTR
- Avoid: Keyword stuffing, duplicate titles

### Meta Descriptions
- 120-160 characters
- Include CTA or value proposition
- Avoid: Duplicate descriptions, keyword stuffing

### Content
- Minimum 300 words (thin content warning)
- Optimal 1,500-2,500 words for comprehensive guides
- Target 2% keyword density (natural language)
- Use semantic HTML (H1-H6, strong, em)

### Images
- Add descriptive alt text to all images
- Use relevant filenames (my-image.jpg not IMG_1234.jpg)
- Include primary keywords naturally

### Links
- Add 3-5 internal links per page minimum
- Use descriptive anchor text
- Link to related, authoritative pages
- Check for broken links regularly

## Frequently Asked Questions

**Q: What's a good SEO score?**
A: 7.0+ is competitive; 8.0+ is excellent. Focus on critical issues first.

**Q: Should I target multiple keywords per page?**
A: 1-2 primary keywords per page. Use keyword variations naturally.

**Q: How often should I run SEO audits?**
A: Monthly for active sites, quarterly for maintenance mode sites.

**Q: Does content length alone guarantee rankings?**
A: No. Content must be high-quality, unique, and answer user intent.

**Q: What's the relationship between SEO score and rankings?**
A: Strong correlation but not deterministic. SEO score is one factor.

**Q: Can I automate SEO improvements?**
A: Yes for technical issues (meta tags, alt text). Content requires human creation.

## Next Steps

1. Run initial SEO audit
2. Review critical issues
3. Plan fixes using priority matrix
4. Implement improvements
5. Rescan and compare results
6. Share report with team/stakeholders
7. Set up monthly monitoring

## Support

For detailed information, see [SEO_OPTIMIZER_README.md](./SEO_OPTIMIZER_README.md)

## Tools Used

- **BeautifulSoup4**: HTML parsing
- **Asyncio**: Concurrent analysis
- **Regex**: Pattern matching for keywords
- **Pydantic**: Data validation and serialization
