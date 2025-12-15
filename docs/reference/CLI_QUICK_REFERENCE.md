# Bug Finder CLI - Quick Reference

Fast lookup for all commands and options.

## Setup

```bash
# Check environment is set up
python -m src.analyzer.cli bug-finder doctor

# Install shell completions (optional, but recommended)
bash scripts/install_completion.sh
```

## Main Commands

| Command | Purpose | Basic Usage |
|---------|---------|------------|
| `scan` | Find bugs across website | `bug-finder scan --example-url <url> --site <site>` |
| `list-scans` | View scan history | `bug-finder list-scans` |
| `doctor` | Check environment | `bug-finder doctor` |
| `compare` | Compare two scans | `bug-finder compare` |
| `export` | Export results | `bug-finder export --input <file>` |
| `patterns` | Manage patterns | `bug-finder patterns list` |
| `config-example` | Generate config | `bug-finder config-example` |

## Scan Command - Full Options

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url <url>           # URL showing the bug (required)
  --site <url>                  # Site to scan (required)
  --max-pages <num>             # Pages to scan (default: 1000)
  --bug-text <text>             # Bug text (instead of extracting)
  --output <path>               # Output file path
  --format <fmt>                # Format: txt, csv, html, json, all
  --config <file>               # Config file with defaults
  --incremental/-i              # Progressive output
  --pattern-file <name>         # Custom pattern
  --load-all-patterns           # Load all patterns
  --quiet/-q                    # Minimal output
  --verbose/-v                  # Detailed output
  --dry-run                     # Preview without running
```

## List-Scans Command

```bash
python -m src.analyzer.cli bug-finder list-scans \
  --limit <num>                 # Show last N scans (default: 20)
  --status <status>             # Filter: running, completed, error, etc.
```

## Scan Statuses

| Status | Meaning |
|--------|---------|
| `running` | Scan in progress |
| `completed` | Scan done, bugs found |
| `completed_clean` | Scan done, no bugs |
| `error` | Scan failed |

## Common Workflows

### Test Before Running
```bash
# Dry-run to validate settings
bug-finder scan --example-url <url> --site <site> --dry-run

# If settings look good, run without --dry-run
bug-finder scan --example-url <url> --site <site>
```

### Track Progress
```bash
# First baseline scan
bug-finder scan --example-url <old-url> --site <site> --max-pages 1000

# Later scan
bug-finder scan --example-url <old-url> --site <site> --max-pages 1000

# Compare
bug-finder list-scans
bug-finder compare
```

### Full Formats
```bash
# Export in all formats
bug-finder scan --site <site> --format all

# Then export to Slack-friendly format
bug-finder export --input results.json --format slack
```

### Use Config File
```bash
# Generate example config
bug-finder config-example

# Edit config file with your defaults
# Then use it:
bug-finder scan --config my-config.json --site <site>
```

## Shell Completion

After installation, use TAB:

```bash
# Bash
bug-finder scan --[TAB]           # Shows available options
bug-finder scan --format [TAB]    # Shows: txt csv html json all

# Zsh
bug-finder scan --[TAB]           # Shows options with descriptions
```

## Output Formats

| Format | Best For | Extension |
|--------|----------|-----------|
| `txt` | Human reading | `.txt` |
| `csv` | Spreadsheet apps | `.csv` |
| `html` | Web viewing | `.html` |
| `json` | Scripting | `.json` |
| `all` | All of above | multiple files |
| `markdown` | Documentation | `.md` |
| `slack` | Chat/Slack | `.txt` |

## Error Messages & Fixes

| Error | Suggestion |
|-------|-----------|
| "URL not found" | Check URL is public, try web.archive.org |
| "Timeout" | Reduce `--max-pages`, check internet |
| "Memory error" | Reduce pages, use `--incremental` |
| "Regex error" | Simplify bug text, avoid special chars |

## File Locations

| Item | Location |
|------|----------|
| Scan registry | `~/.bug-finder/scans.json` |
| Results | `projects/<site>/scans/` |
| Completions | System completion dirs |

## Shortcuts

```bash
# Create alias for frequent use
alias bf='python -m src.analyzer.cli bug-finder'

# Then use:
bf scan --example-url <url> --site <site>
bf list-scans
bf doctor
```

## Help

```bash
# Main help
bug-finder --help

# Command help
bug-finder scan --help
bug-finder list-scans --help
bug-finder doctor --help
bug-finder compare --help
```

## Pro Tips

1. **Always dry-run first**: `--dry-run` validates settings at no cost
2. **Check doctor regularly**: After updates or if issues arise
3. **Use config files**: For repeated scans with same settings
4. **Compare over time**: Track bug fix progress
5. **Filter scans**: `--status error` to find problematic scans
6. **Enable completions**: Makes typing faster and less error-prone

## When Things Go Wrong

```bash
# 1. Check environment
python -m src.analyzer.cli bug-finder doctor

# 2. Try dry-run
python -m src.analyzer.cli bug-finder scan \
  --example-url <url> --site <site> --dry-run

# 3. Check scan history
python -m src.analyzer.cli bug-finder list-scans --status error

# 4. Use --verbose for details
python -m src.analyzer.cli bug-finder scan \
  --example-url <url> --site <site> --verbose
```

---

For detailed guides, see:
- `CLI_USABILITY_GUIDE.md` - Full documentation
- `USABILITY_IMPROVEMENTS_SUMMARY.md` - Features overview
