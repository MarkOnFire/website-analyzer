# Website Analyzer

**MCP-enabled comprehensive website analysis tool for maintenance tracking and optimization**

Website Analyzer performs automated audits of entire websites through extensible test batteries, maintaining persistent project workspaces that track issues, fixes, and ongoing health. Users interact through Claude Desktop or Claude Code via the Model Context Protocol (MCP), making sophisticated website analysis accessible through natural conversation.

## Overview

This tool provides four core analysis capabilities:

1. **Migration Error Scanner**: Find problematic code patterns across entire sites (e.g., failed migration artifacts, deprecated APIs)
2. **LLM Optimization**: Analyze and improve website discoverability in LLM contexts (ChatGPT, Claude, etc.)
3. **SEO Optimization**: Identify search engine optimization opportunities and technical issues
4. **Security Audit**: Detect vulnerabilities and recommend security hardening measures

### Key Features

- **Persistent Project Workspaces**: Each analyzed site gets a dedicated workspace with snapshots, test results, and tracked issues
- **Historical Tracking**: Re-run tests to verify fixes and detect regressions over time
- **Cost-Optimized**: Uses efficient models (Haiku, GPT-4o-mini, Gemini Flash) for analysis (~$0.20-$0.40 per 500 pages)
- **Comprehensive Crawling**: Default 1000 pages with intelligent prioritization and edge case handling
- **MCP Integration**: Seamless access from Claude Desktop and Claude Code—no context switching

## Architecture

**Two-Tier Design:**

```
Claude Desktop/Code (Orchestrator)
         ↓
    MCP Server (Node.js/TypeScript)
         ↓
    Test Runner CLI (Python 3.11)
         ↓
    Project Workspaces (projects/<site-slug>/)
```

- **MCP Server**: Exposes tools to Claude for starting analyses, checking status, viewing issues
- **Test Runner**: Crawls websites with Crawl4AI, executes test plugins, generates reports
- **Project Workspaces**: Persistent storage with snapshots, test results, and issue tracking

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd website-analyzer

# Run initialization script
./init.sh

