# Website Analyzer: Design Document

**Version**: 0.2.0
**Date**: 2025-12-02
**Status**: Initial Design - Revised

## Executive Summary

Website Analyzer is an MCP-enabled service that performs comprehensive website analysis through extensible test batteries. It maintains project workspaces for each analyzed site, tracking issues, fixes, and ongoing health. Users interact through Claude Desktop or Claude Code, which communicate with the analyzer via MCP protocol.

### Core Value Proposition

- **Centralized maintenance tracking**: Single source of truth for site health across multiple test types
- **Persistent analysis workspace**: Maintains site snapshots and historical test results per project
- **MCP integration**: Seamless interaction from Claude interfaces without context switching
- **Extensible test framework**: Add new test types as needs evolve
- **Regression detection**: Re-run tests to verify fixes and detect new issues

## Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│  Claude Desktop │
│  or Claude Code │
│   (Orchestrator)│
└────────┬────────┘
         │ MCP Protocol
         ▼
┌─────────────────┐
│   MCP Server    │
│  (Node.js/TS)   │
└────────┬────────┘
         │ Process spawn
         ▼
┌─────────────────┐
│ Test Runner CLI │
│   (Python 3.11) │
└────┬────────┬───┘
     │        │
     │        └─────────────┐
     ▼                      ▼
