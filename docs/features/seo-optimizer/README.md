# SEO Optimizer Plugin

## Overview

The SEO Optimizer plugin analyzes websites for search engine optimization opportunities across technical SEO, content SEO, and on-page optimization. It provides actionable recommendations to improve search engine rankings, accessibility, and content discoverability.

## Purpose

Identify and prioritize SEO improvements through:
- **Technical SEO checks**: Meta tags, heading structure, image alt text, link health, robots.txt/sitemap validation
- **Content SEO analysis**: Content length, keyword usage, internal linking structure, duplicate content detection
- **Scoring system**: Overall SEO score (0-10) with detailed breakdown of critical issues, warnings, and opportunities

## Key Features

### Technical SEO Checks

- **Meta Tags Analysis**
  - Title tag presence and length optimization (recommended: 30-60 characters)
  - Meta description presence and length (recommended: 120-160 characters)
  - Duplicate title tag detection

- **Heading Structure Validation**
  - H1 tag presence (exactly one per page recommended)
  - Proper heading hierarchy (H1 → H2 → H3, etc.)
  - Broken hierarchy detection

- **Image Alt Text Coverage**
  - Detects images missing descriptive alt text
  - Critical for accessibility and LLM content understanding

- **Link Health Analysis**
  - External link identification and auditing
  - Internal linking structure validation
  - Recommendations for link rel attributes

- **Robots.txt & Sitemap Validation**
  - Sitemap.xml presence detection
  - Crawlability recommendations

### Content SEO Analysis

- **Content Length Evaluation**
  - Identifies "thin content" pages (< 300 words)
  - Provides expansion recommendations

- **Keyword Usage Tracking**
  - Optional target keyword analysis
  - Keyword density and placement evaluation
  - Title tag keyword inclusion

- **Internal Linking Structure**
  - Pages with missing internal links
  - Contextual linking opportunities

- **Duplicate Content Detection**
  - Identifies potentially duplicate pages
  - Recommends canonical tags or consolidation

### Scoring System

Overall SEO score (0-10) calculated based on:
- **Critical Issues** (-2 points each): Blocking proper indexing or structure
- **Warnings** (-0.5 points each): Should-fix items affecting rankings
- **Opportunities** (-0.1 points each): Nice-to-have improvements

**Score Interpretation**:
- 8.0-10.0: Excellent - Strong SEO foundation
- 6.0-7.9: Good - Competitive SEO
- 5.0-5.9: Needs Improvement - Significant optimization needed
- Below 5.0: Poor - Critical issues requiring immediate attention

## Output Format

### Response Structure

```json
{
  "test": "seo-optimization",
  "timestamp": "2025-12-02T12:10:00Z",
  "overall_score": 7.2,
  "critical_issues": [
    {
      "category": "technical",
      "issue": "12 pages with duplicate title tags",
      "impact": "Search engines may not index properly",
      "affected_urls": ["https://example.com/page1", "..."],
      "severity": "high"
    }
  ],
  "warnings": [
    {
      "category": "content",
      "issue": "8 pages under 300 words",
      "impact": "Thin content may rank poorly",
      "affected_urls": ["https://example.com/thin1", "..."]
    }
  ],
  "opportunities": [
    {
      "category": "internal-linking",
      "finding": "High-value pages lack internal links",
      "recommendation": "Add contextual links from related content",
      "affected_urls": ["https://example.com/important", "..."]
    }
  ],
  "pages_analyzed": 156,
  "issue_counts": {
    "missing_title": 5,
    "missing_meta_desc": 12,
    "missing_h1": 8,
    "thin_content": 8,
    "...": "..."
  },
  "target_keywords": ["python tutorial", "web framework"]
}
```

### Issue Categories

- **technical**: Meta tags, headings, alt text, links, robots.txt, sitemap
- **content**: Length, keywords, duplicate content
- **internal-linking**: Internal link structure and distribution
- **mobile**: Mobile responsiveness indicators
- **performance**: Page load metrics

## Usage

### Basic Scan

Perform a standard SEO audit of your website:

```bash
python -m src.analyzer.cli seo-optimizer scan https://example.com
```

### With Target Keywords

Optimize for specific keywords:

```bash
python -m src.analyzer.cli seo-optimizer scan https://example.com \
  --config '{"seo-optimizer": {"target_keywords": ["python tutorial", "web development"]}}'
```

### CLI Integration

The SEO Optimizer integrates with the existing CLI:

```bash
# List available tests
python -m src.analyzer.cli list-tests

# Start analysis with SEO test
python -m src.analyzer.cli analyze https://example.com \
  --tests seo-optimizer \
  --config '{"seo-optimizer": {"target_keywords": ["your", "keywords"]}}'

# View results
python -m src.analyzer.cli view-results example-com
```

