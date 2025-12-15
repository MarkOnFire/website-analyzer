# LLM Optimizer Plugin Documentation

## Overview

The **LLM Optimizer** test plugin analyzes websites to identify opportunities for making them more discoverable and useful in Large Language Model (LLM) contexts. It evaluates site structure, metadata, content organization, and semantic markup to provide actionable recommendations.

## Purpose

As LLMs become primary information discovery tools, websites need to be optimized for:
- **Discoverability**: Ensuring LLMs can easily find and index relevant content
- **Usefulness**: Providing structured context that helps LLMs understand content relationships
- **Clarity**: Organizing information in ways LLMs can efficiently process and summarize
- **Completeness**: Including metadata that enables accurate content understanding

## What Gets Analyzed

### 1. Meta Tags
- **Title Tags**: Every page should have a unique, descriptive title (50-60 characters optimal)
- **Meta Descriptions**: Critical for LLM summarization (50-160 characters recommended)
- **Open Graph Tags**: Enable rich previews in LLM contexts
- **Twitter Cards**: Improve content representation across platforms
- **Keywords Meta Tag**: Helps LLMs understand primary topics

### 2. Schema Markup
- **Schema.org Detection**: Checks for JSON-LD structured data
- **Content Types**: Identifies Article, Product, Organization, Event, etc.
- **Relationship Clarity**: Evaluates whether content relationships are explicit

### 3. Content Hierarchy
- **Heading Structure**: Validates H1 → H2 → H3 hierarchy
- **Semantic HTML**: Checks for proper use of structural elements
- **Content Scannability**: Ensures pages are easy to parse visually and programmatically
- **Content Depth**: Evaluates minimum content length for substantial pages (200+ words)

### 4. Link Structure
- **Internal Navigation**: Analyzes how well pages are interconnected
- **Link Text Quality**: Checks that link anchors are descriptive
- **Navigation Patterns**: Identifies breadcrumbs and navigation hierarchy

## Output Format

The plugin returns results with:

### Overall Score (0-10)
- **9-10**: Excellent LLM optimization
- **7-8**: Good optimization with room for improvement
- **5-6**: Moderate optimization; several issues to address
- **0-4**: Poor optimization; significant work needed

### Quick Wins
Immediate, high-impact items that can be fixed quickly:
- Missing meta descriptions
- Missing page titles
- Pages lacking schema markup
- Poor heading hierarchy

Each quick win includes:
- **Priority**: high, medium, or low
- **Category**: Type of issue (meta-tags, schema-markup, etc.)
- **Issue**: Problem description with count
- **Impact**: Why it matters for LLMs
- **Fix**: Specific action to take
- **Affected URLs**: List of pages with this issue (up to 10 shown)

### Strategic Recommendations
Longer-term, structural improvements:
- Content restructuring needs
- Navigation improvements
- Metadata strategy updates
- Mobile/responsive considerations

Each recommendation includes:
- **Category**: Type of change
- **Finding**: Current state analysis
- **Recommendation**: Proposed solution
- **Effort**: low, medium, or high
- **Impact**: Potential improvement value
- **Affected Pages**: Count of pages impacted

### Metrics
Aggregate statistics across all pages:
- Average title length
- Average description length
- Pages missing descriptions
- Pages missing titles
- Pages without schema markup
- Pages with poor heading hierarchy
- Pages with thin content

## Usage

### Running LLM Optimizer from CLI

```bash
# Basic scan
python -m src.analyzer.cli analyze --url https://example.com --test llm-optimizer

# Scan specific project
python -m src.analyzer.cli analyze --slug example-com --test llm-optimizer

# Scan with custom limits
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --max-pages 500

# Output to specific format
python -m src.analyzer.cli analyze \
  --url https://example.com \
  --test llm-optimizer \
  --output results.json \
  --format json
```

### Running from MCP

If using the MCP server for Claude integration:

```
User: "Analyze my website at https://example.com for LLM optimization"

Claude will:
1. Use start_analysis MCP tool with test="llm-optimizer"
2. Monitor progress with check_status
3. Retrieve results with view_issues
4. Summarize findings and provide recommendations
```

## Interpreting Results

### Example: Missing Meta Descriptions

```json
{
  "priority": "high",
  "category": "meta-tags",
  "issue": "45 pages missing meta descriptions",
  "impact": "LLMs can't generate accurate summaries without description metadata",
  "fix": "Add descriptive meta tags to all content pages (50-160 characters recommended)",
  "affected_urls": [
    "https://example.com/page1",
    "https://example.com/page2",
    ...
  ]
}
```

**How to fix:**
1. Identify affected pages
2. Write unique 50-160 character descriptions for each
3. Add to `<head>` as: `<meta name="description" content="Your description">`
4. Re-run scan to verify improvement

### Example: Strategic Recommendation