┌─────────────┐    ┌────────────────┐
│   Crawl4AI  │    │  LLM Services  │
│   (Local)   │    │ (Haiku/GPT-4o  │
│             │    │  mini/Gemini)  │
└─────────────┘    └────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│      Project Workspace          │
│  projects/<site-slug>/          │
│    ├── snapshots/               │
│    ├── test-results/            │
│    ├── issues.json              │
│    └── metadata.json            │
└─────────────────────────────────┘
```

### Component Architecture

#### 1. MCP Server (Presentation Layer)
- **Technology**: Node.js with TypeScript
- **Responsibilities**:
  - Expose MCP tools for Claude to invoke
  - Present available tests and project status
  - Validate user inputs
  - Spawn Python CLI processes
  - Stream progress/results back to Claude
- **Key Tools**:
  - `list_tests`: Show available test types with descriptions
  - `list_projects`: Show tracked websites and their status
  - `start_analysis`: Begin test battery for a website
  - `check_status`: Query ongoing/completed test runs
  - `view_issues`: Retrieve issue list for a project
  - `rerun_tests`: Re-execute tests to check for fixes

#### 2. Test Runner CLI (Core Engine)
- **Technology**: Python 3.11 with async/await
- **Responsibilities**:
  - Crawl websites using Crawl4AI
  - Maintain project workspaces
  - Execute test plugins
  - Generate structured issue reports
  - Track test history and changes
- **Key Modules**:
  - `crawler.py`: Site crawling and snapshot management
  - `runner.py`: Test orchestration and execution
  - `reporter.py`: Issue aggregation and reporting
  - `workspace.py`: Project directory management

#### 3. Test Plugin System
- **Pattern**: Plugin-based architecture for extensibility
- **Interface**:
  ```python
  class TestPlugin(Protocol):
      name: str
      description: str

      async def analyze(
          self,
          snapshot: SiteSnapshot,
          config: dict
      ) -> TestResult
  ```
- **Initial Tests**: Migration scanner, LLM optimization, SEO optimization, security audit

#### 4. Project Workspace
- **Structure**:
  ```
  projects/
  └── example-com/
      ├── metadata.json          # Site URL, last crawl, test history
      ├── issues.json            # Aggregated issues across all tests
      ├── snapshots/
      │   └── 20251202T120000Z/  # Timestamped site snapshots
      │       ├── pages/         # Individual page artifacts
      │       ├── sitemap.json   # Site structure
      │       └── summary.json   # Crawl metadata
      └── test-results/
          ├── migration-scan/
          │   └── 20251202T120500Z.json
          ├── llm-optimization/
          │   └── 20251202T120800Z.json
          ├── seo-optimization/
          │   └── 20251202T121000Z.json
          └── security-audit/
              └── 20251202T121500Z.json
  ```

## Initial Test Specifications

### Test 1: Migration Error Scanner

**Purpose**: Find instances of problematic code patterns across entire site.

**Inputs**:
- Website URL
- Pattern description (natural language)
- Optional: Regex pattern or code snippet to match

**Process**:
1. Crawl entire site, capture HTML/markdown for all pages
2. Convert pattern description to search strategy (LLM-assisted if needed)
3. Search all pages for pattern matches
4. Extract context around matches (code snippet, surrounding content)
5. Generate list of affected URLs with locations

**Output Format**:
```json
{
  "test": "migration-scan",
  "timestamp": "2025-12-02T12:05:00Z",
  "pattern": "deprecated jQuery .live() calls",
  "matches_found": 23,
  "affected_pages": [
    {
      "url": "https://example.com/page1",
      "matches": [
        {
          "line_number": 42,
          "context": "$('#element').live('click', function() { ... })",
          "suggestion": "Replace with .on() method"
        }
      ]
    }
  ]
}
```

**Issue Tracking**:
- Each match becomes an issue with: URL, location, pattern, priority
- Issues marked "resolved" when pattern no longer found on re-scan

### Test 2: LLM Optimization

**Purpose**: Make site more discoverable and useful in LLM contexts.

**Inputs**:
- Website URL
- Optional: Target LLM provider (OpenAI, Anthropic, etc.)
- Optional: Business goals/priorities

**Process**:
1. Crawl entire site with focus on content structure
2. Analyze site-wide patterns:
   - Meta tags (description, keywords, Open Graph, Twitter cards)
   - Schema.org markup (presence, correctness)
   - Content hierarchy (headings, semantic HTML)
   - Link structure and internal navigation
3. Per-page analysis:
   - Content clarity and scannability
   - Title/description optimization for LLM summarization
   - Key information placement (above the fold, semantic priority)
4. Generate LLM queries against site to test discoverability
5. Produce quick wins and strategic recommendations

**Output Format**:
```json
{
  "test": "llm-optimization",
  "timestamp": "2025-12-02T12:08:00Z",
  "overall_score": 6.5,
  "quick_wins": [
    {
      "priority": "high",
      "category": "meta-tags",
      "issue": "45 pages missing meta descriptions",
      "impact": "LLMs can't generate accurate summaries",
      "fix": "Add descriptive meta tags to all content pages",
      "affected_urls": ["https://example.com/page1", "..."]
    },
    {
      "priority": "medium",
      "category": "schema-markup",
      "issue": "Blog posts lack Article schema",
      "impact": "Content relationships unclear to LLMs",
      "fix": "Add schema.org/Article markup to blog template",
      "affected_urls": ["https://example.com/blog/*"]
    }
  ],
  "strategic_recommendations": [
    {
      "category": "content-structure",
      "finding": "Key information buried in paragraphs",
      "recommendation": "Restructure landing pages with clear sections and headings",
      "effort": "high",
      "impact": "high"
    }
  ]
}
```

**Issue Tracking**:
- Quick wins tracked as actionable issues
- Strategic recommendations tracked as long-term goals
- Re-scan shows improvement scores over time

### Test 3: SEO Optimization

**Purpose**: Identify search engine optimization opportunities.

**Inputs**:
- Website URL
- Optional: Target keywords/phrases
- Optional: Competitor URLs for comparison

**Process**:
1. Crawl entire site with SEO focus
2. Technical SEO checks:
   - Meta tags (title, description, keywords)
   - Heading structure (H1-H6 hierarchy)
   - Image alt text coverage
   - Link health (broken links, redirect chains)
   - Mobile responsiveness indicators
   - Page load performance (from crawler metrics)
   - robots.txt and sitemap.xml validation
3. Content SEO analysis:
   - Keyword density and placement
   - Content length and quality signals
   - Internal linking structure
   - Duplicate content detection
4. If competitors provided, gap analysis

**Output Format**:
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
      "affected_urls": ["..."]
    }
  ],
  "warnings": [
    {
      "category": "content",
      "issue": "8 pages under 300 words",
      "impact": "Thin content may rank poorly",
      "affected_urls": ["..."]
    }
  ],
  "opportunities": [
    {
      "category": "internal-linking",
      "finding": "High-value pages lack internal links",
      "recommendation": "Add contextual links from related content",
      "pages": ["..."]
    }
  ]
}
```