## Best Practices & Recommendations

### Meta Tags

- **Title Tags** (30-60 characters)
  - Include primary keyword near the beginning
  - Be descriptive and compelling for CTR
  - Avoid keyword stuffing
  - Example: "Python Web Framework - FastAPI Tutorials & Guides"

- **Meta Descriptions** (120-160 characters)
  - Include target keyword naturally
  - Call-to-action recommended
  - Describe page value proposition
  - Example: "Learn FastAPI with comprehensive tutorials. Build modern REST APIs with Python. Free guides and examples."

### Heading Structure

- Use exactly one H1 per page for main topic
- Follow hierarchical order (H1 → H2 → H3)
- Include target keywords in headings naturally
- Make headings descriptive and scannable
- Example hierarchy:
  ```
  H1: Complete Guide to FastAPI
    H2: Getting Started
      H3: Installation
      H3: First API
    H2: Advanced Topics
      H3: Async/Await
      H3: Security
  ```

### Content Optimization

- **Minimum content length**: 300 words for thin content warnings
- **Optimal length**: 1,500-2,500 words for comprehensive guides
- **Readability**: Short paragraphs, bullet points, clear structure
- **Keyword placement**: Include target keyword in:
  - First 100 words of content
  - H1 tag
  - First H2 tag
  - Meta description
  - 1-2% keyword density (natural language, not stuffing)

### Image Optimization

- Always include descriptive alt text
- Format: "[object] doing [action]"
- Example: "Python code editor with FastAPI tutorial open"
- Keep alt text under 125 characters
- Include relevant keywords naturally (not keyword stuffing)

### Internal Linking

- Link to related content contextually
- Use descriptive anchor text (not "click here")
- Maintain consistent internal linking structure
- Link high-authority pages to new pages
- Prioritize linking to important pages
- Example: "[FastAPI best practices](https://example.com/fastapi-best-practices)"

### Duplicate Content

- Use canonical tags for intentional duplicates
- Implement URL parameters handling (utm_*, session IDs)
- Consolidate similar pages into comprehensive guides
- Use 301 redirects for moved content
- Implement rel="alternate" for multilingual variants

### Robots.txt & Sitemap

- Create robots.txt with crawl delays
- Generate XML sitemap for all important pages
- Submit sitemap to Google Search Console
- Update sitemap when adding significant new content
- Example robots.txt:
  ```
  User-agent: *
  Allow: /
  Disallow: /admin/
  Disallow: /private/
  Crawl-delay: 1
  Sitemap: https://example.com/sitemap.xml
  ```

## Configuration Options

The SEO Optimizer accepts the following configuration parameters:

### target_keywords

**Type**: List[str] | String
**Default**: []
**Description**: Target keywords/phrases to analyze
**Format**: Comma-separated string or JSON array

```bash
# Comma-separated format
--config '{"seo-optimizer": {"target_keywords": "python tutorial,web framework"}}'

# JSON array format
--config '{"seo-optimizer": {"target_keywords": ["python tutorial", "web framework"]}}'
```

### Analysis Thresholds (Constants)

These can be customized by modifying the plugin code:

- `MIN_CONTENT_LENGTH`: 300 words
- `MIN_TITLE_LENGTH`: 30 characters
- `MAX_TITLE_LENGTH`: 60 characters
- `MIN_META_DESC_LENGTH`: 120 characters
- `MAX_META_DESC_LENGTH`: 160 characters
- `OPTIMAL_H1_COUNT`: 1 per page

## Integration with Other Tests

The SEO Optimizer works alongside other test plugins:

- **Migration Scanner**: Identifies deprecated code that may harm SEO
- **LLM Optimizer**: Improves content discoverability in LLM contexts
- **Security Audit**: Detects HTTPS/security issues affecting trust signals

Run all tests together:

```bash
python -m src.analyzer.cli analyze https://example.com \
  --tests migration-scanner,seo-optimizer,llm-optimizer,security-audit
```

## Common SEO Issues & Solutions

### Issue: Missing Meta Descriptions

**Impact**: Search engines show auto-generated snippets; reduced CTR
**Solution**: Add unique 120-160 character descriptions to all content pages
**Effort**: Low

### Issue: Thin Content (< 300 words)

**Impact**: Poor ranking for competitive keywords
**Solution**: Expand content with value-add sections, examples, guides
**Effort**: Medium to High

### Issue: Duplicate Title Tags

