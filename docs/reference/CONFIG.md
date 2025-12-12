# Configuration Guide

Configure default scan settings for the bug-finder tool, reducing command-line complexity and enabling reproducible scans.

**See Also:** [Main README](../../README.md) | [Bug Finder Guide](../guides/BUG_FINDER.md)

---

## Overview

The bug-finder tool supports JSON and YAML configuration files with settings for:

- **Scan Settings**: Default max pages, crawl depth, output formats
- **Output Settings**: Output directory preferences, file naming options
- **Pattern Settings**: Pattern matching configuration (case sensitivity, regex options)
- **Site-Specific Settings**: Per-URL configuration overrides

---

## Configuration Precedence

Settings are applied in this order (highest to lowest priority):

1. **Command-line arguments** (e.g., `--max-pages 500`)
2. **Site-specific settings** (if URL matches in config file)
3. **Default settings** (in `scan_settings` section)

---

## Quick Start

### Generate a Template Config

```bash
python -m src.analyzer.cli bug-finder config-example --output my-config.json
```

This creates a `my-config.json` file with all available options documented.

### Use Your Config

```bash
python -m src.analyzer.cli bug-finder scan \
  --config my-config.json \
  --example-url "https://archive.org/web/.../page-with-bug" \
  --site "https://www.example.com"
```

### Override Config with CLI Args

```bash
python -m src.analyzer.cli bug-finder scan \
  --config my-config.json \
  --site "https://www.example.com" \
  --max-pages 500 \
  --format json
```

The CLI arguments override config file settings.

---

## Configuration File Format

### JSON Example

```json
{
  "scan_settings": {
    "max_pages": 1000,
    "max_depth": null,
    "format": "txt"
  },
  "output_settings": {
    "output_dir": "projects",
    "create_scans_subdir": true,
    "timestamp_results": true
  },
  "pattern_settings": {
    "case_sensitive": false,
    "use_regex": true,
    "min_pattern_length": 5
  },
  "site_specific": {
    "https://www.example.com": {
      "url": "https://www.example.com",
      "max_pages": 500,
      "format": "html"
    }
  }
}
```

### YAML Example

```yaml
# Default settings for all scans
scan_settings:
  max_pages: 1000
  max_depth: null
  format: txt

# Output preferences
output_settings:
  output_dir: projects
  create_scans_subdir: true
  timestamp_results: true

# Pattern matching configuration
pattern_settings:
  case_sensitive: false
  use_regex: true
  min_pattern_length: 5

# Site-specific overrides
site_specific:
  https://www.example.com:
    url: https://www.example.com
    max_pages: 500
    format: html
```

---

## Configuration Sections

### scan_settings

Default scanning parameters applied to all scans.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_pages` | integer | 1000 | Maximum number of pages to scan |
| `max_depth` | integer or null | null | Maximum crawl depth (null = unlimited) |
| `format` | string | "txt" | Output format: txt, csv, html, json, or all |

### output_settings

Control where and how results are saved.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_dir` | string | "projects" | Base directory for storing results |
| `create_scans_subdir` | boolean | true | Create 'scans' subdirectory for results |
| `timestamp_results` | boolean | true | Include timestamp in result filenames |

### pattern_settings

Configure how patterns are generated and matched.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `case_sensitive` | boolean | false | Case-sensitive pattern matching |
| `use_regex` | boolean | true | Enable regex pattern matching |
| `min_pattern_length` | integer | 5 | Minimum characters for auto-generated patterns |

### site_specific

Per-URL configuration overrides. Each key is a site URL, with settings that override defaults for that URL.

---

## Usage Examples

### Example 1: Simple Default Config

Create `scan-defaults.json`:

```json
{
  "scan_settings": {
    "max_pages": 500,
    "format": "html"
  }
}
```

Use:

```bash
python -m src.analyzer.cli bug-finder scan \
  --config scan-defaults.json \
  --example-url "https://archive.org/web/.../bug" \
  --site "https://mysite.com"
```

### Example 2: Site-Specific Settings

Create `multi-site.json`:

```json
{
  "scan_settings": {
    "max_pages": 1000,
    "format": "txt"
  },
  "site_specific": {
    "https://www.wpr.org": {
      "max_pages": 2000,
      "format": "all"
    },
    "https://example.com": {
      "max_pages": 300,
      "format": "json"
    }
  }
}
```

