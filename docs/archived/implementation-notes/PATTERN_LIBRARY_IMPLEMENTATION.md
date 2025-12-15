# Pattern Library System - Implementation Summary

## Overview

A complete pattern library system has been implemented for the website analyzer, allowing users to define, manage, share, and test custom bug patterns. The system is modular, extensible, and fully integrated with the bug-finder CLI.

## Architecture

### Core Components

1. **Pattern Library Module** (`src/analyzer/pattern_library.py`)
   - `Pattern` dataclass: Represents a single pattern with validation
   - `PatternLibrary` class: Manages loading, saving, and testing patterns
   - Full validation and error handling

2. **CLI Commands** (integrated into `src/analyzer/cli.py`)
   - `patterns list` - Show available patterns
   - `patterns add` - Create new patterns interactively
   - `patterns test` - Test patterns against content/URLs
   - `patterns template` - Get pattern template

3. **Pattern Storage** (`patterns/` directory)
   - JSON format for easy sharing and version control
   - 4 built-in example patterns
   - Extensible for community contributions

## Files Created/Modified

### New Files Created

1. **`src/analyzer/pattern_library.py`** (11 KB)
   - Core pattern management system
   - Pattern validation and testing
   - URL fetching integration with crawl4ai
   - Regex compilation and matching

2. **`patterns/` directory**
   - `patterns/README.md` - Comprehensive pattern directory documentation
   - `patterns/wordpress_embed_bug.json` - WPR embed bug pattern
   - `patterns/broken_image_tag.json` - Malformed image tags
   - `patterns/missing_alt_text.json` - Accessibility pattern
   - `patterns/deprecated_html_tags.json` - HTML5 modernization pattern

3. **`PATTERN_LIBRARY_GUIDE.md`** (8 KB)
   - Complete user guide with examples
   - Pattern testing workflows
   - Built-in pattern documentation
   - Regex tips and troubleshooting

4. **`PATTERN_LIBRARY_IMPLEMENTATION.md`** (this file)
   - Technical implementation details
   - Architecture overview
   - Usage examples

### Modified Files

1. **`src/analyzer/cli.py`**
   - Added `import re` for regex validation in CLI
   - Added `patterns_app` subcommand group
   - Added 5 new commands:
     - `@patterns_app.command("list")` - List patterns
     - `@patterns_app.command("add")` - Create patterns
     - `@patterns_app.command("test")` - Test patterns
     - `@patterns_app.command("template")` - Show template
     - Root `patterns` command for help
   - Extended `bug-finder scan` with:
     - `--pattern-file` option (multi-value)
     - `--load-all-patterns` flag
     - Documentation in docstring

## Pattern JSON Schema

```json
{
  "name": "string",                    // Required: unique identifier
  "description": "string",             // Required: what it detects
  "patterns": ["regex1", "regex2"],    // Required: list of regexes
  "severity": "low|medium|high|critical", // Required: impact level
  "examples": ["example1"],            // Required: at least one example
  "tags": ["tag1"],                    // Optional: categorization
  "author": "string",                  // Optional: creator name
  "notes": "string",                   // Optional: usage notes
  "created_at": "ISO timestamp",       // Auto-set on creation
  "updated_at": "ISO timestamp"        // Auto-updated on save
}
```

## Built-in Patterns

### 1. wordpress_embed_bug (High Severity)
- **Purpose**: Detects WordPress/Drupal field arrays in rendered content
- **Patterns**: 5 regex patterns for field notation, view modes, and arrays
- **Tags**: wordpress, drupal, embed, serialization, visual-bug
- **Example**: `field[0]`, `field_view_mode`, `[{"fid":"..."`

### 2. missing_alt_text (Medium Severity)
- **Purpose**: Finds images missing alt attributes
- **Patterns**: 5 regex patterns for various img tag malformations
- **Tags**: accessibility, a11y, seo, compliance, wcag
- **Example**: `<img src="test.jpg">` (no alt attribute)

