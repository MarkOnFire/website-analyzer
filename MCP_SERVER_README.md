# Website-Analyzer MCP Server

Enable Claude Desktop to run website analysis scans, manage patterns, and organize results through the Model Context Protocol (MCP).

## Quick Start

### Installation

1. **Install MCP SDK:**
   ```bash
   pip install mcp
   ```

2. **Copy the example config:**
   ```bash
   cp claude_desktop_config.example.json /path/to/your/claude_desktop_config.json
   ```

3. **Edit the config** to use the absolute path to your website-analyzer repository

4. **Restart Claude Desktop**

See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md) for detailed setup instructions.

## Tools at a Glance

| Tool | Purpose | Key Parameters |
|------|---------|-----------------|
| `list_projects` | Show available projects | `base_dir` |
| `scan_website` | Run analysis on a project | `project_slug`, `background`, `timeout_seconds` |
| `get_scan_status` | Check background scan progress | `scan_id` |
| `get_scan_results` | View scan results | `project_slug`, `summary_only` |
| `list_patterns` | Show available patterns | `severity`, `tag` |
| `test_pattern` | Test pattern on content/URL | `pattern_name`, `content` or `url` |
| `export_results` | Export in multiple formats | `project_slug`, `format` |

## Architecture

### MCP Server Implementation

The server (`src/analyzer/mcp_server.py`) is built on the MCP SDK and provides:

- **Async Tool Handlers**: All tools are async, supporting long-running operations
- **Background Scanning**: Launch scans and check progress independently
- **Pattern Management**: Full pattern library access through Claude
- **Error Handling**: Graceful error reporting with detailed context
- **Stdio Transport**: Works with Claude Desktop's MCP protocol

### Key Classes

```python
class WebsiteAnalyzerMCPServer:
    """MCP Server implementation for website-analyzer."""

    def __init__(self, base_dir: Optional[Path] = None)
        # Initialize with project workspace

    # Tool handlers (async)
    async def list_projects(request: Request) -> List[TextContent]
    async def scan_website(request: Request) -> List[TextContent]
    async def get_scan_status(request: Request) -> List[TextContent]
    async def get_scan_results(request: Request) -> List[TextContent]
    async def list_patterns(request: Request) -> List[TextContent]
    async def test_pattern(request: Request) -> List[TextContent]
    async def export_results(request: Request) -> List[TextContent]
```

## Real-World Usage Examples

### Example 1: Quick Site Analysis

**User Request:**
```
I need to analyze example-com for any issues. What projects do I have available?
```

**What Happens:**
1. Claude calls `list_projects` (no parameters)
2. Server returns all projects with metadata
3. Claude shows you the projects
4. You ask to scan `example-com`
5. Claude calls `scan_website` with `project_slug="example-com"`
6. Results are displayed

**Claude Response:**
```
I found 3 projects in your workspace:
- example-com (created 2025-12-10, 5 snapshots)
- staging-site-com (created 2025-12-08, 2 snapshots)
- docs-example-com (created 2025-12-05, 8 snapshots)

I'll scan example-com with all available tests...

[Results showing pass/fail for each test]
```

### Example 2: Background Scan with Monitoring

**User Request:**
```
Scan my large site (big-site-com) in the background since it has thousands of pages.
Check the status every 10 seconds and let me know when it's done.
```

**What Happens:**
1. Claude calls `scan_website` with `background=true`
2. Server returns immediately with a `scan_id`
3. Claude repeatedly calls `get_scan_status` with that `scan_id`
4. Eventually the scan completes
5. Claude calls `get_scan_results` to show the final summary

**Server Output:**
```
Scan ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Starting background scan of big-site-com with all tests...

[Status checks every ~10 seconds]
Status: running (25% complete)
Status: running (62% complete)
Status: completed!

Results summary:
- migration_scanner: PASS (0 jQuery .live() found)
- xss_check: PASS (no XSS patterns detected)
- performance: WARNING (3 slow pages detected)
[More results...]
```

### Example 3: Pattern Discovery and Testing