**Issue Tracking**:
- Critical issues: immediate action items
- Warnings: should-fix items
- Opportunities: nice-to-have improvements

### Test 4: Security Audit

**Purpose**: Identify security vulnerabilities and hardening opportunities.

**Inputs**:
- Website URL
- Optional: Authentication credentials for testing protected areas
- Optional: Audit depth (surface/deep)

**Process**:
1. Crawl site noting security-relevant patterns
2. Passive security checks:
   - HTTPS usage (mixed content warnings)
   - Security headers (CSP, X-Frame-Options, HSTS, etc.)
   - Cookie security flags (Secure, HttpOnly, SameSite)
   - Exposed sensitive files (/.git, /admin, /.env)
   - Information disclosure in HTML comments/errors
   - Outdated libraries (detectable from client-side includes)
3. Content security analysis:
   - User-generated content handling
   - Form security (CSRF tokens detectable)
   - Input validation indicators
4. Third-party resource audit:
   - External script sources
   - CDN integrity checks (SRI hashes)
   - Analytics/tracking pixel inventory

**Output Format**:
```json
{
  "test": "security-audit",
  "timestamp": "2025-12-02T12:15:00Z",
  "overall_risk": "medium",
  "vulnerabilities": [
    {
      "severity": "high",
      "category": "mixed-content",
      "issue": "3 pages load insecure resources over HTTP",
      "risk": "Man-in-the-middle attacks possible",
      "affected_urls": ["..."],
      "cwe_id": "CWE-311"
    },
    {
      "severity": "medium",
      "category": "headers",
      "issue": "Missing Content-Security-Policy header",
      "risk": "XSS attacks not mitigated",
      "affected_urls": ["all pages"],
      "recommendation": "Implement CSP with appropriate directives"
    }
  ],
  "warnings": [
    {
      "severity": "low",
      "category": "information-disclosure",
      "issue": "HTML comments contain developer notes",
      "affected_urls": ["..."]
    }
  ],
  "hardening_recommendations": [
    {
      "category": "headers",
      "recommendation": "Add Strict-Transport-Security header",
      "benefit": "Prevent protocol downgrade attacks"
    }
  ]
}
```

**Issue Tracking**:
- Vulnerabilities tracked by severity (high/medium/low)
- Status: open → investigating → fixed → verified
- Re-scan validates fixes and detects regressions

## MCP Tool Specifications

### Tool: `list_tests`

**Description**: Show available test types.

**Input**: None (or optional filter by category)

**Output**:
```json
{
  "tests": [
    {
      "id": "migration-scan",
      "name": "Migration Error Scanner",
      "description": "Search entire site for problematic code patterns",
      "required_inputs": ["url", "pattern"],
      "optional_inputs": ["regex"]
    },
    {
      "id": "llm-optimization",
      "name": "LLM Optimization Audit",
      "description": "Analyze site for LLM discoverability and usefulness",
      "required_inputs": ["url"],
      "optional_inputs": ["target_llm", "business_goals"]
    }
  ]
}
```

### Tool: `list_projects`

**Description**: Show tracked websites and their status.

**Input**: None (or optional filter)

**Output**:
```json
{
  "projects": [
    {
      "slug": "example-com",
      "url": "https://example.com",
      "last_crawl": "2025-12-02T12:00:00Z",
      "open_issues": 45,
      "last_test": "llm-optimization",
      "last_test_date": "2025-12-02T12:08:00Z"
    }
  ]
}
```

### Tool: `start_analysis`

**Description**: Begin test battery for a website.

**Input**:
```json
{
  "url": "https://example.com",
  "tests": ["migration-scan", "llm-optimization"],
  "config": {
    "migration-scan": {
      "pattern": "jQuery .live() calls"
    }
  },
  "crawl_options": {
    "max_depth": null,
    "max_pages": 1000,
    "respect_robots": true,
    "timeout_per_page": 60
  }
}
```

**Output**:
```json
{
  "job_id": "abc123",
  "status": "started",
  "message": "Crawling site and running 2 tests..."
}
```

**Behavior**:
- Returns immediately with job ID
- Spawns Python CLI in background
- Claude can poll with `check_status` or receive streaming updates

### Tool: `check_status`