# Activate virtual environment
source .venv/bin/activate
```

The `init.sh` script will:
- Verify Python 3.11 and Node.js 18+ are installed
- Create a Python virtual environment
- Install all dependencies (crawl4ai, playwright, etc.)
- Install Playwright browsers
- Set up project directories

### Development Status

**Current Progress**: 1/127 features implemented (0.8%)

This project uses Anthropic's long-running autonomous development pattern. Features are implemented systematically across multiple sessions with:
- `feature_list.json` - Comprehensive test case tracking (127 features)
- `init.sh` - Reproducible environment setup
- `claude-progress.txt` - Session memory and progress log

See `docs/design.md` for complete architecture and specifications.

## Project Structure

```
website-analyzer/
├── docs/
│   ├── design.md                    # Complete architecture and specifications
│   └── reference-project-analysis.md # Lessons from prototype
├── projects/                         # Site-specific workspaces
│   └── <site-slug>/
│       ├── snapshots/                # Timestamped site crawls
│       ├── test-results/             # Test execution results
│       ├── issues.json               # Tracked issues
│       └── metadata.json             # Project metadata
├── src/
│   └── analyzer/
│       └── plugins/                  # Extensible test framework
├── tests/                            # Test runner modules
├── mcp-server/                       # MCP integration layer
├── feature_list.json                 # Development roadmap
├── claude-progress.txt               # Session memory
└── init.sh                           # Environment setup
```

## Usage (When Complete)

### Via Claude Desktop/Code

```
User: "Analyze https://example.com for migration errors.
       Look for this pattern: [[{\"fid\":... }}]]"

Claude: *Uses MCP tools to start analysis*
        "I've started crawling example.com (up to 1000 pages).
        The migration error scanner is searching for that pattern.
        This should complete in about 15-20 minutes..."

User: "Check status"

Claude: *Queries MCP server*
        "Crawl complete: 847 pages analyzed.
        Found 23 matches across 15 pages.
        Would you like to see the affected URLs?"
```

### Direct CLI (For Development)

```bash
# Start analysis
python -m tests.runner analyze \
  --url https://example.com \
  --tests migration-scan \
  --pattern '[[{"fid":'

# List projects
python -m tests.runner list-projects

# View issues
python -m tests.runner view-issues example-com \
  --test migration-scan \
  --status open
```

## Development Roadmap

**Phase 1: Foundation (Features 1-44)** - In Progress
- [x] Project directory structure
- [ ] Workspace manager
- [ ] Crawler with Crawl4AI
- [ ] Test plugin framework
- [ ] Migration scanner test
- [ ] CLI interface

**Phase 2: Issue Tracking (Features 45-54)**
- [ ] Issue aggregation and persistence
- [ ] Status management (open/in-progress/fixed/verified)
- [ ] Historical comparison

**Phase 3: LLM & SEO Tests (Features 55-87)**
- [ ] LLM optimization analyzer
- [ ] SEO optimization analyzer
- [ ] Recommendation generation

**Phase 4: Security Audit (Features 88-100)**
- [ ] Security vulnerability detection
- [ ] Header and configuration analysis
- [ ] Third-party resource auditing

**Phase 5: Polish & Production (Features 101-127)**
- [ ] MCP server implementation
- [ ] Progress streaming
- [ ] Error handling and recovery
- [ ] Documentation and deployment

## Technology Stack

### Python CLI
- **crawl4ai** - Web crawling with JavaScript rendering
- **playwright** - Browser automation
- **beautifulsoup4, lxml** - HTML parsing
- **pydantic** - Data validation
- **typer, rich** - CLI framework and UI
- **litellm** - Unified LLM interface (Anthropic, OpenAI, Google)

### Node.js MCP Server
- **@modelcontextprotocol/sdk** - MCP integration
- **TypeScript** - Type-safe server implementation

## Testing

The project includes a real-world test case in `test-project-bug-hunter.md`:
- **Target**: WPR.org
- **Issue**: Failed migration leaving visible WordPress embed code
- **Pattern**: `[[{"fid":"...","type":"media"...}}]]`

This will be used to validate the migration scanner once implemented.

## Contributing

This project is developed using autonomous agent sessions. To continue development:

```bash
# Start a new coding session
# In Claude Desktop or Claude Code, say:
"Please continue development. Implement the next feature from feature_list.json."
```

The coding-agent will:
1. Read `claude-progress.txt` for context
2. Review `feature_list.json` for next feature
3. Run `./init.sh` to verify environment
4. Implement and test the feature
5. Update tracking and commit changes
6. Document progress

## Documentation

- `docs/design.md` - Complete architecture, specifications, and cost analysis
- `docs/reference-project-analysis.md` - Lessons learned from prototype
- `CLAUDE.md` - Guidance for AI assistants working in this repository
- `AGENTS.md` - Agent architecture and collaboration patterns

## Cost Optimization

Analysis uses cost-efficient models to keep expenses low:
- **Pattern matching**: Local processing (regex, BeautifulSoup)
- **Content analysis**: Haiku 3.5 or GPT-4o-mini
- **Recommendations**: Gemini 1.5 Flash or GPT-4o-mini
- **Orchestration**: Claude Sonnet (via Claude Desktop/Code)

**Expected costs**: ~$0.20-$0.40 per 500-page site for full analysis

## License

[Specify license here]

## Co-Authors

This repository is developed collaboratively with AI assistance. Contributors are tracked via git commits following workspace conventions.

### Active Agents

| Agent | Role | Sessions |
|-------|------|----------|
| **initializer** | Project foundation setup | Session 1 |
| **coding-agent** | Feature implementation | Sessions 2+ |
| **Main Assistant** | Orchestration, documentation | Ongoing |

### Agent Contributions

View agent-specific contributions:

```bash
# View all commits by coding-agent
git log --grep="Agent: coding-agent"

# View all agent-attributed commits
git log --grep="Agent:" --oneline

# Count commits by agent
git log --oneline | grep -o '\[Agent: [^]]*\]' | sort | uniq -c
```

### Workspace Integration

This project follows workspace-wide conventions for agent collaboration:

- **Commit Attribution**: All AI-generated commits include `[Agent: <name>]` after the subject line
- **Feature Tracking**: `feature_list.json` maintains single source of truth
- **Session Memory**: `claude-progress.txt` provides continuity across sessions
- **Infrastructure Compliance**: Level 3 compliance with workspace requirements

See [workspace conventions](../../workspace_ops/conventions/COMMIT_CONVENTIONS.md) for complete details.

---

**Current Status**: Foundation phase in progress (Feature 1/127 complete)
**Next Milestone**: Complete Phase 1 foundation (Features 1-44)
**Documentation**: See `docs/design.md` for comprehensive specifications
