# Documentation Map

Quick reference for finding documentation in the Website Analyzer project.

---

## Root Level Files

| File | Purpose |
|------|---------|
| **[README.md](README.md)** | Main project overview, features, installation, quick start |
| **[QUICKSTART.md](QUICKSTART.md)** | 2-minute guide to your first scan |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | How to contribute code, report bugs, request features |
| **[CLAUDE.md](CLAUDE.md)** | Instructions for AI assistants working on this codebase |
| **[AGENTS.md](AGENTS.md)** | Agent architecture and collaboration patterns |

---

## Getting Started Path

```
1. README.md          - Understand what the project does
       |
2. QUICKSTART.md      - Run your first scan in 2 minutes
       |
3. Pick your tool:
   ├── docs/guides/BUG_FINDER.md        - Find visual bugs
   └── docs/guides/MIGRATION_SCANNER.md - Find deprecated patterns
```

---

## Documentation Structure

### Core User Guides (`docs/guides/`)

| Document | Description |
|----------|-------------|
| [BUG_FINDER.md](docs/guides/BUG_FINDER.md) | Complete bug finder documentation |
| [MIGRATION_SCANNER.md](docs/guides/MIGRATION_SCANNER.md) | Pattern scanning guide |
| [PROJECTS.md](docs/guides/PROJECTS.md) | Project workspace management |
| [CLI_USABILITY.md](docs/guides/CLI_USABILITY.md) | CLI interface overview |

### Reference (`docs/reference/`)

| Document | Description |
|----------|-------------|
| [CONFIG.md](docs/reference/CONFIG.md) | Configuration file reference |
| [CLI_QUICK_REFERENCE.md](docs/reference/CLI_QUICK_REFERENCE.md) | Command cheat sheet |

### Feature Documentation (`docs/features/`)

Each advanced feature has its own directory with complete documentation:

| Feature | Location | Description |
|---------|----------|-------------|
| Scheduler | [docs/features/scheduler/](docs/features/scheduler/) | Automated scan scheduling |
| Notifications | [docs/features/notifications/](docs/features/notifications/) | Alert system |
| MCP Server | [docs/features/mcp-server/](docs/features/mcp-server/) | AI assistant integration |
| SEO Optimizer | [docs/features/seo-optimizer/](docs/features/seo-optimizer/) | SEO analysis |
| LLM Optimizer | [docs/features/llm-optimizer/](docs/features/llm-optimizer/) | AI-powered analysis |
| Pattern Library | [docs/features/pattern-library/](docs/features/pattern-library/) | Pre-built patterns |
| Web Dashboard | [docs/features/web-dashboard/](docs/features/web-dashboard/) | Browser UI |

### Development (`docs/development/`)

| Document | Description |
|----------|-------------|
| [TESTING.md](docs/development/TESTING.md) | Running the test suite |
| [UX_TESTING.md](docs/development/UX_TESTING.md) | User experience testing |
| [BUG_FINDER_TESTS.md](docs/development/BUG_FINDER_TESTS.md) | Bug finder test suite |

### Examples (`docs/examples/`)

| Document | Description |
|----------|-------------|
| [COMMANDS.md](docs/examples/COMMANDS.md) | Common command patterns |

### Archive (`docs/archived/`)

Historical documentation preserved for reference. Not actively maintained.

---

## Quick Reference by Task

| I want to... | Go to... |
|--------------|----------|
| Get started quickly | [QUICKSTART.md](QUICKSTART.md) |
| Find visual bugs | [docs/guides/BUG_FINDER.md](docs/guides/BUG_FINDER.md) |
| Find deprecated code | [docs/guides/MIGRATION_SCANNER.md](docs/guides/MIGRATION_SCANNER.md) |
| Manage multiple sites | [docs/guides/PROJECTS.md](docs/guides/PROJECTS.md) |
| Schedule scans | [docs/features/scheduler/QUICK_START.md](docs/features/scheduler/QUICK_START.md) |
| Set up notifications | [docs/features/notifications/QUICK_START.md](docs/features/notifications/QUICK_START.md) |
| Use with Claude/AI | [docs/features/mcp-server/README.md](docs/features/mcp-server/README.md) |
| Analyze SEO | [docs/features/seo-optimizer/README.md](docs/features/seo-optimizer/README.md) |
| Configure the tool | [docs/reference/CONFIG.md](docs/reference/CONFIG.md) |
| Contribute code | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Run tests | [docs/development/TESTING.md](docs/development/TESTING.md) |

---

## Quick Reference by Audience

| I am a... | Start with... |
|-----------|---------------|
| New user | [QUICKSTART.md](QUICKSTART.md) |
| Website manager | [docs/guides/BUG_FINDER.md](docs/guides/BUG_FINDER.md) |
| Developer | [docs/guides/MIGRATION_SCANNER.md](docs/guides/MIGRATION_SCANNER.md) |
| DevOps engineer | [docs/features/scheduler/INDEX.md](docs/features/scheduler/INDEX.md) |
| AI assistant developer | [docs/features/mcp-server/INDEX.md](docs/features/mcp-server/INDEX.md) |
| Contributor | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## Master Index

For a complete documentation index with all links, see:
- **[docs/INDEX.md](docs/INDEX.md)** - Full documentation index

---

## File Organization

```
website-analyzer/
├── Root Documentation (5 files)
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── CONTRIBUTING.md
│   ├── CLAUDE.md
│   └── AGENTS.md
│
├── docs/
│   ├── INDEX.md              # Master documentation index
│   │
│   ├── guides/               # Core user guides (4 files)
│   │   ├── BUG_FINDER.md
│   │   ├── MIGRATION_SCANNER.md
│   │   ├── PROJECTS.md
│   │   └── CLI_USABILITY.md
│   │
│   ├── features/             # Feature documentation (7 directories)
│   │   ├── scheduler/        # 6 files
│   │   ├── notifications/    # 5 files
│   │   ├── mcp-server/       # 5 files
│   │   ├── seo-optimizer/    # 4 files
│   │   ├── llm-optimizer/    # 3 files
│   │   ├── pattern-library/  # 3 files
│   │   └── web-dashboard/    # 2 files
│   │
│   ├── reference/            # Technical reference (2 files)
│   │   ├── CONFIG.md
│   │   └── CLI_QUICK_REFERENCE.md
│   │
│   ├── examples/             # Examples (1 file)
│   │   └── COMMANDS.md
│   │
│   ├── development/          # Development docs (16 files)
│   │   ├── TESTING.md
│   │   └── ...
│   │
│   └── archived/             # Historical docs
│       ├── implementation-notes/
│       └── summaries/
│
└── Harness Files
    ├── feature_list.json     # Feature roadmap
    ├── claude-progress.txt   # Session memory
    └── init.sh               # Environment setup
```

---

## Documentation Statistics

| Category | Files | Location |
|----------|-------|----------|
| Root documentation | 5 | `/` |
| User guides | 4 | `docs/guides/` |
| Feature docs | ~28 | `docs/features/` |
| Reference docs | 2 | `docs/reference/` |
| Examples | 1 | `docs/examples/` |
| Development docs | 16 | `docs/development/` |
| Archived docs | ~20 | `docs/archived/` |

**Total**: ~76 documentation files organized into a clear hierarchy.

---

**Last Updated**: 2025-12-12