**Description**: Query status of ongoing or completed test run.

**Input**:
```json
{
  "job_id": "abc123"
}
```

**Output**:
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": {
    "crawl": "complete",
    "tests": {
      "migration-scan": "complete",
      "llm-optimization": "running"
    }
  },
  "estimated_completion": "2025-12-02T12:20:00Z"
}
```

### Tool: `view_issues`

**Description**: Retrieve issue list for a project.

**Input**:
```json
{
  "project": "example-com",
  "filters": {
    "test": "llm-optimization",
    "priority": "high",
    "status": "open"
  }
}
```

**Output**:
```json
{
  "project": "example-com",
  "total_issues": 45,
  "filtered_issues": 12,
  "issues": [
    {
      "id": "issue-001",
      "test": "llm-optimization",
      "priority": "high",
      "status": "open",
      "title": "45 pages missing meta descriptions",
      "affected_urls": ["..."],
      "first_detected": "2025-12-02T12:08:00Z"
    }
  ]
}
```

### Tool: `rerun_tests`

**Description**: Re-execute tests to verify fixes and detect new issues.

**Input**:
```json
{
  "project": "example-com",
  "tests": ["migration-scan"],
  "recrawl": true
}
```

**Output**:
```json
{
  "job_id": "def456",
  "status": "started",
  "message": "Re-crawling site and running 1 test..."
}
```

## LLM Cost Optimization Strategy

**Design Principle**: Claude Desktop/Code acts as orchestrator; analysis uses cost-efficient models.

### Model Selection by Task

| Task | Model | Rationale |
|------|-------|-----------|
| **Orchestration** | Sonnet (Claude Desktop/Code) | User interaction, complex reasoning, tool use |
| **Pattern matching** | Haiku 3.5 or GPT-4o-mini | Simple text analysis, high speed |
| **Content analysis** | Haiku 3.5 or Gemini 1.5 Flash | Meta tag quality, heading structure |
| **Recommendation generation** | GPT-4o-mini or Gemini 1.5 Flash | Structured outputs, cost-effective |
| **Security analysis** | Haiku 3.5 | Pattern detection, vulnerability classification |

### Cost Control Measures

1. **Local-first processing**: Use regex, BeautifulSoup, and lxml for structured data extraction before considering LLM calls
2. **Batch processing**: Group similar analysis tasks to minimize API calls
3. **Caching**: Store LLM responses for repeated patterns (e.g., common meta tag issues)
4. **Progressive analysis**: Start with rule-based checks, escalate to LLM only when ambiguous
5. **Configurable depth**: Allow users to choose "quick scan" (minimal LLM) vs "deep analysis" (more LLM)
6. **Timeouts and retries**: Fail gracefully on API errors without wasting tokens

### Expected Cost Profile (Example: 500-page site)

- **Migration scan**: $0.00 (pure pattern matching, no LLM)
- **SEO optimization**: $0.05-0.10 (mostly rule-based, LLM for content quality scoring)
- **LLM optimization**: $0.10-0.25 (meta description quality, recommendation phrasing)
- **Security audit**: $0.02-0.05 (pattern detection, vulnerability descriptions)

**Total per full analysis**: ~$0.20-$0.40 for 500 pages

### Implementation Notes

- Use `litellm` library for unified interface across providers
- Environment variables for API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`)
- Graceful degradation: if API unavailable, fall back to rule-based analysis with notes
- Progress indicators should show which model is being used for transparency

## Technology Stack

### MCP Server
- **Runtime**: Node.js 18+ with TypeScript
- **Framework**: `@modelcontextprotocol/sdk`
- **Key Libraries**:
  - Process management for spawning Python CLI
  - JSON schema validation for inputs
  - Logging (winston or pino)

### Test Runner CLI
- **Language**: Python 3.11
- **Key Libraries**:
  - `crawl4ai` 0.7.6+ - Web crawling
  - `playwright` - Browser automation
  - `beautifulsoup4` - HTML parsing
  - `lxml` - Fast XML/HTML processing
  - `asyncio` - Async orchestration
  - `pydantic` - Data validation
  - `typer` - CLI framework
  - `rich` - Terminal UI/progress bars
