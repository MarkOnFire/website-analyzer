# LLM Optimizer Plugin - Examples and Use Cases

## Example 1: Test Site Analysis

### Input
Website: https://example.com (test site with 1 page)

### Command
```bash
python -m src.analyzer.cli analyze \
  --slug example-com \
  --test llm-optimizer \
  --format json
```

### Output
```json
{
  "plugin_name": "llm-optimizer",
  "timestamp": "2025-12-12T18:30:45Z",
  "status": "fail",
  "summary": "LLM Optimization Score: 2.5/10 - Found 2 quick wins and 2 strategic recommendations",
  "details": {
    "overall_score": 2.5,
    "pages_analyzed": 1,
    "quick_wins": [
      {
        "priority": "high",
        "category": "meta-tags",
        "issue": "1 pages missing meta descriptions",
        "impact": "LLMs can't generate accurate summaries without description metadata",
        "fix": "Add descriptive meta tags to all content pages (50-160 characters recommended)",
        "affected_urls": ["https://example.com/external"]
      },
      {
        "priority": "medium",
        "category": "schema-markup",
        "issue": "1 pages lack schema.org markup",
        "impact": "Content relationships unclear to LLMs; harder to extract structured data",
        "fix": "Add schema.org markup (Article, Product, Organization, etc.) to relevant pages",
        "affected_urls": ["https://example.com/external"]
      }
    ],
    "strategic_recommendations": [
      {
        "category": "content-structure",
        "finding": "1 pages have poor heading hierarchy (missing H2s or H3s)",
        "recommendation": "Restructure content with clear heading hierarchy (H1 → H2 → H3) to improve scannability for LLMs",
        "effort": "medium",
        "impact": "high",
        "affected_pages": 1
      },
      {
        "category": "content-depth",
        "finding": "1 content pages have fewer than 200 words",
        "recommendation": "Expand content with more detailed information, key points, and context",
        "effort": "medium",
        "impact": "high",
        "affected_pages": 1
      }
    ],
    "metrics": {
      "avg_title_length": 14.0,
      "avg_description_length": 0,
      "pages_missing_description": 1,
      "pages_missing_title": 0,
      "pages_without_schema": 1,
      "pages_with_poor_headings": 1,
      "pages_with_short_content": 1
    }
  }
}
```

### Interpretation

The site has a **score of 2.5/10** (FAIL), indicating significant optimization opportunities:

1. **Missing Meta Descriptions** (High Priority)
   - 1 page lacks a meta description
   - **Action:** Add description like: `<meta name="description" content="Brief, meaningful summary of page content">`

2. **Missing Schema Markup** (Medium Priority)
   - No schema.org JSON-LD found
   - **Action:** Add Article schema or appropriate content type

3. **Poor Heading Hierarchy** (Strategic)
   - Page doesn't follow H1 → H2 → H3 structure
   - **Action:** Restructure HTML headings

4. **Thin Content** (Strategic)
   - Page has < 200 words
   - **Action:** Expand with more substantive content

## Example 2: Well-Optimized Site (Hypothetical)

If a site were well-optimized, results would look like:

```json
{
  "status": "pass",
  "summary": "LLM Optimization Score: 8.5/10 - Found 0 quick wins and 1 strategic recommendation",
  "details": {
    "overall_score": 8.5,
    "pages_analyzed": 250,
    "quick_wins": [],
    "strategic_recommendations": [
      {
        "category": "content-structure",
        "finding": "15 product pages lack detailed specifications",
        "recommendation": "Enhance product descriptions with detailed specs, materials, dimensions in structured format",
        "effort": "medium",
        "impact": "medium",
        "affected_pages": 15
      }
    ],
    "metrics": {
      "avg_title_length": 58.2,
      "avg_description_length": 155.8,
      "pages_missing_description": 2,
      "pages_missing_title": 0,
      "pages_without_schema": 18,
      "pages_with_poor_headings": 3,
      "pages_with_short_content": 5
    }
  }
}
```

### What This Indicates

- **8.5/10 score**: Excellent LLM optimization foundation
- **Zero quick wins**: All critical metadata present
- **Average title length (58.2 chars)**: Optimal for LLM processing
- **Average description length (155.8 chars)**: Well within recommended range (50-160)
- **Only 2 pages missing descriptions**: Acceptable minor issues
- **18 pages without schema**: Opportunity for improvement

## Example 3: E-commerce Site Analysis

### Scenario
A 500-page e-commerce site analyzing product pages, category pages, and blog content.

### Expected Issues and Fixes

#### Quick Win: Product Pages Missing Schema
```
Issue: "285 product pages lack schema.org markup"
Fix: Add structured Product schema to all product pages

Before:
<h1>Widget Pro - Best-Selling Widget</h1>
<p>Price: $99.99</p>

After:
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Widget Pro",
  "description": "Best-selling widget with advanced features",
  "brand": "WidgetCorp",
  "price": "99.99",
  "priceCurrency": "USD",
  "offers": {
    "@type": "Offer",
    "availability": "https://schema.org/InStock",
    "price": "99.99",
    "priceCurrency": "USD"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "89"
  }
}
</script>
```

#### Quick Win: Blog Pages Missing Descriptions
```
Issue: "42 blog post pages missing meta descriptions"
Fix: Generate unique descriptions for each blog post

For each post:
<meta name="description" content="Brief summary of the article topic and key takeaway (50-160 chars)">
```

#### Strategic Recommendation: Category Page Navigation
```
Finding: "Complex nested categories lack clear breadcrumb navigation"
Recommendation: "Implement breadcrumb navigation and improve internal linking"

Expected improvement:
- LLMs better understand site structure
- Content relationships become explicit
- Improved crawlability and indexing
```

