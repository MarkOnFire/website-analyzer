# Pattern Library System - User Guide

## Overview

The pattern library system allows you to define, manage, and share reusable bug patterns for website scanning. Each pattern is a JSON file containing:

- Regular expressions to detect specific bugs or issues
- Severity levels and categorization
- Examples of where the pattern appears
- Metadata for organization and documentation

## Quick Start

### List Available Patterns

```bash
python3.11 -m src.analyzer.cli bug-finder patterns list
```

Output shows all patterns with their names, descriptions, and severity levels.

For more details:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns list --verbose
python3.11 -m src.analyzer.cli bug-finder patterns list --format json
python3.11 -m src.analyzer.cli bug-finder patterns list --format csv
```

### Test a Pattern

Test a pattern against provided text:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern wordpress_embed_bug \
  --content "field[0] and field_view_mode in HTML"
```

Test a pattern against a file:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --file page.html
```

Test a pattern against a live URL:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --url https://example.com/page
```

### Get a Template

Display a pattern template in JSON:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns template
```

Save template to file:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns template \
  --output my_pattern_template.json
```

## Creating Custom Patterns

### Method 1: Interactive Mode

```bash
python3.11 -m src.analyzer.cli bug-finder patterns add
```

Follow the prompts to:
1. Enter pattern name (e.g., `my_custom_bug`)
2. Enter description
3. Enter regex patterns (one per line, blank line to finish)
4. Enter example matches (one per line)
5. Add tags for organization
6. Set author name
7. Optionally test the pattern immediately

### Method 2: From Saved JSON File

Create a JSON file with pattern definition:

```json
{
  "name": "custom_pattern",
  "description": "Detects my specific bug",
  "patterns": [
    "regex_pattern_1",
    "regex_pattern_2"
  ],
  "severity": "high",
  "examples": [
    "Example 1",
    "Example 2"
  ],
  "tags": ["category", "tags"],
  "author": "Your Name"
}
```

Then load it:
```bash
python3.11 -m src.analyzer.cli bug-finder patterns add \
  --file my_pattern.json
```

### Method 3: Using Template File

```bash
# Get template
python3.11 -m src.analyzer.cli bug-finder patterns template \
  --output pattern_template.json

# Edit the file with your pattern details
# Then load it
python3.11 -m src.analyzer.cli bug-finder patterns add \
  --file pattern_template.json
```

## Using Patterns in Scans

### Scan with Single Pattern

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --max-pages 500
```

### Scan with Multiple Patterns

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --pattern-file missing_alt_text \
  --pattern-file broken_image_tag \
  --max-pages 500
```

### Scan with All Patterns

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --load-all-patterns \
  --max-pages 500
```

### Scan with Example URL and Custom Pattern

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --example-url https://archive.org/web/*/example.com/page \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --max-pages 1000
```

## Built-in Patterns

### wordpress_embed_bug (High Severity)

**What it detects:** WordPress embed field arrays rendered as visible text

**Use cases:**
- Sites using Drupal field arrays improperly serialized
- WordPress embed code appearing in content instead of being rendered
- Field metadata leaking into page content

**Regex patterns:**
- `field\[[^\]]*\]` - Field array notation
- `field_view_mode` - Field view mode metadata
- `\[\{\s*["']fid["']` - Field ID structures
- `field_image_caption\[` - Image caption fields
- `field_file_image` - File image field references

**Examples:**
```
field[0]
field_view_mode="full_width"
[{"fid":"1101026","view_mode":"full_width"
field_image_caption[und][0][value]
```

### missing_alt_text (Medium Severity)

**What it detects:** Images missing alt text attributes

**Use cases:**
- Accessibility audits (WCAG compliance)
- SEO optimization
- Finding forgotten alt attributes

**Regex patterns:**
- `<img(?!\s+[^>]*alt\s*=)[^>]*>` - IMG without alt
- `<img\s+src[^>]*(?!alt\s*=)` - IMG with src but no alt
- `<img[^>]*alt\s*=\s*["'][^>]*$` - Unclosed alt attributes
- And others for various malformed cases

**Examples:**
```html
<img src="image.jpg">
<img src="photo.png" alt="">
<img src="test.gif" alt='' >
<img width="100" src="pic.jpg" height="100">
```

### broken_image_tag (Medium Severity)

**What it detects:** Malformed or broken image tags

**Use cases:**
- Finding rendering issues
- Identifying broken markup
- Detecting JavaScript/data URLs in img src

**Regex patterns:**
- Detects missing src attributes
- Detects invalid JavaScript URLs
- Detects empty src values
- Detects malformed attribute combinations

**Examples:**
```html
<img alt="test">
<img src="" alt="broken">
<img src="javascript:void(0)">
<img src="about:blank">
```

### deprecated_html_tags (Low Severity)

**What it detects:** Deprecated HTML tags that should be modernized

**Use cases:**
- HTML5 migration projects
- Code modernization
- Best practices enforcement

**Deprecated tags found:**
- `<center>` - use CSS flexbox
- `<font>` - use CSS color property
- `<marquee>` - use CSS animations
- `<blink>` - removed from standards
- `<big>`, `<strike>`, `<tt>`, `<u>` (when not in semantic contexts)
- `<basefont>`, `<dir>`

**Examples:**
```html
<center>Centered text</center>
<font color="red">Red text</font>
<marquee>Scrolling text</marquee>
<blink>Blinking content</blink>
<strike>Strikethrough</strike>
```

## Pattern File Locations

Patterns are stored in:
```
/Users/mriechers/Developer/website-analyzer/patterns/
```