- **Optional Libraries** (per test):
  - `openai` or `anthropic` - LLM API calls for analysis
  - `requests` - HTTP utilities
  - `validators` - URL validation
  - `tldextract` - Domain parsing

### Storage
- **Format**: JSON files (simple, readable, git-friendly)
- **Structure**: Filesystem-based project workspaces
- **Future**: Could add SQLite for query performance if needed

## Crawl Scope and Limits

### Default Crawl Behavior

**Philosophy**: Comprehensive by default, with safety limits to prevent runaway crawls.

**Default Settings**:
- `max_pages`: 1000 pages (configurable up to 10,000)
- `max_depth`: None (follow all internal links until max_pages reached)
- `timeout_per_page`: 60 seconds
- `respect_robots`: true
- `follow_external_links`: false (stay within same domain)
- `include_subdomains`: true (e.g., blog.example.com if starting from example.com)

### Rationale

**For Migration Error Scanner**: We want comprehensive coverage to avoid missing problematic pages. A depth limit could skip deep pages that contain the target pattern. Using `max_pages` as the primary constraint ensures we scan as much of the site as feasible while preventing infinite crawls.

**Performance Considerations**:
- 1000 pages @ 60s timeout = max ~17 hours (worst case)
- Typical crawl: 1000 pages @ 2-5s average = 35-85 minutes
- Progress updates every 10 pages keep user informed
- Can interrupt and resume if needed (checkpoint support in Phase 2)

### Crawl Strategy

1. **Discovery Phase**:
   - Start at provided URL (typically homepage)
   - Extract all internal links from each page
   - Build crawl queue prioritizing:
     - Shallow pages first (breadth-first)
     - High-value paths (e.g., /products/, /blog/) over utility pages (/privacy/, /terms/)
     - Pages already in sitemap.xml if available

2. **Crawl Execution**:
   - Async crawling with concurrency limit (5 concurrent requests)
   - Respect robots.txt delays and crawl-delay directives
   - Deduplicate URLs (normalize, handle trailing slashes, query params)
   - Store each page: raw HTML, cleaned HTML, markdown, metadata

3. **Completion Conditions**:
   - Reached `max_pages` limit
   - No more internal links to discover
   - User interruption (Ctrl+C)
   - Timeout exceeded (configurable overall timeout, e.g., 4 hours)

### User Configuration

Users can override defaults via MCP tool:

```json
{
  "crawl_options": {
    "max_pages": 2500,
    "max_depth": 5,
    "timeout_per_page": 90,
    "include_patterns": ["/blog/*", "/docs/*"],
    "exclude_patterns": ["/archive/*", "/old/*"],
    "priority_urls": ["https://example.com/important-page"]
  }
}
```

### Edge Cases

- **Large sites (10,000+ pages)**: Warn user, offer sampling strategy or focused crawl
- **Dynamic content**: Crawl4AI with Playwright handles JavaScript-rendered pages
- **Login walls**: Skip for v1, document limitation
- **Rate limiting**: Back off exponentially if encountering 429 responses
- **Paywalls**: Detect and skip, note in report

## Development Roadmap

### Phase 1: Foundation (MVP)
**Goal**: Basic MCP server + single test working end-to-end

1. Project workspace management (Python)
   - Create/load project directories
   - Store/retrieve metadata
2. Basic crawler (Python)
   - Crawl site with Crawl4AI
   - Store snapshots
   - Generate sitemap
3. Test plugin interface (Python)
   - Define plugin protocol
   - Implement runner that loads plugins
4. Migration scanner test (Python)
   - Simple pattern matching across site
5. MCP server skeleton (Node.js)
   - Basic tool implementations
   - Spawn Python CLI
   - Return results
6. End-to-end test: User asks Claude to scan a site

**Deliverable**: Can scan a website for migration errors via Claude Desktop

### Phase 2: Issue Tracking
**Goal**: Persistent issues with status tracking

7. Issue aggregation (Python)
   - Collect issues from test results
   - Store in `issues.json`
8. Issue management (Python)
   - Mark issues resolved/in-progress
   - Track issue history
9. MCP tools for issue viewing (Node.js)
   - `view_issues` with filtering
   - Issue status updates

**Deliverable**: Issues persist across runs, can track fixes

