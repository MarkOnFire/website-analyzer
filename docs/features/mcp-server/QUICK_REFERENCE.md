# MCP Server Quick Reference Card

## Installation (30 seconds)

```bash
# 1. Install MCP SDK
pip install mcp

# 2. Copy config template
cp claude_desktop_config.example.json ~/path/to/config.json

# 3. Edit path in config
# Change: "/path/to/website-analyzer" → your actual path

# 4. Restart Claude Desktop
```

## Tool Summary

| Tool | What It Does | Quick Example |
|------|-------------|---------------|
| `list_projects` | See all projects | "What projects do I have?" |
| `scan_website` | Run analysis | "Scan example-com" |
| `get_scan_status` | Check progress | "Check status of scan abc123" |
| `get_scan_results` | View results | "Show latest results for example-com" |
| `list_patterns` | See patterns | "What patterns are available?" |
| `test_pattern` | Test on URL | "Test xss_vulnerability on my-site.com" |
| `export_results` | Download results | "Export example-com as markdown" |

## Common Commands

### Quick Scan
```
Scan example-com
```

### Background Scan (Large Sites)
```
Scan big-site-com in the background
Check status every 10 seconds
```

### Pattern Discovery
```
Show all security patterns
Test the top one against my-site.com
```

### Results Management
```
Show latest results for example-com
Export as markdown
```

### Complete Audit
```
1. List all critical patterns
2. Test top 5 against my-site.com
3. Run full site scan
4. Export as markdown report
```

## Parameter Reference

### scan_website
```json
{
  "project_slug": "example-com",        // REQUIRED
  "test_names": ["migration_scanner"],  // Optional: specific tests
  "snapshot_timestamp": "2025-12-11T..", // Optional: specific snapshot
  "background": true,                   // Optional: run async
  "timeout_seconds": 600                // Optional: per-test timeout
}
```

### get_scan_results
```json
{
  "project_slug": "example-com",        // REQUIRED
  "results_file": "results_2025...",    // Optional: specific file
  "summary_only": true                  // Optional: summary vs full
}
```

### list_patterns
```json
{
  "severity": "critical",               // Optional: filter by severity
  "tag": "security"                     // Optional: filter by tag
}
```

### test_pattern
```json
{
  "pattern_name": "xss_vulnerability",  // REQUIRED
  "url": "https://example.com",         // REQUIRED (unless content)
  "content": "<html>..."                // REQUIRED (unless url)
}
```

## Response Format

All responses are formatted as readable text/markdown:

```markdown
# Tool Output

**Key Info:** Value
- Bullet point
- Another point

## Section
Details here
```

## Troubleshooting Checklist

- [ ] Python 3.11 installed? `python3.11 --version`
- [ ] MCP SDK installed? `python3.11 -m pip list | grep mcp`
- [ ] Config has absolute path? No relative paths
- [ ] Config JSON valid? Use JSON validator
- [ ] Claude restarted? After config change
- [ ] File permissions? Is repo readable?

## File Locations

**Config File:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Server Code:**
- `src/analyzer/mcp_server.py`

**Documentation:**
- `MCP_SERVER_SETUP.md` - Detailed setup
- `MCP_SERVER_README.md` - Full API reference
- `MCP_USAGE_EXAMPLES.md` - Real-world examples
- `claude_desktop_config.example.json` - Config template

## Key Concepts

### Synchronous Scan
```
You: Scan example-com
Claude: [Waits for scan to complete]
Claude: [Shows results]
```

### Background Scan
```
You: Scan big-site-com in the background
Claude: Returns immediately with scan_id
Claude: [You can ask for status]
You: Check status of scan abc123
Claude: [Shows progress]
```

### Pattern Testing
```
You: Test pattern X on URL
Claude: [Fetches URL or uses provided content]
Claude: [Tests all regex patterns]
Claude: [Shows matches]
```

## Performance Tips

- **Large sites** → Use `background: true`
- **Slow scans** → Increase `timeout_seconds`
- **Fewer results** → Use `test_names` parameter
- **Large results** → Export to JSON for import
- **Monitoring** → Use `get_scan_status` for progress

## Common Issues

### Server won't connect
```
1. cd /path/to/website-analyzer
2. python3.11 -m src.analyzer.mcp_server
3. Check output for errors
```

### Tools don't appear
```
1. Restart Claude Desktop completely
2. Check config has absolute path
3. Verify JSON syntax
```

### Scan times out
```
1. Use: background: true
2. Increase timeout_seconds
3. Use test_names to run fewer tests
```

## Examples

### One-Liner Scan
```
"Scan my-site-com and show me the results"
```

### Pattern Hunting
```
"Show me all critical security patterns and test them against https://my-site.com"
```

### Export Report
```
"Scan example-com with all tests and give me a markdown report"
```

### Progress Monitoring
```
"Start a background scan of big-site-com, check progress every 30 seconds, and summarize results"
```

### Comparison
```
"Compare scan results from Dec 10 vs today for example-com. Did security improve?"
```

## Accessing Documentation

From Claude Desktop:

```
"Show me the MCP server documentation"
"How do I set up the MCP server?"
"What are the available tools?"
"Show me examples of using the analyzer"
```

## Testing Server Directly

```bash
# Start server (will hang - that's normal)
python3.11 -m src.analyzer.mcp_server

# In another terminal, test with curl
curl -X POST http://localhost:3000/tools/list_projects

# Or use mcp-cli if installed
mcp-cli list-tools
```

## Glossary

- **Project Slug**: Short ID for project (e.g., "example-com")
- **Snapshot**: Point-in-time crawl of all site pages
- **Pattern**: Regex-based rule to detect issues
- **Test/Plugin**: Analysis rule that runs on snapshots
- **Scan ID**: UUID for background scans
- **Timestamp**: ISO 8601 format (2025-12-11T15:30:45Z)

## Support

- Full setup guide: `MCP_SERVER_SETUP.md`
- API reference: `MCP_SERVER_README.md`
- Usage examples: `MCP_USAGE_EXAMPLES.md`
- GitHub issues: Project repository

## Version Info

- MCP SDK: `pip show mcp`
- Python: 3.11+
- Requires: `pydantic`, `crawl4ai`, `typer`, `rich`

## Quick Config Template

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/absolute/path/to/website-analyzer"
    }
  }
}
```

Replace `/absolute/path/to/website-analyzer` with your actual path!

---

**Last Updated:** 2025-12-11
**Status:** Production Ready
**Support:** See MCP_SERVER_SETUP.md for detailed help
