# Pattern Library - Quick Reference

## Most Common Commands

### View Available Patterns
```bash
python3.11 -m src.analyzer.cli bug-finder patterns list
```

### Test a Pattern
```bash
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern wordpress_embed_bug \
  --content "Your test content here"
```

### Scan Website with Pattern
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
  --max-pages 500
```

### Create Custom Pattern
```bash
python3.11 -m src.analyzer.cli bug-finder patterns add
```

## Built-in Patterns

| Pattern | Severity | Purpose | Tags |
|---------|----------|---------|------|
| `wordpress_embed_bug` | HIGH | Detect unrendered WordPress embed code | wordpress, drupal |
| `missing_alt_text` | MEDIUM | Find images without alt attributes | accessibility, a11y |
| `broken_image_tag` | MEDIUM | Detect malformed img tags | html, images |
| `deprecated_html_tags` | LOW | Find old HTML tags needing modernization | html, semantic |

## All Pattern Commands

```bash
# List
python3.11 -m src.analyzer.cli bug-finder patterns list
python3.11 -m src.analyzer.cli bug-finder patterns list --verbose
python3.11 -m src.analyzer.cli bug-finder patterns list --format json

# Create
python3.11 -m src.analyzer.cli bug-finder patterns add

# Test
python3.11 -m src.analyzer.cli bug-finder patterns test --pattern NAME --content TEXT
python3.11 -m src.analyzer.cli bug-finder patterns test --pattern NAME --file FILE.html
python3.11 -m src.analyzer.cli bug-finder patterns test --pattern NAME --url https://example.com

# Template
python3.11 -m src.analyzer.cli bug-finder patterns template
python3.11 -m src.analyzer.cli bug-finder patterns template --output my_pattern.json
```

## Pattern File Format

```json
{
  "name": "my_pattern",
  "description": "What this detects",
  "patterns": ["regex1", "regex2"],
  "severity": "high",
  "examples": ["example text"],
  "tags": ["category"],
  "author": "Your Name"
}
```

## Common Regex Patterns

```regex
# HTML tags
<tagname[^>]*>

# HTML attributes
attribute\s*=\s*["'][^"']*["']

# Field arrays
field\[[^\]]*\]

# Quoted strings
["']([^"']*)['"']

# Deprecated tags
<center|<font|<marquee|<blink
```

## Scan Options

| Option | Usage |
|--------|-------|
| `--site URL` | Website to scan (required) |
| `--pattern-file NAME` | Load pattern (can specify multiple times) |
| `--load-all-patterns` | Use all available patterns |
| `--max-pages N` | Maximum pages to scan (default: 1000) |
| `--incremental` | Write results as they're found |
| `--format FORMAT` | Output format: txt, json, csv, html, all |

## Examples

### Find accessibility issues
```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --pattern-file missing_alt_text \
  --pattern-file broken_image_tag
```

### Modernize deprecated HTML
```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mysite.com \
  --pattern-file deprecated_html_tags \
  --max-pages 5000
```

### Find WordPress rendering bugs
```bash
python3.11 -m src.analyzer.cli bug-finder scan \
  --site https://mywordpresssite.com \
  --pattern-file wordpress_embed_bug \
  --incremental
```

## File Locations

- **Patterns:** `/Users/mriechers/Developer/website-analyzer/patterns/`
- **Pattern Library Code:** `/Users/mriechers/Developer/website-analyzer/src/analyzer/pattern_library.py`
- **CLI Code:** `/Users/mriechers/Developer/website-analyzer/src/analyzer/cli.py`

## Troubleshooting

**Pattern not found?**
```bash
python3.11 -m src.analyzer.cli bug-finder patterns list
```

**Want to test a pattern first?**
```bash
python3.11 -m src.analyzer.cli bug-finder patterns test \
  --pattern pattern_name \
  --content "test content"
```

**Invalid regex?**
- Use an online regex tester first
- Test with `patterns test` command
- Check `patterns list` for validation errors

## Next Steps

1. **Browse patterns:** `patterns list --verbose`
2. **Test a pattern:** `patterns test --pattern NAME --content "..."`
3. **Use in scan:** `scan --site URL --pattern-file NAME`
4. **Create custom:** `patterns add` then follow prompts
5. **Share with team:** Commit to git, push to repo

## Documentation

- **Full Guide:** See `PATTERN_LIBRARY_GUIDE.md`
- **Pattern Details:** See `patterns/README.md`
- **Implementation:** See `PATTERN_LIBRARY_IMPLEMENTATION.md`