### 3. broken_image_tag (Medium Severity)
- **Purpose**: Detects malformed or broken image tags
- **Patterns**: 5 regex patterns for missing/invalid src attributes
- **Tags**: html, images, accessibility, rendering
- **Example**: `<img alt="test">` (missing src), `<img src="">`

### 4. deprecated_html_tags (Low Severity)
- **Purpose**: Identifies deprecated HTML tags for modernization
- **Patterns**: 10 regex patterns for deprecated tags
- **Tags**: html, semantic, modernization, deprecation, html5
- **Examples**: `<center>`, `<font>`, `<marquee>`, `<blink>`, etc.

## CLI Command Examples

### List Patterns

```bash
# Basic list
python3.11 -m src.analyzer.cli bug-finder patterns list

# Verbose with details
python3.11 -m src.analyzer.cli bug-finder patterns list --verbose

# JSON output for automation
python3.11 -m src.analyzer.cli bug-finder patterns list --format json

# CSV for spreadsheet analysis
python3.11 -m src.analyzer.cli bug-finder patterns list --format csv
```

### Create Patterns

```bash
# Interactive mode (guided)
python3.11 -m src.analyzer.cli bug-finder patterns add

# From existing JSON file
python3.11 -m src.analyzer.cli bug-finder patterns add --file my_pattern.json

# With specific values (partial)
python3.11 -m src.analyzer.cli bug-finder patterns add \
  --name "my_pattern" \
  --description "My pattern description" \
  --severity high
```

### Test Patterns

```bash
# Test with inline content
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern wordpress_embed_bug \
  --content "field[0] and field_view_mode"

# Test with HTML file
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --file page.html

# Test with live URL
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --url https://example.com/page
```

### Get Template

```bash
# Display template
python3.11 -m src.analyzer.cli bug-finder patterns template

# Save to file
python3.11 -m src.analyzer.cli bug-finder patterns template \
  --output my_pattern.json

# YAML format
python3.11 -m src.analyzer.cli bug-finder patterns template \
  --format yaml --output my_pattern.yaml
```

### Scan with Patterns

```bash
# Scan with single pattern
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --max-pages 500

# Scan with multiple patterns
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --pattern-file missing_alt_text \
  --pattern-file broken_image_tag

# Scan with all patterns
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --load-all-patterns \
  --max-pages 1000

# Scan with example URL and custom pattern
python3.11 -m src.analyzer.cli bug-finder scan \
  --example-url https://archive.org/web/*/example.com/page \
  --site https://example.com \
  --pattern-file wordpress_embed_bug
```

## Key Features

### 1. Pattern Validation
- All patterns validated on creation and load
- Regex syntax checking with detailed error messages
- Required field validation
- Severity enum validation
- Automatic timestamp management

### 2. Flexible Testing
- Test against inline text content
- Test against HTML/text files
- Test against live URLs (requires crawl4ai)
- Match counting and sampling
- Pattern-by-pattern breakdown

### 3. Interactive Creation
- Guided wizard for pattern creation
- Real-time regex validation
- Example verification on save
- Optional immediate testing

### 4. Multi-Format Output
- Table format with color-coded severity
- JSON output for automation
- CSV export for spreadsheets
- Verbose mode for detailed info

### 5. Pattern Library Management
- List available patterns with metadata
- Search/filter by name (via shell commands)
- View pattern details
- Test before using
- Share via git/version control

## Implementation Details

### Pattern Class

```python
@dataclass
class Pattern:
    name: str
    description: str
    patterns: List[str]
    severity: str
    examples: List[str]
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None
```

Features:
- Dataclass for easy JSON serialization
- `validate()` method returns (is_valid, error_list)
- `to_dict()` for JSON output
- `from_dict()` for JSON parsing

### PatternLibrary Class

Key methods:
- `list_patterns()` - Get all patterns with metadata
- `load_pattern_file(path)` - Load from JSON file
- `load_pattern_by_name(name)` - Find pattern by name
- `load_all_patterns()` - Load entire library
- `save_pattern(pattern, filename)` - Save with auto-timestamps
- `test_pattern_on_content(pattern, text)` - Test against content
- `test_pattern_on_url(pattern, url)` - Fetch and test URL
- `validate()` - Validate pattern structure
- `get_pattern_template()` - Return template dict

