# Reference Project Analysis: LLM-analysis-reference-project

**Document Purpose**: Captures key insights from the archived PBS Wisconsin LLM analysis prototype to inform the design of this website analyzer project.

**Archive Date**: 2025-12-02
**Analysis Date**: 2025-12-02

## Project Overview

The reference project was a focused prototype for crawling PBS Wisconsin web content for LLM evaluation. It was intentionally sunset in favor of a redesigned approach (this project).

### Technical Stack

- **Primary Tool**: Crawl4AI 0.7.6
- **Python Version**: 3.x (implied from requirements)
- **Key Dependencies**:
  - `crawl4ai==0.7.6` - Core crawling engine
  - `playwright==1.55.0` - Browser automation
  - `beautifulsoup4==4.14.2` - HTML parsing
  - `trafilatura==2.0.0` - Content extraction
  - `lxml==5.4.0` - XML/HTML processing
  - `aiohttp==3.13.1` - Async HTTP
  - `openai==2.6.1` - LLM integration (present but unused in code)
  - `litellm==1.79.0` - Multi-provider LLM interface (present but unused)

### Architecture

**Simple Single-Purpose Design:**

```
src/crawl.py (main crawler)
  ↓
config/pbswisconsin_urls.json (seed URLs)
  ↓
data/raw/<slug>/<timestamp>/ (timestamped artifacts)
  ├── raw.html
  ├── cleaned.html
  ├── content.md
  └── metadata.json
```

**Key Design Decisions:**
1. **Timestamped storage**: Each crawl creates a new timestamped directory, enabling historical diffing
2. **URL slugification**: Converts URLs to filesystem-friendly paths (e.g., `pbswisconsin_org__about`)
3. **Triple artifact pattern**: Stores raw HTML, cleaned HTML, and markdown for each page
4. **Metadata sidecar**: JSON file captures status codes, redirects, links, session info
5. **Respectful crawling**: Honors robots.txt, uses reasonable timeouts
6. **Cache bypass**: Explicitly bypasses cache during prototyping for fresh data

## Code Analysis

### Core Crawler (`src/crawl.py`)

**Configuration Pattern:**
```python
DEFAULT_CONFIG = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    check_robots_txt=True,
    wait_until="domcontentloaded",
    page_timeout=60_000,
    screenshot=False,
    capture_network_requests=False,
)
```

**Workflow:**
1. Load seed URLs from JSON config
2. Slugify URLs for filesystem storage
3. Crawl with AsyncWebCrawler (batch or streaming)
4. Persist four artifacts per URL per timestamp
5. Continue on error (resilient batch processing)

**Notable Implementation Details:**
- Uses `async with AsyncWebCrawler()` pattern for proper resource cleanup
- Handles both iterable and async iterable result containers
- UTF-8 encoding explicit throughout
- UTC timestamps for consistency
- Creates directories on-demand

### Unimplemented Features (TODOs)

The code contains several TODOs indicating planned but unimplemented features:

1. **HTML Cleaning Pipeline** (Line 71)
   - Decision point: trafilatura vs. native Crawl4AI cleaning
   - Current: Both raw and "cleaned" HTML stored, but cleaning may be minimal

2. **Entity Extraction** (Line 85)
   - Schema inventories not implemented
   - Link collection present but not analyzed

3. **Screenshot Capture** (Line 89)
   - Screenshot flag disabled in config
   - Snapshot directory created but unused

4. **Historical Diffing** (Line 68)
   - Comment suggests "newline-delimited snapshot" format
   - Not implemented; would enable tracking content changes over time

## What Worked Well

Based on code structure and comments:

1. **Simple, focused design** - Single-purpose crawler easy to understand and modify
2. **Artifact preservation** - Triple-output format (raw/cleaned/markdown) provides flexibility
3. **Timestamped versioning** - Natural support for tracking content evolution
4. **Resilient crawling** - Continues on individual URL failures
5. **Respectful defaults** - Robots.txt compliance, reasonable timeouts

## Gaps and Limitations

Based on unimplemented TODOs and simple architecture:

1. **No actual LLM analysis** - Despite LLM libs in requirements, no evaluation code present
2. **No link following** - Only crawls seed URLs, doesn't spider
3. **No deduplication** - Would crawl same URL repeatedly with new timestamps
4. **No rate limiting** - Relies on Crawl4AI defaults
5. **No incremental updates** - Full recrawl required, no change detection
6. **No structured extraction** - Metadata captured but not parsed (schemas, entities)
7. **Single domain focus** - PBS Wisconsin hardcoded in config path
8. **No output for analysis** - Stores artifacts but no aggregation/reporting

## Lessons for Website Analyzer

### Architectural Patterns to Keep

1. **Timestamped artifact storage** - Enables historical analysis
2. **Multi-format output** - Raw HTML + markdown + metadata provides flexibility
3. **Async batch crawling** - Efficient for multi-URL operations
4. **URL slugification** - Clean filesystem organization
5. **Config-driven URL lists** - Easy to manage seed sets

### Improvements for New Design

1. **Multi-domain support** - Remove PBS-specific hardcoding
2. **Link discovery/spidering** - Optional crawl depth configuration
3. **Incremental crawling** - Change detection, conditional fetches
4. **LLM integration layer** - Actually implement analysis workflows
5. **Structured extraction** - Parse schemas, entities, meta tags
6. **Reporting/aggregation** - Summarize findings across crawls
7. **Screenshot pipeline** - Implement visual QA capabilities
8. **Content diffing** - Detect and report changes between crawls
9. **Configurable cleaning** - Choose cleaning strategy per use case
10. **Rate limiting/throttling** - Respectful crawling at scale

### Technical Debt to Avoid

1. **Unused dependencies** - Reference project includes openai/litellm but never uses them
2. **Incomplete features** - Either implement or remove screenshot/entity extraction TODOs
3. **Hardcoded paths** - Make all paths configurable or discoverable
4. **Missing error context** - Reference project fails silently on some errors

## Integration with Template Patterns

The reference project's simplicity contrasts with this template's agent-based approach:

**Reference Project**: Simple script → batch crawl → store artifacts
**Template Pattern**: Agent orchestration → feature-driven development → tested incremental delivery

### Recommended Hybrid Approach

1. **Crawling module** - Adopt reference project's core patterns, improve incrementally
2. **Analysis agents** - Specialized agents for different analysis types (LLM, SEO, accessibility)
3. **Orchestration layer** - Coordinate crawling, extraction, analysis workflows
4. **Knowledge base** - Store findings structured for agent consumption
5. **Feature list** - Break capabilities into testable, deliverable features

## Questions for Design Phase

1. **Scale**: Single sites or multi-site comparative analysis?
2. **Frequency**: One-time audits or continuous monitoring?
3. **Depth**: Homepage only, or full site crawls?
4. **Analysis types**: What questions should the analyzer answer?
5. **Output format**: Reports, APIs, dashboards, or raw data?
6. **LLM strategy**: Which models for what analysis tasks?
7. **Storage**: Local files (like reference) or database?

## Conclusion

The reference project demonstrates a solid foundation for web crawling with Crawl4AI. Its simplicity is a strength for prototyping but reveals gaps for production use. The new website-analyzer project should:

- Preserve the clean crawling architecture
- Add proper LLM analysis implementation
- Support multi-domain, configurable workflows
- Implement agent-based orchestration for complex analysis
- Provide actionable outputs, not just raw artifacts

The template's long-running development pattern is well-suited for iteratively building out the missing capabilities identified here.