**User Request:**
```
Show me all security-related patterns, then test the top one against my homepage.
```

**What Happens:**
1. Claude calls `list_patterns` with `tag="security"`
2. Server returns matching patterns
3. Claude selects one (e.g., "xss_vulnerability")
4. Claude calls `test_pattern` with the URL
5. Results show if the pattern matches your site

**Claude Response:**
```
Found 4 security patterns:
- xss_vulnerability (critical)
- csrf_token_missing (high)
- sql_injection_risk (critical)
- insecure_headers (medium)

Testing xss_vulnerability against https://example.com/...

Matches found: 0 ✓
Pattern tested successfully - no XSS vulnerabilities detected.
```

### Example 4: Export and Archive

**User Request:**
```
Scan example-com and give me the results as a markdown report I can save.
```

**What Happens:**
1. Claude calls `scan_website` with `project_slug="example-com"`
2. Waits for results
3. Claude calls `export_results` with `format="markdown"`
4. Server returns markdown-formatted results
5. Claude displays in a nice format or provides download

**Export Output:**
````markdown
# Website Analysis Report: example-com

**Scan Date:** 2025-12-11T15:30:45Z
**Total Tests:** 7
**Passed:** 5 | **Warnings:** 1 | **Failed:** 1

## Test Results

### migration_scanner
**Status:** PASS
**Summary:** No deprecated jQuery patterns found
- Checked 42 pages
- 0 .live() calls
- 0 deprecated selectors

### xss_check
**Status:** PASS
**Summary:** No XSS vulnerabilities detected
...
````

## Configuration Patterns

### Single Instance (Default)

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/website-analyzer"
    }
  }
}
```

### Multiple Instances

```json
{
  "mcpServers": {
    "analyzer-prod": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/prod-analyzer"
    },
    "analyzer-staging": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/staging-analyzer"
    }
  }
}
```

### With Custom Environment

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/website-analyzer",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "ANALYZER_PATTERNS_DIR": "/custom/patterns"
      }
    }
  }
}
```

## API Reference

### Request/Response Format

All tools follow this pattern:

```python
async def tool_name(request: Request) -> List[TextContent]:
    """
    Tool description.

    Returns:
        List[TextContent] - MCP response containing text/markdown
    """
```

### Tool Details

#### `list_projects`
Lists all projects in the workspace.

**Input:**
```json
{
  "base_dir": "/path/to/workspace"  // optional
}
```

**Output:**
```markdown
# Available Projects

**example-com**
- URL: https://example.com
- Created: 2025-12-10T12:00:00Z
- Snapshots: 5
- Latest Results: results_2025-12-11T...json

**staging-site-com**
- URL: https://staging.site.com
- Created: 2025-12-08T10:00:00Z
- Snapshots: 2
```

#### `scan_website`
Runs analysis on a project.

**Input:**
```json
{
  "project_slug": "example-com",           // required
  "test_names": ["migration_scanner"],     // optional
  "snapshot_timestamp": "2025-12-11T...",  // optional
  "background": false,                     // optional, default: false
  "timeout_seconds": 300                   // optional, default: 300
}
```

**Output (Synchronous):**
```markdown
# Scan Results

**Total Tests:** 2

## migration_scanner
**Status:** pass
**Summary:** No deprecated jQuery patterns found
**Details:** {...}

## xss_check
**Status:** pass
**Summary:** No XSS issues detected
```

**Output (Background):**
```markdown
Scan started in background
Scan ID: 550e8400-e29b-41d4-a716-446655440000

Use 'get_scan_status' with this ID to check progress.
```

#### `get_scan_status`
Checks progress of a background scan.

**Input:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000"  // required
}
```

**Output:**
```markdown
# Scan Status: running

**Project:** example-com
**Progress:** 67%
```

Or when complete:
```markdown
# Scan Status: completed

**Project:** example-com
**Progress:** 100%

## Results (5 tests)