Each pattern is a separate JSON file:
- `wordpress_embed_bug.json`
- `missing_alt_text.json`
- `broken_image_tag.json`
- `deprecated_html_tags.json`
- `<your_custom_patterns>.json`

## Pattern JSON Schema

```json
{
  "name": "string",
  "description": "string (50-200 chars recommended)",
  "patterns": ["regex1", "regex2"],
  "severity": "low|medium|high|critical",
  "examples": ["example1", "example2"],
  "tags": ["optional", "array"],
  "author": "string (optional)",
  "notes": "string (optional)"
}
```

### Field Descriptions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| name | Yes | string | Unique identifier (lowercase, underscores) |
| description | Yes | string | What the pattern detects |
| patterns | Yes | array | List of regex patterns to match |
| severity | Yes | string | low, medium, high, or critical |
| examples | Yes | array | Examples where pattern appears |
| tags | No | array | Categorization tags |
| author | No | string | Creator name |
| notes | No | string | Usage notes and remediation advice |

## Regex Tips

### Best Practices

1. **Be specific**: Avoid overly broad patterns
2. **Test first**: Validate regex before adding
3. **Use character classes**: `[a-z]`, `\d`, `\s` instead of `.`
4. **Escape special characters**: `.` → `\.`, `[` → `\[`
5. **Non-greedy matching**: Use `.*?` instead of `.*` around delimiters

### Common Patterns

```regex
# Match HTML tags
<tagname[^>]*>

# Match quoted strings
["']([^"']*)['"']

# Match brackets/braces
\[([^\]]*)\]
\{([^}]*)\}

# Match URLs
https?://[^\s<>"{}|\\^`\[\]]*

# Match field arrays
field\[[^\]]*\]

# Lookahead/lookbehind
(?<!\w)..(?!\w)  # not preceded/followed by word char
(?=[^>]*alt)     # followed by alt attribute
(?![^>]*alt)     # not followed by alt attribute
```

## Troubleshooting

### Pattern Not Loading

```bash
python3.11 -m src.analyzer.cli bug-finder patterns list
```

If a pattern shows an error, it has validation issues. Common problems:
- Invalid regex syntax
- Missing required fields
- Invalid severity value

### Pattern Matching Too Much

1. Check regex specificity
2. Add boundary checks: `(?<!\w)..(?!\w)`
3. Be more specific about context

### Pattern Not Matching Anything

1. Verify test content contains what you're looking for
2. Remember: patterns are case-insensitive by default
3. Test regex in isolation first

## Advanced Usage

### Pattern Testing Workflow

1. Create pattern from template
2. Test with examples: `--content` flag
3. Test with file: `--file` flag
4. Test with real URL: `--url` flag
5. Refine regexes as needed
6. Save final version

### Organizing Patterns by Category

Use tags effectively:
```json
{
  "tags": ["accessibility", "wcag", "a11y"]
}
```

Then document in README which patterns to use for:
- Accessibility audits
- SEO optimization
- Security reviews
- Modernization projects

### Sharing Patterns

To share a pattern:
1. Save as JSON in patterns/ directory
2. Include comprehensive examples
3. Add notes about remediation
4. Commit to git
5. Share the file with team

## Command Reference

```bash
# List commands
python3.11 -m src.analyzer.cli bug-finder patterns --help

# List patterns
python3.11 -m src.analyzer.cli bug-finder patterns list [--verbose] [--format json|csv|table]

# Create pattern
python3.11 -m src.analyzer.cli bug-finder patterns add [--file <path>]

# Test pattern
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern <name> \
  [--content <text> | --file <path> | --url <url>]

# Get template
python3.11 -m src.analyzer.cli bug-finder patterns template [--output <path>] [--format json|yaml]

# Scan with pattern(s)
python3.11 -m src.analyzer.cli bug-finder scan \
  --site <url> \
  [--pattern-file <name>] \
  [--load-all-patterns] \
  [--max-pages <num>]
```

## Examples

### Example 1: Find All Missing Alt Text

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --pattern-file missing_alt_text \
  --max-pages 1000
```

### Example 2: Accessibility Audit with Multiple Patterns

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --pattern-file missing_alt_text \
  --pattern-file broken_image_tag \
  --max-pages 1000
```

### Example 3: Full Site Audit with All Patterns

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --load-all-patterns \
  --max-pages 5000
```

### Example 4: Custom Pattern Workflow

```bash
# 1. Get template
python3.11 -m src.analyzer.cli bug-finder patterns template \
  --output my_bug.json

# 2. Edit my_bug.json with your pattern details

# 3. Test the pattern
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern my_bug \
  --content "Test content with your bug"

# 4. Use in scan
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --pattern-file my_bug \
  --max-pages 500
```

## Debugging Patterns

### Test Pattern Step-by-Step

1. Test individual regex in online regex editor
2. Test pattern with `patterns test --content`
3. Test with real HTML file: `patterns test --file`
4. Test with live URL: `patterns test --url`
5. Adjust regex and repeat

### Export and Analyze Results

```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file my_pattern \
  --max-pages 100 \
  --format json

# Results in: projects/example-com/scans/bug_results_example-com.json
```

## See Also

- `/Users/mriechers/Developer/website-analyzer/patterns/README.md` - Pattern directory documentation
- `/Users/mriechers/Developer/website-analyzer/src/analyzer/pattern_library.py` - Pattern library implementation
- `/Users/mriechers/Developer/website-analyzer/src/analyzer/cli.py` - CLI command implementations
