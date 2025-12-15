# Website-Analyzer MCP Server Setup Guide

This guide explains how to set up and use the Model Context Protocol (MCP) server for the website-analyzer tool with Claude Desktop.

## Overview

The website-analyzer MCP server provides Claude with direct access to:
- Website scanning and analysis capabilities
- Pattern management and testing
- Project organization and results management
- Multiple export formats for analysis results

## Requirements

- Claude Desktop (latest version)
- Python 3.11+
- Website-analyzer repository installed
- MCP SDK: `pip install mcp`

## Installation Steps

### 1. Install MCP SDK

First, ensure the MCP SDK is installed in your website-analyzer environment:

```bash
cd /path/to/website-analyzer
source .venv/bin/activate  # or appropriate venv activation
pip install mcp
```

### 2. Update Claude Desktop Configuration

The MCP server configuration is stored in Claude Desktop's settings. The location depends on your operating system:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 3. Add MCP Server Configuration

Add the website-analyzer MCP server to your `claude_desktop_config.json`. Here's a template:

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": [
        "-m",
        "src.analyzer.mcp_server"
      ],
      "cwd": "/path/to/website-analyzer"
    }
  }
}
```

**Important:** Replace `/path/to/website-analyzer` with the actual path to your repository.

### 4. Restart Claude Desktop

After updating the configuration, restart Claude Desktop completely:
- Close all Claude windows
- Quit Claude Desktop from the menu or dock
- Reopen Claude Desktop

You should see a notification that the MCP server has connected.

## Configuration Details

### Alternative: NPX-based Setup (if using Node.js wrapper)

If you prefer to wrap the Python server in Node.js, you can use npx:

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "npx",
      "args": [
        "-y",
        "node-based-wrapper"
      ]
    }
  }
}
```

### Environment Variables (Optional)

