# Documentation Index

Complete guide to Website Analyzer documentation and resources.

---

## Start Here

### First Time Users
1. **[Quick Start (2 minutes)](../QUICKSTART.md)** - Get your first scan running in under 2 minutes
2. **[Main README](../README.md)** - Project overview and features
3. **[Installation Guide](guides/INSTALLATION.md)** - Detailed setup instructions

### Experienced Users
1. **[Bug Finder Guide](guides/BUG_FINDER.md)** - Complete bug discovery documentation
2. **[Migration Scanner Guide](guides/MIGRATION_SCANNER.md)** - Pattern matching in depth
3. **[Projects & Workspaces](guides/PROJECTS.md)** - Managing multiple sites

---

## User Guides

### Getting Started
- **[Quick Start](../QUICKSTART.md)** - 2-minute introduction (visit first!)
- **[Installation Guide](guides/INSTALLATION.md)** - Setup for all platforms
- **[First Project Setup](guides/FIRST_PROJECT.md)** - Step-by-step walkthrough (coming soon)

### Core Tools
- **[Bug Finder Guide](guides/BUG_FINDER.md)** - Find visual bugs by example
- **[Migration Scanner Guide](guides/MIGRATION_SCANNER.md)** - Find deprecated code patterns
- **[Projects & Workspaces Guide](guides/PROJECTS.md)** - Manage multiple analyses
- **[Configuration Guide](reference/CONFIG.md)** - Settings and customization

### Advanced Topics
- **[Performance Tuning](guides/PERFORMANCE.md)** - Optimize for large sites (coming soon)
- **[CI/CD Integration](guides/CI_CD.md)** - Automated scanning (coming soon)
- **[Custom Plugins](guides/CUSTOM_PLUGINS.md)** - Build your own tests (coming soon)

---

## Examples & Case Studies

### Real-World Examples
- **[WPR.org Case Study](examples/CASE_STUDY_WPR.md)** - 131 WordPress bugs found (coming soon)
- **[Example Workflows](examples/WORKFLOWS.md)** - Common analysis patterns (coming soon)
- **[Pattern Examples](examples/PATTERNS.md)** - Pre-built patterns for common issues (coming soon)

### Code Examples
- **[Python API Usage](examples/API_USAGE.md)** - Programmatic access (coming soon)
- **[Shell Scripts](examples/SCRIPTS.md)** - Automated workflows (coming soon)

---

## Reference