The tool automatically applies site-specific settings when matching the `--site` URL.

### Example 3: Development vs Production

Create `config.development.json`:

```json
{
  "scan_settings": {
    "max_pages": 50,
    "format": "txt"
  }
}
```

Create `config.production.json`:

```json
{
  "scan_settings": {
    "max_pages": 5000,
    "format": "all"
  }
}
```

Use appropriately:

```bash
# Fast development scan
python -m src.analyzer.cli bug-finder scan \
  --config config.development.json \
  --site "https://www.example.com"

# Comprehensive production scan
python -m src.analyzer.cli bug-finder scan \
  --config config.production.json \
  --site "https://www.example.com"
```

---

## Advanced Features

### Dynamic Config Generation

Programmatically create config files:

```python
from src.analyzer.config import ConfigLoader, BugFinderConfig, ScanSettings

config = BugFinderConfig(
    scan_settings=ScanSettings(
        max_pages=2000,
        format="all"
    )
)

ConfigLoader.save(config, "my-config.json", format="json")
```

### Configuration Merging

Load config and merge with CLI overrides:

```python
from src.analyzer.config import ConfigLoader, ConfigMerger

config = ConfigLoader.load("config.json")

merged = ConfigMerger.merge(
    config,
    cli_overrides={'max_pages': 500, 'format': 'json'},
    site_url='https://www.example.com'
)
```

### YAML Support

YAML requires PyYAML:

```bash
pip install PyYAML
```

Then use `.yaml` or `.yml` files:

```bash
python -m src.analyzer.cli bug-finder scan \
  --config config.yaml \
  --example-url "..." \
  --site "..."
```

---

## File Locations

Example configuration files are provided in the repository:

- `config.example.json` - JSON format example with all options
- `config.example.yaml` - YAML format example with all options

Copy and modify these for your use case.

---

## CLI Flag Reference

### --config (-c)

Load settings from configuration file.

```bash
--config path/to/config.json
--config path/to/config.yaml
```

Supported formats:
- `.json` - JSON configuration
- `.yaml` or `.yml` - YAML configuration

### Interaction with Other Flags

| Flag | Config Setting | Priority |
|------|----------------|----------|
| `--max-pages` | `scan_settings.max_pages` | CLI > Site > Default |
| `--format` | `scan_settings.format` | CLI > Site > Default |
| `--output` | N/A | CLI only |
| `--example-url` | N/A | CLI only |
| `--site` | N/A | CLI only |

---

## Troubleshooting

### Config File Not Found

```
Error: Config file not found: config.json
```

Solution: Provide full or relative path to existing config file.

### Invalid JSON

```
Error loading config: Invalid JSON in config file
```

Solution: Validate JSON syntax. Use online JSON validator or:
```bash
python -m json.tool config.json
```

### YAML Module Not Found

```
ImportError: YAML support requires PyYAML. Install with: pip install PyYAML
```

Solution: Either install PyYAML or use JSON config files instead.

### Site-Specific Settings Not Applied

Make sure the `--site` URL matches the key in `site_specific` exactly:

```json
{
  "site_specific": {
    "https://www.example.com": { ... }  // Note: with 'www'
  }
}
```

```bash
# This won't match
--site "https://example.com"  // Without 'www'

# This will match
--site "https://www.example.com"  // With 'www'
```

---

## Best Practices

1. **Version Control**: Check config files into git (unless they contain secrets)
2. **Documentation**: Add comments in YAML explaining your settings
3. **Presets**: Create multiple config files for different use cases
4. **Defaults**: Keep conservative defaults in `scan_settings`, override for specific sites
5. **Testing**: Test config files with a small site before full scans

---

## Integration with CI/CD

Use config files in automated workflows:

```bash
#!/bin/bash
# scan.sh

python -m src.analyzer.cli bug-finder scan \
  --config ci-config.json \
  --example-url "$EXAMPLE_URL" \
  --site "$TARGET_SITE"
```

---

## See Also

- `config.example.json` - JSON configuration template
- `config.example.yaml` - YAML configuration template
- [Bug Finder Guide](../guides/BUG_FINDER.md)
- [Main README](../../README.md)