```json
{
  "category": "content-structure",
  "finding": "32 pages have poor heading hierarchy (missing H2s or H3s)",
  "recommendation": "Restructure content with clear heading hierarchy (H1 → H2 → H3) to improve scannability for LLMs",
  "effort": "medium",
  "impact": "high",
  "affected_pages": 32
}
```

**Implementation strategy:**
1. Audit 3-5 representative pages
2. Restructure headings to follow H1 → H2 → H3 pattern
3. Apply template changes to similar content types
4. Test with markdown conversion to verify readability
5. Re-run scan to measure improvement

## Best Practices

### For Maximum LLM Utility

1. **Unique Titles & Descriptions**
   - Every page should have unique metadata
   - Don't use template text like "Welcome to my site"
   - Include primary keywords naturally

2. **Clear Heading Hierarchy**
   ```html
   <h1>Main Topic</h1>
   <h2>Subtopic A</h2>
   <h3>Detail for Subtopic A</h3>
   <h2>Subtopic B</h2>
   <h3>Detail for Subtopic B</h3>
   ```

3. **Structured Data**
   ```html
   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@type": "Article",
     "headline": "Article Headline",
     "description": "Article summary",
     "author": "Author Name"
   }
   </script>
   ```

4. **Content Length**
   - Aim for 300+ words for substantive content
   - Minimum 200 words for utility pages
   - Shorter content acceptable for index/directory pages

5. **Internal Navigation**
   - Link related content with descriptive anchor text
   - Use breadcrumbs for hierarchy
   - Create topic clusters with hub pages

### Open Graph for LLM Context

```html
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Page description">
<meta property="og:type" content="article">
<meta property="og:url" content="https://example.com/page">
<meta property="og:image" content="https://example.com/image.jpg">
```

### Schema.org Markup Examples

**Article:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "description": "Short summary",
  "author": {"@type": "Person", "name": "Author Name"},
  "datePublished": "2025-01-15",
  "dateModified": "2025-01-15"
}
```

**Blog Post:**
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Blog Post Title",
  "description": "Post summary",
  "author": {"@type": "Person", "name": "Author Name"},
  "datePublished": "2025-01-15",
  "articleBody": "Main content here..."
}
```

**Product:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "Product description",
  "brand": "Brand Name",
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "USD"
  }
}
```

## Scoring Methodology

The overall score (0-10) is calculated as follows:

```
Score = 10.0

# Deductions:
- Missing descriptions: -3 points × (missing_ratio)
- Missing titles: -2 points × (missing_ratio)
- Missing schema: -2 points × (missing_ratio)
- Poor headings: -1.5 points × (poor_ratio)
- Thin content: -1 point × (thin_ratio)

# Final score clamped to 0-10 range
```

**Example:** A site with:
- 50% pages missing descriptions: -1.5 points
- 10% pages missing titles: -0.2 points
- 70% without schema: -1.4 points
- 20% poor headings: -0.3 points
- 15% thin content: -0.15 points

**Final Score: 10 - 3.55 = 6.45** (warning status, room for improvement)

## Re-running and Tracking Progress

After implementing recommendations:

```bash
# Re-run the same project
python -m src.analyzer.cli analyze --slug example-com --test llm-optimizer

# Compare results
python -m src.analyzer.cli view-issues --project example-com --test llm-optimizer

# See improvement over time
python -m src.analyzer.cli view-issues \
  --project example-com \
  --test llm-optimizer \
  --status all
```

Score improvements indicate successful implementation:
- **6.5 → 7.5**: Quick wins fixed, good progress
- **7.5 → 8.5**: Most metadata issues resolved
- **8.5 → 9.5**: Excellent optimization achieved

## Technical Details

### Plugin Name
`llm-optimizer`

### Performance
- Typically completes in < 2 seconds per 100 pages
- Analyzes HTML structure, not page rendering
- No external API calls required

### Limitations
- Does not render JavaScript (uses static HTML analysis)
- Does not validate schema markup correctness, only presence
- Does not check for actual LLM discoverability (would require LLM queries)
- Meta description length is approximate (character-based, not pixel-based)

### Future Enhancements
- Query-based testing: Generate LLM queries to test actual discoverability
- Visual hierarchy analysis: Evaluate content placement and emphasis
- Accessibility scoring: Check alt text, ARIA labels, semantic markup
- Mobile optimization: Analyze responsive design effectiveness
- Competitive analysis: Compare optimization against top competitors

## Related Tests

- **Migration Scanner**: Finds deprecated code patterns
- **SEO Optimizer**: Optimizes for search engine visibility
- **Security Audit**: Identifies security vulnerabilities

## Support and Feedback

For issues, improvements, or feature requests related to the LLM Optimizer:
1. Check existing project issues for similar problems
2. Run the analyzer in verbose mode for detailed output
3. Review the design specification in `docs/design.md`
4. Consult the main CLI help: `python -m src.analyzer.cli analyze --help`
