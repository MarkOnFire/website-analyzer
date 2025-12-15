# Documentation Index

Complete guide to Website Analyzer documentation and resources.

---

## Start Here

### First Time Users
1. **[Quick Start (2 minutes)](../QUICKSTART.md)** - Get your first scan running in under 2 minutes
2. **[Main README](../README.md)** - Project overview and features
3. **[CLI Usability Guide](guides/CLI_USABILITY.md)** - Command-line interface overview

### Experienced Users
1. **[Bug Finder Guide](guides/BUG_FINDER.md)** - Complete bug discovery documentation
2. **[Migration Scanner Guide](guides/MIGRATION_SCANNER.md)** - Pattern matching in depth
3. **[Projects & Workspaces](guides/PROJECTS.md)** - Managing multiple sites

---

## User Guides

### Core Tools
- **[Bug Finder Guide](guides/BUG_FINDER.md)** - Find visual bugs by example
- **[Migration Scanner Guide](guides/MIGRATION_SCANNER.md)** - Find deprecated code patterns
- **[Projects & Workspaces Guide](guides/PROJECTS.md)** - Manage multiple analyses
- **[CLI Usability Guide](guides/CLI_USABILITY.md)** - Command-line best practices

### Reference
- **[Configuration Guide](reference/CONFIG.md)** - Settings and customization
- **[CLI Quick Reference](reference/CLI_QUICK_REFERENCE.md)** - Command cheat sheet

---

## Feature Documentation

Advanced features have dedicated documentation in `docs/features/`:

### Scheduler
Automated scan scheduling and recurring analyses.
- **[Index](features/scheduler/INDEX.md)** - Scheduler overview
- **[Quick Start](features/scheduler/QUICK_START.md)** - Get started quickly
- **[Guide](features/scheduler/GUIDE.md)** - Complete usage guide
- **[Command Reference](features/scheduler/COMMAND_REFERENCE.md)** - All scheduler commands
- **[Deployment](features/scheduler/DEPLOYMENT.md)** - Production deployment

### Notifications
Alert system for scan results and events.
- **[Index](features/notifications/INDEX.md)** - Notifications overview
- **[Quick Start](features/notifications/QUICK_START.md)** - Set up notifications
- **[Guide](features/notifications/GUIDE.md)** - Complete notification guide
- **[Developer Guide](features/notifications/DEVELOPER.md)** - Custom integrations

### MCP Server
Model Context Protocol integration for AI assistants.
- **[Index](features/mcp-server/INDEX.md)** - MCP overview
- **[README](features/mcp-server/README.md)** - Getting started
- **[Setup](features/mcp-server/SETUP.md)** - Installation and configuration
- **[Examples](features/mcp-server/EXAMPLES.md)** - Usage examples
- **[Quick Reference](features/mcp-server/QUICK_REFERENCE.md)** - Command cheat sheet

### SEO Optimizer
Search engine optimization analysis.
- **[README](features/seo-optimizer/README.md)** - SEO optimizer overview
- **[Usage Guide](features/seo-optimizer/USAGE.md)** - How to use
- **[Quick Commands](features/seo-optimizer/QUICK_COMMANDS.md)** - Common commands
- **[Examples](features/seo-optimizer/EXAMPLES.md)** - Real-world examples

### LLM Optimizer
AI-powered content analysis and suggestions.
- **[README](features/llm-optimizer/README.md)** - LLM optimizer overview
- **[Quick Start](features/llm-optimizer/QUICK_START.md)** - Get started
- **[Examples](features/llm-optimizer/EXAMPLES.md)** - Usage examples

### Pattern Library
Pre-built patterns for common issues.
- **[Index](features/pattern-library/INDEX.md)** - Pattern library overview
- **[Guide](features/pattern-library/GUIDE.md)** - Using patterns
- **[Quick Reference](features/pattern-library/QUICK_REFERENCE.md)** - Pattern cheat sheet

### Web Dashboard
Browser-based results viewer.
- **[Guide](features/web-dashboard/GUIDE.md)** - Dashboard usage
- **[Quick Start](features/web-dashboard/QUICK_START.md)** - Launch the dashboard

---

## Examples

- **[Command Examples](examples/COMMANDS.md)** - Common command patterns

---

## Development