### CLI Integration

Pattern commands are registered as a sub-app:
```python
patterns_app = typer.Typer(...)
bug_finder_app.add_typer(patterns_app)
```

Each command:
- Uses Rich console for formatted output
- Proper error handling with user-friendly messages
- Comprehensive docstrings with examples
- Type hints for IDE support

## Extensibility

### Adding New Built-in Patterns

1. Create JSON file in `patterns/` directory
2. Ensure valid schema
3. Test with `patterns test` command
4. Commit to git
5. Update patterns/README.md

### Custom Pattern Workflow

1. User runs `patterns add` or creates JSON
2. Pattern validation occurs
3. Optional testing before save
4. Pattern saved to `patterns/` directory
5. Available for immediate use in scans

### Community Patterns

Repository maintainers can:
1. Accept pull requests with new patterns
2. Validate patterns before merge
3. Document in patterns/README.md
4. Reference in PATTERN_LIBRARY_GUIDE.md

## Testing

All commands tested and verified:

```bash
# List commands
python3.11 -m src.analyzer.cli bug-finder patterns list
python3.11 -m src.analyzer.cli bug-finder patterns list --verbose
python3.11 -m src.analyzer.cli bug-finder patterns list --format json

# Test patterns
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern wordpress_embed_bug \
  --content "field[0]"

python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --file test.html

python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern deprecated_html_tags \
  --url https://example.com

# Template
python3.11 -m src.analyzer.cli bug-finder patterns template
```

## File Locations

```
/Users/mriechers/Developer/website-analyzer/
├── patterns/
│   ├── README.md                          (Pattern directory guide)
│   ├── wordpress_embed_bug.json            (Built-in pattern)
│   ├── broken_image_tag.json               (Built-in pattern)
│   ├── missing_alt_text.json               (Built-in pattern)
│   └── deprecated_html_tags.json           (Built-in pattern)
├── src/analyzer/
│   ├── pattern_library.py                  (Core implementation)
│   └── cli.py                              (Pattern CLI commands)
├── PATTERN_LIBRARY_GUIDE.md                (User guide)
└── PATTERN_LIBRARY_IMPLEMENTATION.md       (This file)
```

## Dependencies

- `typer` - CLI framework (existing)
- `pathlib` - File system access (stdlib)
- `json` - Pattern serialization (stdlib)
- `re` - Regex support (stdlib)
- `dataclasses` - Pattern class definition (stdlib)
- `datetime` - Timestamp management (stdlib)
- `crawl4ai` - Optional for URL testing (existing)
- `rich` - Console output (existing)

No additional dependencies required!

## Performance Considerations

### Pattern Testing
- Regex compilation happens once per test
- Matches limited to first 5 per pattern for efficiency
- Large files handled gracefully
- URL fetching uses async (via crawl4ai)

### Scanning
- Patterns can be loaded once and reused
- Multiple patterns tested in single pass
- Results are accumulated efficiently
- No memory accumulation issues

## Security Considerations

### Regex Injection
- All user regexes are compiled with `re.compile()`
- No eval() or exec() used
- Invalid regexes caught and reported

### File Operations
- Path validation on all file operations
- User permissions respected
- No symlink traversal issues

### URL Handling
- URL validation in docstrings
- Timeout handling via crawl4ai
- Safe async implementation

## Future Enhancements

Potential additions:
1. Pattern tagging system for organization
2. Pattern versioning for tracking changes
3. Pattern performance metrics/benchmarks
4. Community pattern repository
5. Pattern composition (combining patterns)
6. Scheduled pattern testing
7. Pattern statistics (usage, effectiveness)
8. Web UI for pattern management

## Summary

A production-ready pattern library system has been successfully implemented with:

- 4 built-in patterns for common issues
- Full CLI integration with 5+ commands
- Comprehensive user documentation
- Interactive pattern creation
- Pattern testing and validation
- Extensible architecture for custom patterns
- Git-friendly JSON format
- Zero additional dependencies

Users can now easily create, test, and share bug patterns across the organization!