You can configure the MCP server behavior via environment variables:

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/website-analyzer",
      "env": {
        "ANALYZER_BASE_DIR": "/path/to/website-analyzer",
        "ANALYZER_PATTERNS_DIR": "/path/to/patterns",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Available Tools

Once connected, Claude can use these tools:

### `list_projects`
Lists all available website analysis projects in the workspace.

**Parameters:**
- `base_dir` (optional): Base directory to search

**Example:**
```
List all my analysis projects
```

### `scan_website`
Runs an analysis scan on a website project.

**Parameters:**
- `project_slug` (required): Project identifier (e.g., 'example-com')
- `test_names` (optional): Specific tests to run
- `snapshot_timestamp` (optional): Use specific snapshot (ISO 8601)
- `background` (optional): Run in background (default: false)
- `timeout_seconds` (optional): Timeout per plugin (default: 300)

**Example:**
```
Scan the example-com project with all tests
```

```
Run just the migration_scanner test on my-site-com in the background
```

### `get_scan_status`
Check the progress of a background scan.

**Parameters:**
- `scan_id` (required): Returned from background scan

**Example:**
```
Check status of scan abc-def-123
```

### `get_scan_results`
Read and summarize scan results.

**Parameters:**
- `project_slug` (required): Project identifier
- `results_file` (optional): Specific results file
- `summary_only` (optional): Return summary only (default: true)

**Example:**
```
Show me the latest scan results for example-com
```

### `list_patterns`
List available bug analysis patterns.

**Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `tag` (optional): Filter by tag

**Example:**
```
Show me all high severity patterns
```

```
List patterns tagged with 'security'
```

### `test_pattern`
Test a pattern against content or a URL.

**Parameters:**
- `pattern_name` (required): Pattern to test
- `content` (optional): HTML/text to analyze
- `url` (optional): URL to fetch and analyze

**Example:**
```
Test the jquery_live_deprecated pattern against https://example.com
```

```
Does the xss_vulnerability pattern match this code: <img src=x onerror=alert('xss')>
```

### `export_results`
Export scan results to various formats.

**Parameters:**
- `project_slug` (required): Project identifier
- `format` (required): json, html, csv, or markdown
- `results_file` (optional): Specific results file
- `output_path` (optional): Save to file

**Example:**
```
Export the latest results for my-site-com as markdown
```

```
Give me the scan results as JSON for archival
```

## Usage Examples

### Example 1: Quick Scan and Summary

```
I want to analyze my-site-com. First list the available projects, then scan it with all tests.
```

Claude will:
1. Call `list_projects` to show available projects
2. Call `scan_website` with your project
3. Display the results

### Example 2: Background Scan with Status Checking

```
Start a background scan of my-site-com and check on it in a minute.
```

Claude will:
1. Call `scan_website` with `background: true`
2. Get a scan_id
3. Periodically call `get_scan_status` to monitor progress
4. Show you the results when complete

### Example 3: Testing Patterns

```
What patterns are available? Show me the high severity ones, then test the top one against my homepage.
```

Claude will:
1. Call `list_patterns` filtered by severity
2. Call `test_pattern` against your URL
3. Show matches and details

### Example 4: Results Export

```
Scan example-com and export the results as a markdown report.
```

Claude will:
1. Call `scan_website`
2. Call `export_results` with format=markdown
3. Display or save the formatted report

## Troubleshooting

### MCP Server Not Connecting

**Problem:** Claude Desktop shows "Failed to start MCP server"

**Solutions:**
1. Check Python 3.11 is installed: `python3.11 --version`
2. Verify MCP SDK: `python3.11 -m pip list | grep mcp`
3. Ensure the path in config is correct and uses absolute paths
4. Check file permissions on the repository

**Debug Steps:**
```bash
# Test the server directly
cd /path/to/website-analyzer
python3.11 -m src.analyzer.mcp_server
```

### Tools Not Appearing

**Problem:** Connected but tools don't show in Claude

**Solutions:**
1. Restart Claude Desktop completely (close and reopen)
2. Check configuration has correct JSON syntax
3. Verify Python version matches in config

### Scan Failures

**Problem:** Scans error out or timeout

**Solutions:**
1. Increase `timeout_seconds` in scan configuration
2. Run specific tests instead of all: `test_names: ["migration_scanner"]`
3. Use `background: true` for large sites
4. Check if the project has snapshots: `list_projects` first

### Pattern Testing Errors

**Problem:** Pattern tests fail or show "not found"

**Solutions:**
1. Use `list_patterns` to see exact pattern names
2. Ensure content/URL is accessible
3. Check pattern regex is valid using `test_pattern` tool

## Performance Tips

1. **Use Background Scans**: For large sites or multiple tests, use `background: true` and check status periodically

2. **Filter Tests**: Specify only needed tests with `test_names` to reduce scan time

3. **Pattern Testing**: Cache pattern test results in conversation context rather than retesting repeatedly

4. **Results Export**: Use `summary_only: true` for faster results loading

## Security Considerations

1. **File Paths**: MCP server operates relative to the configured `cwd`. All paths are sandboxed to the project directory.

2. **No External Network Access**: The MCP server only accesses URLs explicitly provided via tool calls.

3. **Credentials**: Keep any API keys or credentials in `.env` files, never in MCP configuration.

4. **Results Privacy**: Scan results are stored locally. Export them securely.

## Advanced Configuration

### Multiple Analyzer Instances

You can configure multiple analyzer instances for different repositories:

```json
{
  "mcpServers": {
    "website-analyzer-prod": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/prod-analyzer"
    },
    "website-analyzer-staging": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/staging-analyzer"
    }
  }
}
```

Claude can then use tools with the `@` syntax to target specific instances.

### Custom Patterns Directory

Point to a custom patterns location:

```json
{
  "mcpServers": {
    "website-analyzer": {
      "command": "python3.11",
      "args": ["-m", "src.analyzer.mcp_server"],
      "cwd": "/path/to/website-analyzer",
      "env": {
        "ANALYZER_PATTERNS_DIR": "/path/to/custom/patterns"
      }
    }
  }
}
```

## Monitoring and Logging

The MCP server logs to stdout/stderr. To capture logs:

**macOS/Linux:**
```bash
tail -f ~/.config/Claude/logs/mcp-website-analyzer.log
```

**Claude Desktop Console:**
- Open Developer Tools (Cmd+Alt+I on macOS)
- Check the Console tab for MCP messages

## Updates and Maintenance

### Updating the MCP Server

After pulling new changes to website-analyzer:

```bash
cd /path/to/website-analyzer
git pull
pip install -r requirements.txt --upgrade
```

Then restart Claude Desktop.

### Checking Server Version

You can ask Claude to check server capabilities:

```
What tools are available from the website-analyzer MCP server?
```

Claude will call `list_projects` and other tools to verify the server is working.

## Support and Troubleshooting

For issues:

1. Check this documentation first
2. Review the server logs in Claude's developer tools
3. Test the MCP server independently: `python3.11 -m src.analyzer.mcp_server`
4. Check GitHub issues in the website-analyzer repository

## Next Steps

Once configured, try:

1. **List Projects**: Ask Claude to show your projects
2. **Run a Scan**: Scan one project with all tests
3. **Check Results**: View the scan summary
4. **Export Data**: Export results in your preferred format

Example conversation starter:
```
List all my analysis projects and give me a summary of what we have.
```

Enjoy using website-analyzer with Claude Desktop!