### CLI & Commands
- **[CLI Command Reference](reference/CLI.md)** - All commands explained (coming soon)
- **[Bug Finder Commands](guides/BUG_FINDER.md#cli-usage)** - Bug finder CLI options
- **[Migration Scanner Commands](guides/MIGRATION_SCANNER.md#cli-usage)** - Pattern scanner CLI options
- **[Configuration Guide](reference/CONFIG.md)** - Config file reference

### Architecture
- **[System Architecture](reference/ARCHITECTURE.md)** - Design overview (coming soon)
- **[Plugin System](reference/PLUGINS.md)** - Building test plugins (coming soon)
- **[Data Formats](reference/DATA_FORMATS.md)** - JSON/CSV output specs (coming soon)

### Other Reference
- **[Pattern Library](reference/PATTERNS.md)** - Built-in and custom patterns (coming soon)
- **[API Reference](reference/API.md)** - Python API documentation (coming soon)
- **[FAQ](reference/FAQ.md)** - Frequently asked questions (coming soon)

---

## Development

### For Contributors
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute code
- **[Development Setup](development/SETUP.md)** - Development environment (coming soon)
- **[Testing Guide](development/TESTING.md)** - Running test suite (coming soon)
- **[Code Style](development/CODE_STYLE.md)** - Style guidelines (coming soon)

### Project Management
- **[Feature Roadmap](../feature_list.json)** - 127 planned features
- **[Progress Tracking](../claude-progress.txt)** - Session notes and progress
- **[Development Notes](development/NOTES.md)** - Technical decisions (coming soon)

---

## Archive

### Previous Documentation
- **[Original BUG_FINDER_README.md](../BUG_FINDER_README.md)** - Initial implementation details
- **[MIGRATION_SCANNER_README.md](../MIGRATION_SCANNER_README.md)** - Scanner documentation
- **[Development Notes](development/)** - Implementation details
- **[Brainstorming](../brainstorming/)** - Initial project ideas

---

## Quick Navigation

### By Task

**I want to...**

- **Find visual bugs** → Start with [Bug Finder Guide](guides/BUG_FINDER.md)
- **Find deprecated code** → Start with [Migration Scanner Guide](guides/MIGRATION_SCANNER.md)
- **Manage multiple sites** → Start with [Projects Guide](guides/PROJECTS.md)
- **Set up the tool** → Start with [Installation Guide](guides/INSTALLATION.md)
- **Use it in CI/CD** → See [Contributing Guide](../CONTRIBUTING.md) (feature in progress)
- **Build a custom test** → See [Plugin System](reference/PLUGINS.md)
- **Contribute code** → Start with [Contributing Guide](../CONTRIBUTING.md)

### By Audience

**I am a...**

- **New User** → Read [Quick Start](../QUICKSTART.md) → [Main README](../README.md)
- **Website Manager** → Read [Bug Finder Guide](guides/BUG_FINDER.md) → [Migration Scanner Guide](guides/MIGRATION_SCANNER.md)
- **Developer** → Read [API Reference](reference/API.md) → [Architecture](reference/ARCHITECTURE.md)
- **Contributor** → Read [Contributing Guide](../CONTRIBUTING.md) → [Development Setup](development/SETUP.md)
- **Site Reliability Engineer** → Read [Projects Guide](guides/PROJECTS.md) → Performance tuning docs

---

## Directory Structure

```
website-analyzer/
├── README.md                           # Main project overview
├── QUICKSTART.md                       # 2-minute quick start
├── CONTRIBUTING.md                     # Contribution guidelines
├── docs/
│   ├── INDEX.md                        # This file
│   ├── guides/
│   │   ├── INSTALLATION.md             # Setup instructions
│   │   ├── FIRST_PROJECT.md            # Getting started walkthrough
│   │   ├── BUG_FINDER.md               # Bug finder complete guide
│   │   ├── MIGRATION_SCANNER.md        # Pattern scanner guide
│   │   └── PROJECTS.md                 # Project workspace guide
│   ├── reference/
│   │   ├── CONFIG.md                   # Configuration guide
│   │   ├── CLI.md                      # Command reference (todo)
│   │   ├── ARCHITECTURE.md             # Design overview (todo)
│   │   ├── PLUGINS.md                  # Plugin system (todo)
│   │   ├── PATTERNS.md                 # Pattern library (todo)
│   │   ├── API.md                      # Python API (todo)
│   │   └── FAQ.md                      # FAQ (todo)
│   ├── examples/
│   │   ├── CASE_STUDY_WPR.md           # Real-world example (todo)
│   │   ├── WORKFLOWS.md                # Common workflows (todo)
│   │   ├── PATTERNS.md                 # Pattern examples (todo)
│   │   ├── API_USAGE.md                # Code examples (todo)
│   │   └── SCRIPTS.md                  # Shell scripts (todo)
│   ├── development/
│   │   ├── SETUP.md                    # Dev environment (todo)
│   │   ├── TESTING.md                  # Testing guide (todo)
│   │   ├── CODE_STYLE.md               # Style guidelines (todo)
│   │   └── NOTES.md                    # Technical decisions (todo)
│   ├── architecture/
│   │   └── (Reference from root docs/)
│   ├── bootstrap.md                    # Template adoption (existing)
│   ├── design.md                       # Original design (existing)
│   ├── harness-guide.md                # Template harness (existing)
│   └── archived/                       # Old documentation
│       └── test-project-bug-hunter.md  # Original case study
├── src/analyzer/                       # Main source code
├── tests/                              # Test suite
├── patterns/                           # Pattern library
├── projects/                           # Analysis workspaces
├── feature_list.json                   # Feature roadmap (127 features)
└── claude-progress.txt                 # Session memory
```

---

## Documentation Status

### Complete ✅
- Main README
- Quick Start
- Bug Finder Guide
- Migration Scanner Guide
- Projects & Workspaces Guide
- Configuration Guide
- Contributing Guide

### In Progress 🚀
- Installation Guide
- Example Workflows
- API Reference

### Planned 📋
- CLI Command Reference
- System Architecture
- Plugin System Guide
- Pattern Library
- CI/CD Integration
- Performance Tuning
- Case Studies & Examples

---

## How to Use This Documentation

1. **Start with [Quick Start](../QUICKSTART.md)** - Get running in 2 minutes
2. **Choose your tool** - [Bug Finder](guides/BUG_FINDER.md) or [Migration Scanner](guides/MIGRATION_SCANNER.md)
3. **Refer to guides as needed** - Reference documentation for detailed information
4. **Check examples** - Real-world use cases in examples/ directory
5. **Read the code** - Source code is well-documented with docstrings

---

## Getting Help

- **Quick questions** → Check [FAQ](reference/FAQ.md)
- **Command help** → Run `python -m src.analyzer.cli --help`
- **Usage issues** → See relevant guide (Bug Finder, Migration Scanner, etc.)
- **Bugs** → Open a GitHub issue
- **Feature requests** → Open a GitHub discussion
- **Contributing** → See [Contributing Guide](../CONTRIBUTING.md)

---

## Related Resources

- **GitHub Repository** - https://github.com/yourusername/website-analyzer
- **Issues Tracker** - https://github.com/yourusername/website-analyzer/issues
- **Discussions** - https://github.com/yourusername/website-analyzer/discussions
- **Crawl4AI** - https://github.com/unclecode/crawl4ai (web crawler)
- **Typer** - https://typer.tiangolo.com (CLI framework)
- **Pydantic** - https://docs.pydantic.dev (data validation)

---

**Last Updated**: 2025-12-11

**Note**: This documentation is maintained alongside the code. Check for updates regularly as the project evolves.