### For Contributors
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute code
- **[Testing Guide](development/TESTING.md)** - Running test suite
- **[UX Testing Guide](development/UX_TESTING.md)** - User experience testing
- **[Bug Finder Tests](development/BUG_FINDER_TESTS.md)** - Bug finder test suite

### Technical Documentation
- **[Design Document](design.md)** - Original architecture design
- **[Bootstrap Guide](bootstrap.md)** - Template adoption
- **[Harness Guide](harness-guide.md)** - Development harness
- **[Reference Project Analysis](reference-project-analysis.md)** - Analysis methodology

### Project Management
- **[Feature Roadmap](../feature_list.json)** - 127 planned features
- **[Progress Tracking](../claude-progress.txt)** - Session notes and progress

---

## Archive

Historical documentation preserved for reference:
- **[archived/](archived/)** - Old documentation versions
- **[archived/implementation-notes/](archived/implementation-notes/)** - Implementation summaries
- **[archived/summaries/](archived/summaries/)** - Project summaries

---

## Quick Navigation

### By Task

**I want to...**

- **Find visual bugs** - [Bug Finder Guide](guides/BUG_FINDER.md)
- **Find deprecated code** - [Migration Scanner Guide](guides/MIGRATION_SCANNER.md)
- **Manage multiple sites** - [Projects Guide](guides/PROJECTS.md)
- **Schedule automated scans** - [Scheduler Quick Start](features/scheduler/QUICK_START.md)
- **Set up notifications** - [Notifications Quick Start](features/notifications/QUICK_START.md)
- **Use with AI assistants** - [MCP Server Setup](features/mcp-server/SETUP.md)
- **Analyze SEO** - [SEO Optimizer](features/seo-optimizer/README.md)
- **Use pre-built patterns** - [Pattern Library](features/pattern-library/INDEX.md)
- **Contribute code** - [Contributing Guide](../CONTRIBUTING.md)

### By Audience

**I am a...**

- **New User** - Read [Quick Start](../QUICKSTART.md) then [Main README](../README.md)
- **Website Manager** - Read [Bug Finder](guides/BUG_FINDER.md) and [Migration Scanner](guides/MIGRATION_SCANNER.md)
- **DevOps Engineer** - Read [Scheduler](features/scheduler/INDEX.md) and [Notifications](features/notifications/INDEX.md)
- **AI Developer** - Read [MCP Server](features/mcp-server/INDEX.md)
- **Contributor** - Read [Contributing Guide](../CONTRIBUTING.md)

---

## Directory Structure

```
website-analyzer/
├── README.md                    # Main project overview
├── QUICKSTART.md                # 2-minute quick start
├── CONTRIBUTING.md              # Contribution guidelines
├── CLAUDE.md                    # AI assistant instructions
├── AGENTS.md                    # Agent architecture
├── docs/
│   ├── INDEX.md                 # This file
│   ├── guides/                  # Core user guides
│   │   ├── BUG_FINDER.md
│   │   ├── MIGRATION_SCANNER.md
│   │   ├── PROJECTS.md
│   │   └── CLI_USABILITY.md
│   ├── features/                # Advanced feature docs
│   │   ├── scheduler/
│   │   ├── notifications/
│   │   ├── mcp-server/
│   │   ├── seo-optimizer/
│   │   ├── llm-optimizer/
│   │   ├── pattern-library/
│   │   └── web-dashboard/
│   ├── reference/               # Technical reference
│   │   ├── CONFIG.md
│   │   └── CLI_QUICK_REFERENCE.md
│   ├── examples/                # Example code and commands
│   │   └── COMMANDS.md
│   ├── development/             # Development documentation
│   │   ├── TESTING.md
│   │   └── ...
│   └── archived/                # Historical documentation
│       ├── implementation-notes/
│       └── summaries/
├── src/analyzer/                # Main source code
├── tests/                       # Test suite
├── projects/                    # Analysis workspaces
├── feature_list.json            # Feature roadmap
└── claude-progress.txt          # Session memory
```

---

## Getting Help

- **Command help** - Run `python -m src.analyzer.cli --help`
- **Usage issues** - See relevant guide (Bug Finder, Migration Scanner, etc.)
- **Bugs** - Open a GitHub issue
- **Feature requests** - Open a GitHub discussion
- **Contributing** - See [Contributing Guide](../CONTRIBUTING.md)

---

**Last Updated**: 2025-12-12

**Note**: This documentation is maintained alongside the code. Check for updates regularly as the project evolves.