### Phase 3: LLM & SEO Tests
**Goal**: Add optimization-focused tests

10. LLM optimization test (Python)
    - Meta tag analysis
    - Schema markup detection
    - Content structure analysis
    - Generate recommendations
11. SEO optimization test (Python)
    - Technical SEO checks
    - Content analysis
    - Link health
12. Test configuration via MCP (Node.js)
    - Pass test-specific config from Claude

**Deliverable**: Can run LLM and SEO audits

### Phase 4: Security Audit
**Goal**: Add security testing

13. Security audit test (Python)
    - Header analysis
    - HTTPS/mixed content
    - Exposed files
    - Third-party resources
14. Vulnerability tracking (Python)
    - Severity-based prioritization
    - CWE/CVE references where applicable

**Deliverable**: Comprehensive security audit capability

### Phase 5: Polish & UX
**Goal**: Production-ready quality

15. Progress streaming (Node.js + Python)
    - Real-time updates during crawl/test
16. Error handling and recovery (Both)
    - Graceful failures
    - Partial results on timeout
17. Report generation (Python)
    - Human-readable summaries
    - Export formats (markdown, HTML, PDF)
18. Documentation (Both)
    - User guide for Claude interactions
    - Developer guide for adding tests
    - API documentation

**Deliverable**: Polished, documented, reliable tool

## Success Criteria

### Functional Requirements
- [ ] Can crawl and snapshot websites of varying sizes (10-10,000 pages)
- [ ] Executes all four initial test types successfully
- [ ] Maintains project workspaces with historical data
- [ ] Accessible from both Claude Desktop and Claude Code via MCP
- [ ] Re-running tests detects resolved issues and new problems
- [ ] Handles errors gracefully (network failures, timeouts, invalid input)

### Quality Requirements
- [ ] Tests complete in reasonable time (< 5 min for 100 pages)
- [ ] Issue reports are actionable and well-structured
- [ ] False positive rate < 10% for pattern matching
- [ ] Recommendations in LLM/SEO tests are relevant and prioritized
- [ ] Security audit covers OWASP Top 10 relevant checks

### Usability Requirements
- [ ] Users can start an analysis with a single Claude message
- [ ] Clear progress indicators during long-running operations
- [ ] Issue lists are easy to filter and prioritize
- [ ] Test configurations have sensible defaults
- [ ] Documentation enables users to add custom tests

## Design Decisions

### Resolved in v0.2.0

1. **✅ Crawl scope limits**: Default 1000 pages (configurable to 10,000), no depth limit to ensure comprehensive coverage for migration scans
2. **✅ LLM costs**: Use cost-efficient models (Haiku, GPT-4o-mini, Gemini Flash) for analysis; Claude Desktop/Code orchestrates. Expected ~$0.20-0.40 per 500-page site
3. **✅ Test extensibility**: Backend-managed tests only (no user plugin system in v1)
4. **✅ Authentication**: Not supported in v1, document limitation and defer to future

### Open Questions for Future Phases

1. **Rate limiting**: Should we throttle crawls to avoid overwhelming servers? (Current: respect robots.txt, 5 concurrent requests)
2. **Reporting**: Do we need a web UI, or is Claude + CLI sufficient? (Current: CLI + MCP sufficient)
3. **Diff detection**: Should we auto-compare snapshots between crawls to highlight changes? (Defer to Phase 2)
4. **Scheduling**: Should the tool support scheduled re-scans (cron-like)? (Defer, user can cron the CLI)
5. **Checkpoint/resume**: For very large sites, support interruption and resumption? (Defer to Phase 2)
6. **Export formats**: Beyond JSON, support CSV, HTML reports, PDF? (Defer to Phase 5)

## Next Steps

1. **Review and refine design**: Iterate on this document based on feedback
2. **Set up development environment**: Python 3.11, Node.js, dependencies
3. **Invoke initializer agent**: Generate `feature_list.json` for long-running development
4. **Begin Phase 1 implementation**: Foundation + migration scanner
5. **Test with real websites**: Validate design assumptions with production data

---

**Document Revision History**:
- 2025-12-02: Initial design (v0.1.0)
- 2025-12-02: Revised with LLM cost strategy, crawl limits, resolved design decisions (v0.2.0)