## Example 4: News/Publishing Site

### Analysis Results

```json
{
  "overall_score": 6.2,
  "quick_wins": [
    {
      "priority": "high",
      "category": "meta-tags",
      "issue": "67 articles missing author information in schema",
      "impact": "LLMs cannot attribute content properly",
      "fix": "Add author field to Article schema on all pieces"
    },
    {
      "priority": "high",
      "category": "schema-markup",
      "issue": "100% of articles missing datePublished/dateModified",
      "impact": "Cannot determine content currency and freshness",
      "fix": "Include ISO 8601 dates in Article schema"
    }
  ],
  "strategic_recommendations": [
    {
      "category": "content-structure",
      "finding": "Article summaries buried in body text",
      "recommendation": "Add structured summary section right after headline",
      "effort": "medium",
      "impact": "high"
    }
  ]
}
```

### Implementation Steps

1. **Add DatePublished to Articles**
```html
<script type="application/ld+json">
{
  "@type": "NewsArticle",
  "headline": "Article Title",
  "description": "Article summary",
  "author": [
    {
      "@type": "Person",
      "name": "Author Name"
    }
  ],
  "datePublished": "2025-01-15T10:00:00Z",
  "dateModified": "2025-01-16T14:30:00Z",
  "publisher": {
    "@type": "Organization",
    "name": "Publication Name",
    "logo": "logo.png"
  }
}
</script>
```

2. **Improve Article Summaries**
```html
<article>
  <h1>Article Title</h1>
  <div class="summary" role="doc-summary">
    <p>Clear, concise summary that captures key points...</p>
  </div>
  <h2>Main Section</h2>
  <p>Detailed content...</p>
</article>
```

## Example 5: Documentation Site

### Analysis
A technical documentation site with 1000+ pages.

### Common Issues Found

```json
{
  "overall_score": 7.1,
  "quick_wins": [
    {
      "priority": "high",
      "issue": "412 doc pages missing meta descriptions",
      "affected_urls": 412
    },
    {
      "priority": "medium",
      "issue": "Documentation lacks BreadcrumbList schema",
      "affected_urls": 1000
    }
  ]
}
```

### Recommended Fixes

1. **Generate Descriptions from First Paragraph**
```
For each doc page, create description from intro paragraph:
- Extract first 50-160 characters
- Include key terms naturally
- Avoid duplication
```

2. **Add BreadcrumbList Schema**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Documentation",
      "item": "https://docs.example.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Getting Started",
      "item": "https://docs.example.com/getting-started"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Installation",
      "item": "https://docs.example.com/getting-started/installation"
    }
  ]
}
</script>
```

## Scoring Progression Example

### Initial Scan
```
- Score: 3.5/10 (FAIL)
- Main issues: No metadata, no schema, poor structure
```

### After Quick Wins (1-2 weeks)
```
- Score: 5.8/10 (WARNING)
- Fixed: Meta descriptions, page titles
- Remaining: Schema markup, content expansion
```

### After Strategic Work (3-4 weeks)
```
- Score: 7.5/10 (PASS)
- Fixed: Added schema, improved headings
- Remaining: Content optimization, edge cases
```

### Optimization Complete
```
- Score: 8.8/10 (EXCELLENT)
- All quick wins resolved
- Minor improvements only (competitor benchmarking)
```

## Running Multiple Tests in Sequence

```bash
# Baseline measurement
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --output baseline.json

# Implement fixes...

# Verify improvements
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --output after-fixes.json

# Compare scores
python3 << 'EOF'
import json

with open('baseline.json') as f:
    baseline = json.load(f)[0]

with open('after-fixes.json') as f:
    after = json.load(f)[0]

baseline_score = baseline['details']['overall_score']
after_score = after['details']['overall_score']
improvement = after_score - baseline_score

print(f"Baseline Score: {baseline_score}/10")
print(f"Current Score: {after_score}/10")
print(f"Improvement: +{improvement:.1f} points")
EOF
```

## Integration with Claude

### Example Conversation

**User:** "Analyze my website's LLM optimization. It's at https://mysite.com"

**Claude:** (using MCP tools)
1. Calls `start_analysis` with test="llm-optimizer"
2. Waits for completion with `check_status`
3. Retrieves results with `view_issues`

**Claude's Response:**
```
I've analyzed your website for LLM optimization. Here are the key findings:

**Score: 5.2/10** - There's significant room for improvement.

**Immediate Priorities:**
1. Add meta descriptions to 45 pages (HIGH) - This is the single biggest improvement you can make
2. Implement schema.org markup on product pages (MEDIUM) - Helps LLMs understand product details

**Strategic Improvements:**
- Restructure your blog content with better heading hierarchy
- Ensure all main content pages have 300+ words of substantive content

**Expected impact:** Following these recommendations could improve your score to 7.5+ in 2-3 weeks.

Want me to show you specific examples of how to implement any of these fixes?
```

## CLI Options

```bash
# Basic analysis
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer

# Specify project to update existing
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer

# Limit pages scanned
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --max-pages 100

# Output to file
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --output results.json \
  --format json

# Run alongside other tests
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --test migration-scanner \
  --output report.json

# Compare with previous run
python -m src.analyzer.cli analyze \
  --slug my-site \
  --test llm-optimizer \
  --snapshot 2025-01-15T10-30-00Z  # Use specific snapshot
```

## Performance Notes

- **1 page**: < 1 second
- **100 pages**: 2-3 seconds
- **500 pages**: 8-12 seconds
- **1000+ pages**: 15-25 seconds

Analysis scales linearly with page count; no external API calls required.
