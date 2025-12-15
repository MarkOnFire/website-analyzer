# LLM Optimizer - Quick Start Guide

## Installation & Verification

### 1. Verify Plugin Installation
```bash
# Check that the plugin loads
python3 -c "
from src.analyzer.plugins.llm_optimizer import LLMOptimizer
p = LLMOptimizer()
print(f'✓ Plugin loaded: {p.name}')
print(f'✓ Description: {p.description}')
"
```

Expected output:
```
✓ Plugin loaded: llm-optimizer
✓ Description: Analyze site for LLM discoverability and optimization
```

### 2. Verify Plugin Discovery
```bash
# Check that plugin is discovered by loader
python3 -c "
from src.analyzer.plugin_loader import load_plugins
plugins = load_plugins()
names = [p.name for p in plugins]
print(f'✓ Found {len(plugins)} plugin(s): {names}')
"
```

Expected output:
```
✓ Found 2 plugin(s): ['llm-optimizer', 'migration-scanner']
```

## Basic Usage

### Analyze a Website
```bash
# Analyze your website
python -m src.analyzer.cli analyze \
  --url https://your-website.com \
  --test llm-optimizer
```

### Analyze Existing Project
```bash
# Analyze a previously crawled project
python -m src.analyzer.cli analyze \
  --slug your-website-com \
  --test llm-optimizer
```

### Save Results to File
```bash
# Save JSON results
python -m src.analyzer.cli analyze \
  --url https://your-website.com \
  --test llm-optimizer \
  --output results.json \
  --format json
```

## Understanding the Score

The LLM Optimizer produces a **0-10 score**:

- **9-10**: Excellent - Your site is highly optimized for LLMs
- **7-8**: Good - Solid optimization with minor improvements needed
- **5-6**: Warning - Significant optimization opportunities exist
- **0-4**: Fail - Critical issues need immediate attention

## Understanding Quick Wins

Quick Wins are **high-priority, easily fixable** issues:

### Example: Missing Meta Descriptions
```json
{
  "priority": "high",
  "category": "meta-tags",
  "issue": "45 pages missing meta descriptions",
  "impact": "LLMs can't generate accurate summaries",
  "fix": "Add descriptive meta tags (50-160 characters)",
  "affected_urls": ["page1", "page2", ...]
}
```

**How to fix**: Add to your page `<head>`:
```html
<meta name="description" content="Brief, meaningful description of page content">
```

### Example: Missing Schema Markup
```json
{
  "priority": "medium",
  "category": "schema-markup",
  "issue": "Blog posts lack Article schema",
  "impact": "Content relationships unclear to LLMs",
  "fix": "Add schema.org/Article markup",
  "affected_urls": ["blog/*"]
}
```

**How to fix**: Add before closing `</head>`:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "description": "Article summary",
  "author": "Author Name"
}
</script>
```

## Understanding Strategic Recommendations

Strategic Recommendations are **longer-term structural improvements**:

### Example: Poor Heading Hierarchy
```json
{
  "category": "content-structure",
  "finding": "32 pages have poor heading hierarchy",
  "recommendation": "Restructure with H1 → H2 → H3 pattern",
  "effort": "medium",
  "impact": "high",
  "affected_pages": 32
}
```

**Implementation strategy**:
1. Audit 3-5 representative pages
2. Restructure headings to follow proper hierarchy
3. Apply template changes across similar pages
4. Test with markdown conversion for readability

## Interpreting Output

### Score Breakdown
The score is calculated by deducting points for issues:
- Missing descriptions: -3 per 100%
- Missing titles: -2 per 100%
- Missing schema: -2 per 100%
- Poor headings: -1.5 per 100%
- Thin content: -1 per 100%

**Example**: If 50% of pages lack descriptions:
```
10.0 (base) - 1.5 (50% × -3) = 8.5 score
```

### Metrics Understanding
```json
{
  "metrics": {
    "avg_title_length": 58.2,          // Character count (optimal: 50-60)
    "avg_description_length": 155.8,   // Character count (optimal: 50-160)
    "pages_missing_description": 2,    // Count of pages without description
    "pages_missing_title": 0,          // Count of pages without title
    "pages_without_schema": 18,        // Count of pages without schema markup
    "pages_with_poor_headings": 3,     // Count with bad H1-H2-H3 structure
    "pages_with_short_content": 5      // Count with < 200 words
  }
}
```

## Best Practices

### Meta Tags
- **Title**: Unique for each page, 50-60 characters
- **Description**: Unique for each page, 50-160 characters
- **OG Image**: Include for social sharing

Example:
```html
<title>Product Name - Best Features - Your Company</title>
<meta name="description" content="Discover our innovative product with advanced features designed for your needs.">
<meta property="og:image" content="https://yoursite.com/product-image.jpg">
```

### Content Hierarchy
Always follow this structure:
```html
<h1>Main Topic (one per page)</h1>