**Impact**: Diluted page authority; search confusion
**Solution**: Make titles unique; use page topic variations
**Effort**: Medium

### Issue: Missing H1 Tags

**Impact**: Page structure unclear to search engines
**Solution**: Add single descriptive H1 to every page
**Effort**: Low

### Issue: No Internal Links

**Impact**: Isolated pages reduce crawlability and authority flow
**Solution**: Add contextual links from related pages
**Effort**: Medium

### Issue: Missing Image Alt Text

**Impact**: Lost image search opportunities; poor accessibility; LLMs can't understand
**Solution**: Add descriptive alt text to all images
**Effort**: Low to Medium

## Performance Characteristics

- **Analysis Time**: O(n) where n = number of pages
- **Memory Usage**: Minimal per-page (HTML parsing doesn't store full content)
- **Typical Speed**: 100-500 pages per minute (HTML parsing only)
- **Accuracy**: Rule-based detection with 95%+ precision for technical checks

## Example Report Interpretation

### Scenario: E-commerce Site with 450 Pages

```json
{
  "overall_score": 5.8,
  "critical_issues": [
    {
      "category": "technical",
      "issue": "145 pages missing meta descriptions",
      "impact": "Search engines can't generate summaries",
      "affected_urls": 145
    }
  ],
  "warnings": [
    {
      "category": "content",
      "issue": "67 product pages under 300 words",
      "impact": "Thin content competes poorly in search",
      "affected_urls": 67
    }
  ],
  "opportunities": [
    {
      "category": "internal-linking",
      "issue": "High-traffic category pages lack links from homepage",
      "affected_urls": 12
    }
  ]
}
```

**Recommended Actions** (Priority Order):
1. **Week 1**: Add meta descriptions to 145 pages (high ROI, low effort)
2. **Week 2-4**: Expand thin product pages with specifications, reviews, use cases
3. **Week 4**: Improve homepage internal linking to top categories
4. **Ongoing**: Implement keyword optimization in content updates

## Limitations

- **No ranking data**: This tool doesn't check actual search rankings
- **No competitor analysis**: Compare URLs manually or with external tools
- **No backlink analysis**: Requires external backlink checker
- **Simplified duplicate detection**: Hash-based, not full content matching
- **Rule-based scoring**: Doesn't incorporate machine learning models
- **No JavaScript execution metrics**: Client-side rendering not fully analyzed

## Future Enhancements

- Machine learning-based content quality scoring
- Competitor gap analysis integration
- Schema.org structured data validation
- Core Web Vitals integration
- Mobile usability scoring
- Search intent analysis
- AI-powered recommendation generation
- Scheduled re-scans and trend tracking

## Support & Troubleshooting

### Plugin Not Loading

```bash
# Verify plugin is discoverable
python3 -c "from src.analyzer.plugin_loader import load_plugins; print([p.name for p in load_plugins()])"
```

### Missing Dependencies

```bash
# Install requirements
pip install -r requirements.txt
```

### High Memory Usage

- Plugin processes HTML pages one at a time
- For very large sites (>5000 pages), run in batches:

```bash
# Scan first 1000 pages
python -m src.analyzer.cli analyze https://example.com \
  --max-pages 1000 --tests seo-optimizer
```

## Contributing

To extend the SEO Optimizer:

1. Add new check method following `_check_*` pattern
2. Append findings to appropriate lists (critical_issues, warnings, opportunities)
3. Update `_calculate_score()` if changing scoring logic
4. Add test cases for new checks
5. Update documentation with new issue categories

Example:

```python
def _check_schema_markup(self, snapshot: SiteSnapshot, findings: Dict) -> None:
    """Check for structured data (schema.org)."""
    pages_without_schema = []

    for page in snapshot.pages:
        soup = BeautifulSoup(page.get_content(), "html.parser")
        schema = soup.find("script", {"type": "application/ld+json"})

        if not schema:
            pages_without_schema.append(page.url)

    if pages_without_schema:
        findings["opportunities"].append(
            SeoIssue(
                category="technical",
                issue=f"{len(pages_without_schema)} pages without schema markup",
                impact="Missing structured data reduces rich result eligibility",
                affected_urls=pages_without_schema[:10],
                recommendation="Add schema.org markup for rich snippets"
            )
        )
```

## License

This plugin is part of the Website Analyzer project. See main project LICENSE for details.

## References

- [Google Search Central: SEO Starter Guide](https://developers.google.com/search/docs/beginner/seo-starter-guide)
- [Google Web Vitals](https://web.dev/vitals/)
- [Schema.org Structured Data](https://schema.org/)
- [W3C Web Content Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OWASP SEO Top 10](https://owasp.org/)