- **migration_scanner**: pass
- **xss_check**: pass
- **performance**: warning
- **headers**: pass
- **accessibility**: pass
```

#### `get_scan_results`
Reads saved scan results.

**Input:**
```json
{
  "project_slug": "example-com",        // required
  "results_file": "results_2025-12-11...",  // optional
  "summary_only": true                  // optional, default: true
}
```

**Output (Summary):**
```markdown
# Results: results_2025-12-11T...json

## migration_scanner
**Status:** pass
**Summary:** No deprecated jQuery patterns found

## xss_check
**Status:** pass
**Summary:** No XSS vulnerabilities detected
```

#### `list_patterns`
Lists available analysis patterns.

**Input:**
```json
{
  "severity": "high",    // optional: low|medium|high|critical
  "tag": "security"      // optional: custom tags
}
```

**Output:**
```markdown
# Available Patterns

## xss_vulnerability
**Description:** Detects potential XSS vulnerabilities
**Severity:** critical
**Tags:** security, injection
**Patterns:** 3
**Author:** Security Team

## sql_injection
**Description:** Finds potential SQL injection vectors
**Severity:** critical
**Tags:** security, injection
**Patterns:** 5
```

#### `test_pattern`
Tests a pattern against content or URL.

**Input (Content):**
```json
{
  "pattern_name": "jquery_live_deprecated",
  "content": "<html>...$('.foo').live('click', ...)...</html>"
}
```

**Input (URL):**
```json
{
  "pattern_name": "jquery_live_deprecated",
  "url": "https://example.com/page"
}
```

**Output:**
```markdown
# Pattern Test Results: jquery_live_deprecated

**Pattern:** Detects deprecated jQuery .live() method
**Matches Found:** 2

## Matches by Pattern

- **\$\(.*\)\.live\(**: 2 matches
  1. $('.element').live('click', function() {...
  2. $('.modal').live('mouseenter', function() {...
```

#### `export_results`
Exports results in different formats.

**Input:**
```json
{
  "project_slug": "example-com",           // required
  "format": "markdown",                    // required: json|html|csv|markdown
  "results_file": "results_2025-12-11...", // optional
  "output_path": "/tmp/report.md"          // optional
}
```

**Output:**
```markdown
# Export Results: MARKDOWN

**Format:** markdown
**Source:** results_2025-12-11T...json
**Records:** 5

[Full markdown report...]
```

## Performance Considerations

### Large Sites
For sites with 1000+ pages:
- Use `background: true` for scans
- Increase `timeout_seconds` to 600+
- Run specific tests with `test_names` instead of all

### Pattern Testing
- Cache results in conversation context
- Avoid re-testing same pattern multiple times
- Batch multiple patterns into single test

### Memory Usage
- Server stores scan metadata in memory
- Long-running sessions with many background scans may accumulate memory
- Restart server periodically for cleanup

## Troubleshooting

### Server Won't Start

**Check Python version:**
```bash
python3.11 --version
```

**Verify MCP SDK:**
```bash
python3.11 -m pip install mcp
```

**Test directly:**
```bash
cd /path/to/website-analyzer
python3.11 -m src.analyzer.mcp_server
```

### Tools Not Working

1. Restart Claude Desktop completely (quit, then reopen)
2. Check config file for JSON syntax errors
3. Verify absolute paths in config
4. Check file permissions on repository

### Scan Failures

- Use `list_projects` to verify project exists
- Check project has snapshots with `get_snapshots_dir()`
- Increase timeout if tests are timing out
- Run individual tests with `test_names` parameter

## Development

### Testing the Server Locally

```bash
# Run server in debug mode
python3.11 -m src.analyzer.mcp_server

# In another terminal, test a tool
curl http://localhost:3000/tools/list_projects
```

### Adding New Tools

1. Define the tool schema in `_setup_tools()`
2. Implement async handler method
3. Return `List[TextContent]` responses
4. Update documentation

### Extension Points

- **Custom patterns**: Add JSON files to `patterns/` directory
- **New tests**: Implement as plugins in `src/analyzer/plugins/`
- **Export formats**: Extend `export_results` handler

## Contributing

Improvements welcome! Submit issues or PRs to the website-analyzer repository.

## Support

For detailed setup and troubleshooting, see [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md).