<h2>Major Section 1</h2>
<h3>Subsection A</h3>
<p>Content...</p>

<h2>Major Section 2</h2>
<h3>Subsection B</h3>
<p>Content...</p>
```

### Schema.org Markup
Add appropriate type for your content:
```html
<!-- For articles -->
<script type="application/ld+json">
{
  "@type": "Article",
  "headline": "Title",
  "datePublished": "2025-01-15",
  "author": {"@type": "Person", "name": "Author"}
}
</script>

<!-- For products -->
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Product Name",
  "description": "Product description",
  "price": "99.99",
  "priceCurrency": "USD"
}
</script>

<!-- For organizational info -->
<script type="application/ld+json">
{
  "@type": "Organization",
  "name": "Your Company",
  "url": "https://yoursite.com",
  "logo": "https://yoursite.com/logo.png"
}
</script>
```

## Tracking Progress

### First Analysis (Baseline)
```bash
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --output baseline.json
```

Make improvements...

### Second Analysis (Verification)
```bash
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --output after-improvements.json
```

### Compare Results
```bash
python3 << 'EOF'
import json

with open('baseline.json') as f:
    baseline = json.load(f)[0]

with open('after-improvements.json') as f:
    after = json.load(f)[0]

baseline_score = baseline['details']['overall_score']
after_score = after['details']['overall_score']
improvement = after_score - baseline_score

print(f"Before: {baseline_score:.1f}/10")
print(f"After: {after_score:.1f}/10")
print(f"Improvement: +{improvement:.1f} points")
EOF
```

## Common Scenarios

### E-commerce Product Pages
**Common issues**: Missing product schema, no descriptions

**Fix approach**:
1. Add Product schema with price and availability
2. Create unique description for each product
3. Ensure proper heading hierarchy (H1 product name, H2 sections)

### Blog Posts
**Common issues**: Missing Article schema, no publish dates

**Fix approach**:
1. Add Article schema with datePublished
2. Include author information
3. Add descriptive meta description (key topic summary)

### Documentation Sites
**Common issues**: Missing breadcrumb schema, no descriptions

**Fix approach**:
1. Add BreadcrumbList schema for navigation
2. Generate description from first paragraph
3. Ensure consistent heading structure across doc types

## Command Reference

```bash
# Basic analysis
python -m src.analyzer.cli analyze --url <URL> --test llm-optimizer

# Options
--slug <slug>              # Use existing project
--max-pages <number>       # Limit pages to analyze
--output <filename>        # Save results to file
--format json             # Output format
--snapshot <timestamp>    # Use specific snapshot (existing projects)

# Examples
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --max-pages 100 \
  --output report.json

python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --output results.json \
  --format json
```

## Next Steps

1. **Run your first analysis**
   ```bash
   python -m src.analyzer.cli analyze --url YOUR_SITE --test llm-optimizer
   ```

2. **Review the score** (0-10 scale)

3. **Identify quick wins** (high-priority fixes)

4. **Implement recommendations** in order of priority

5. **Re-run analysis** to verify improvements

6. **Track progress** over time

## Additional Resources

- **User Guide**: `docs/LLM_OPTIMIZER_README.md`
- **Examples**: `docs/LLM_OPTIMIZER_EXAMPLES.md`
- **Implementation Details**: `docs/LLM_OPTIMIZER_IMPLEMENTATION.md`
- **Design Spec**: `docs/design.md` (lines 176-238)

## Support

For issues or questions:
1. Check the comprehensive README: `docs/LLM_OPTIMIZER_README.md`
2. Review real-world examples: `docs/LLM_OPTIMIZER_EXAMPLES.md`
3. Check implementation guide: `docs/LLM_OPTIMIZER_IMPLEMENTATION.md`
4. Run tests to verify your environment: `python tests/test_llm_optimizer.py`

---

**Ready to optimize your site for LLMs!**

The LLM Optimizer helps you:
- ✓ Improve discoverability in LLM contexts
- ✓ Make content more useful to AI systems
- ✓ Track optimization progress over time
- ✓ Get actionable recommendations

Start with: `python -m src.analyzer.cli analyze --url YOUR_SITE --test llm-optimizer`
