#!/usr/bin/env python3.11
"""
MCP Server for website-analyzer tool.

Provides Model Context Protocol (MCP) integration for website analysis,
allowing Claude Desktop to run scans, manage projects, and analyze patterns.

Tools available:
- list_projects: Show available project directories
- scan_website: Run analysis scan on a website project
- get_scan_status: Check background scan progress
- get_scan_results: Read and summarize results from JSON
- list_patterns: Show available bug patterns
- test_pattern: Test a pattern against content/URL
- export_results: Export scan results to different formats
"""

import asyncio
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import subprocess
import uuid

try:
    from mcp.server import Server, Request
    from mcp.types import Tool, TextContent, Resource
except ImportError:
    raise ImportError(
        "MCP SDK not installed. Install with: pip install mcp"
    )

from src.analyzer.workspace import Workspace, slugify_url
from src.analyzer.runner import TestRunner
from src.analyzer.pattern_library import PatternLibrary
from src.analyzer.test_plugin import TestResult


class WebsiteAnalyzerMCPServer:
    """MCP Server implementation for website-analyzer."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the MCP server.

        Args:
            base_dir: Base directory containing projects/ folder.
                     Defaults to current directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.runner = TestRunner(self.base_dir)
        self.pattern_lib = PatternLibrary()

        # Background scan tracking: scan_id -> {status, progress, results_path}
        self.scans: Dict[str, Dict[str, Any]] = {}

        # Initialize MCP server
        self.server = Server("website-analyzer")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register all MCP tools."""
        self.server.add_tool(
            Tool(
                name="list_projects",
                description="List all available website analysis projects",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_dir": {
                            "type": "string",
                            "description": "Base directory to search (optional, defaults to workspace root)"
                        }
                    }
                }
            ),
            self.list_projects
        )

        self.server.add_tool(
            Tool(
                name="scan_website",
                description="Run analysis scan on a website project. Can run synchronously or in background.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_slug": {
                            "type": "string",
                            "description": "Project slug (e.g., 'example-com')"
                        },
                        "test_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of specific tests to run. If omitted, runs all tests."
                        },
                        "snapshot_timestamp": {
                            "type": "string",
                            "description": "Optional specific snapshot timestamp (ISO 8601). If omitted, uses latest."
                        },
                        "background": {
                            "type": "boolean",
                            "description": "If true, run in background and return scan_id. If false, wait for results.",
                            "default": False
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "description": "Maximum execution time per plugin in seconds",
                            "default": 300
                        }
                    },
                    "required": ["project_slug"]
                }
            ),
            self.scan_website
        )

        self.server.add_tool(
            Tool(
                name="get_scan_status",
                description="Check the status and progress of a background scan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "Scan ID returned by scan_website (background=true)"
                        }
                    },
                    "required": ["scan_id"]
                }
            ),
            self.get_scan_status
        )

        self.server.add_tool(
            Tool(
                name="get_scan_results",
                description="Read and summarize test results from a completed scan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_slug": {
                            "type": "string",
                            "description": "Project slug"
                        },
                        "results_file": {
                            "type": "string",
                            "description": "Optional specific results file (default: latest)"
                        },
                        "summary_only": {
                            "type": "boolean",
                            "description": "If true, return only summary. If false, include details.",
                            "default": True
                        }
                    },
                    "required": ["project_slug"]
                }
            ),
            self.get_scan_results
        )

        self.server.add_tool(
            Tool(
                name="list_patterns",
                description="List all available bug analysis patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "description": "Filter by severity (low, medium, high, critical)",
                            "enum": ["low", "medium", "high", "critical"]
                        },
                        "tag": {
                            "type": "string",
                            "description": "Filter by tag (e.g., 'security', 'performance')"
                        }
                    }
                }
            ),
            self.list_patterns
        )

        self.server.add_tool(
            Tool(
                name="test_pattern",
                description="Test a pattern against content or a URL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern_name": {
                            "type": "string",
                            "description": "Name of pattern to test (from list_patterns)"
                        },
                        "content": {
                            "type": "string",
                            "description": "HTML/text content to test against (alternative to url)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch and test against (alternative to content)"
                        }
                    },
                    "required": ["pattern_name"]
                }
            ),
            self.test_pattern
        )

        self.server.add_tool(
            Tool(
                name="export_results",
                description="Export scan results to different formats (JSON, HTML, CSV, Markdown)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_slug": {
                            "type": "string",
                            "description": "Project slug"
                        },
                        "format": {
                            "type": "string",
                            "description": "Export format",
                            "enum": ["json", "html", "csv", "markdown"]
                        },
                        "results_file": {
                            "type": "string",
                            "description": "Optional specific results file (default: latest)"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional output path. If omitted, returns as string/data."
                        }
                    },
                    "required": ["project_slug", "format"]
                }
            ),
            self.export_results
        )

    async def list_projects(self, request: Request) -> List[TextContent]:
        """List all available projects."""
        try:
            base_dir = Path(request.params.get("base_dir", self.base_dir))
            projects_dir = base_dir / "projects"

            if not projects_dir.exists():
                return [TextContent(
                    type="text",
                    text=f"No projects directory found at {projects_dir}"
                )]

            projects = []
            for project_path in sorted(projects_dir.iterdir()):
                if not project_path.is_dir():
                    continue

                try:
                    workspace = Workspace.load(project_path.name, base_dir)

                    # Get latest snapshot info
                    snapshots_dir = workspace.get_snapshots_dir()
                    snapshot_count = len(list(snapshots_dir.glob("*"))) if snapshots_dir.exists() else 0

                    # Get latest results
                    results_dir = workspace.get_test_results_dir()
                    latest_result = None
                    if results_dir.exists():
                        results = sorted(results_dir.glob("results_*.json"), reverse=True)
                        if results:
                            latest_result = results[0].name

                    projects.append({
                        "slug": workspace.metadata.slug,
                        "url": workspace.metadata.url,
                        "created": workspace.metadata.created_at,
                        "last_crawl": workspace.metadata.last_crawl,
                        "snapshots": snapshot_count,
                        "latest_result": latest_result
                    })
                except Exception as e:
                    continue

            if not projects:
                return [TextContent(
                    type="text",
                    text="No valid projects found"
                )]

            output = "# Available Projects\n\n"
            for proj in projects:
                output += f"**{proj['slug']}**\n"
                output += f"- URL: {proj['url']}\n"
                output += f"- Created: {proj['created']}\n"
                output += f"- Snapshots: {proj['snapshots']}\n"
                if proj['latest_result']:
                    output += f"- Latest Results: {proj['latest_result']}\n"
                output += "\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing projects: {str(e)}\n\n{traceback.format_exc()}"
            )]

    async def scan_website(self, request: Request) -> List[TextContent]:
        """Run analysis scan on a project."""
        try:
            project_slug = request.params.get("project_slug")
            test_names = request.params.get("test_names")
            snapshot_timestamp = request.params.get("snapshot_timestamp")
            background = request.params.get("background", False)
            timeout_seconds = request.params.get("timeout_seconds", 300)

            if not project_slug:
                return [TextContent(
                    type="text",
                    text="Error: project_slug is required"
                )]

            if background:
                # Launch background scan
                scan_id = str(uuid.uuid4())
                self.scans[scan_id] = {
                    "status": "pending",
                    "project_slug": project_slug,
                    "test_names": test_names,
                    "snapshot_timestamp": snapshot_timestamp,
                    "timeout_seconds": timeout_seconds,
                    "progress": 0,
                    "results": None
                }

                # Schedule background task
                asyncio.create_task(self._run_background_scan(scan_id))

                return [TextContent(
                    type="text",
                    text=f"Scan started in background\nScan ID: {scan_id}\n\nUse 'get_scan_status' with this ID to check progress."
                )]
            else:
                # Run synchronously
                results = await self.runner.run(
                    slug=project_slug,
                    test_names=test_names,
                    snapshot_timestamp=snapshot_timestamp,
                    save=True,
                    timeout_seconds=timeout_seconds
                )

                output = self._format_results(results)
                return [TextContent(type="text", text=output)]

        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error running scan: {str(e)}\n\n{traceback.format_exc()}"
            )]

    async def _run_background_scan(self, scan_id: str) -> None:
        """Execute scan in background."""
        scan_info = self.scans[scan_id]
        try:
            scan_info["status"] = "running"

            results = await self.runner.run(
                slug=scan_info["project_slug"],
                test_names=scan_info["test_names"],
                snapshot_timestamp=scan_info["snapshot_timestamp"],
                save=True,
                timeout_seconds=scan_info["timeout_seconds"]
            )

            scan_info["status"] = "completed"
            scan_info["progress"] = 100
            scan_info["results"] = [r.model_dump() for r in results]

        except Exception as e:
            scan_info["status"] = "error"
            scan_info["error"] = str(e)

    async def get_scan_status(self, request: Request) -> List[TextContent]:
        """Check background scan status."""
        try:
            scan_id = request.params.get("scan_id")

            if not scan_id:
                return [TextContent(
                    type="text",
                    text="Error: scan_id is required"
                )]

            if scan_id not in self.scans:
                return [TextContent(
                    type="text",
                    text=f"Error: Scan {scan_id} not found"
                )]

            scan_info = self.scans[scan_id]

            output = f"# Scan Status: {scan_info['status']}\n\n"
            output += f"**Project:** {scan_info['project_slug']}\n"
            output += f"**Progress:** {scan_info['progress']}%\n"

            if scan_info['status'] == "error":
                output += f"**Error:** {scan_info.get('error', 'Unknown error')}\n"

            if scan_info['results']:
                output += f"\n## Results ({len(scan_info['results'])} tests)\n\n"
                for result in scan_info['results']:
                    output += f"- **{result['plugin_name']}**: {result['status']}\n"
                    output += f"  {result['summary']}\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error checking scan status: {str(e)}"
            )]

    async def get_scan_results(self, request: Request) -> List[TextContent]:
        """Read and summarize test results."""
        try:
            project_slug = request.params.get("project_slug")
            results_file = request.params.get("results_file")
            summary_only = request.params.get("summary_only", True)

            if not project_slug:
                return [TextContent(
                    type="text",
                    text="Error: project_slug is required"
                )]

            workspace = Workspace.load(project_slug, self.base_dir)
            results_dir = workspace.get_test_results_dir()

            if not results_dir.exists():
                return [TextContent(
                    type="text",
                    text=f"No results found for project {project_slug}"
                )]

            # Find results file
            if results_file:
                results_path = results_dir / results_file
            else:
                # Get latest
                results_files = sorted(results_dir.glob("results_*.json"), reverse=True)
                if not results_files:
                    return [TextContent(
                        type="text",
                        text=f"No results found for project {project_slug}"
                    )]
                results_path = results_files[0]

            if not results_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Results file not found: {results_file}"
                )]

            results_data = json.loads(results_path.read_text())

            if summary_only:
                output = f"# Results: {results_path.name}\n\n"
                for result in results_data:
                    output += f"## {result['plugin_name']}\n"
                    output += f"**Status:** {result['status']}\n"
                    output += f"**Summary:** {result['summary']}\n\n"
            else:
                output = "# Full Results\n\n"
                output += "```json\n"
                output += json.dumps(results_data, indent=2)
                output += "\n```\n"

            return [TextContent(type="text", text=output)]

        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error reading results: {str(e)}\n\n{traceback.format_exc()}"
            )]

    async def list_patterns(self, request: Request) -> List[TextContent]:
        """List available bug patterns."""
        try:
            severity_filter = request.params.get("severity")
            tag_filter = request.params.get("tag")

            patterns_data = self.pattern_lib.list_patterns()

            # Filter
            filtered = patterns_data
            if severity_filter:
                filtered = [p for p in filtered if p.get("severity") == severity_filter]
            if tag_filter:
                filtered = [p for p in filtered if tag_filter in (p.get("tags") or [])]

            if not filtered:
                return [TextContent(
                    type="text",
                    text="No patterns found matching criteria"
                )]

            output = "# Available Patterns\n\n"
            for pattern in filtered:
                if "error" in pattern:
                    output += f"**{pattern['filename']}**: Error loading pattern\n"
                    continue

                output += f"## {pattern['name']}\n"
                output += f"**Description:** {pattern['description']}\n"
                output += f"**Severity:** {pattern['severity']}\n"
                if pattern.get('tags'):
                    output += f"**Tags:** {', '.join(pattern['tags'])}\n"
                output += f"**Patterns:** {pattern['patterns_count']}\n"
                if pattern.get('author'):
                    output += f"**Author:** {pattern['author']}\n"
                output += "\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing patterns: {str(e)}"
            )]

    async def test_pattern(self, request: Request) -> List[TextContent]:
        """Test a pattern against content or URL."""
        try:
            pattern_name = request.params.get("pattern_name")
            content = request.params.get("content")
            url = request.params.get("url")

            if not pattern_name:
                return [TextContent(
                    type="text",
                    text="Error: pattern_name is required"
                )]

            if not content and not url:
                return [TextContent(
                    type="text",
                    text="Error: either content or url is required"
                )]

            # Get pattern by name
            pattern = self.pattern_lib.load_pattern_by_name(pattern_name)
            if not pattern:
                return [TextContent(
                    type="text",
                    text=f"Pattern not found: {pattern_name}"
                )]

            # Test pattern
            if url:
                test_result = self.pattern_lib.test_pattern_on_url(pattern, url)
            else:
                test_result = self.pattern_lib.test_pattern_on_content(pattern, content)

            output = f"# Pattern Test Results: {pattern_name}\n\n"
            output += f"**Pattern:** {pattern.description}\n"

            if "error" in test_result:
                output += f"**Error:** {test_result['error']}\n"
            else:
                output += f"**Total Matches:** {test_result['total_matches']}\n"
                if test_result['total_matches'] > 0:
                    output += "\n## Matches by Pattern\n\n"
                    for regex, match_info in test_result['matches_by_pattern'].items():
                        if 'error' in match_info:
                            output += f"- **{regex}**: Error - {match_info['error']}\n"
                        else:
                            output += f"- **{regex}**: {match_info['count']} matches\n"
                            if match_info['matches']:
                                for i, match in enumerate(match_info['matches'][:3], 1):
                                    preview = str(match)[:100].replace('\n', ' ')
                                    output += f"  {i}. {preview}\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error testing pattern: {str(e)}\n\n{traceback.format_exc()}"
            )]

    async def export_results(self, request: Request) -> List[TextContent]:
        """Export results to different formats."""
        try:
            project_slug = request.params.get("project_slug")
            export_format = request.params.get("format")
            results_file = request.params.get("results_file")
            output_path = request.params.get("output_path")

            if not project_slug or not export_format:
                return [TextContent(
                    type="text",
                    text="Error: project_slug and format are required"
                )]

            workspace = Workspace.load(project_slug, self.base_dir)
            results_dir = workspace.get_test_results_dir()

            # Find results file
            if results_file:
                results_path = results_dir / results_file
            else:
                results_files = sorted(results_dir.glob("results_*.json"), reverse=True)
                if not results_files:
                    return [TextContent(
                        type="text",
                        text=f"No results found for project {project_slug}"
                    )]
                results_path = results_files[0]

            if not results_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Results file not found"
                )]

            results_data = json.loads(results_path.read_text())

            # For now, return JSON representation
            # In a real implementation, would call actual export functions
            output = f"# Export Results: {export_format.upper()}\n\n"
            output += f"**Format:** {export_format}\n"
            output += f"**Source:** {results_path.name}\n"
            output += f"**Records:** {len(results_data)}\n\n"

            if export_format == "json":
                output += "```json\n"
                output += json.dumps(results_data, indent=2)
                output += "\n```\n"
            else:
                output += f"Export to {export_format} format not yet implemented in MCP.\n"
                output += "Results are available in JSON format above.\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error exporting results: {str(e)}"
            )]

    def _format_results(self, results: List[TestResult]) -> str:
        """Format test results for display."""
        if not results:
            return "No results to display"

        output = "# Scan Results\n\n"
        output += f"**Total Tests:** {len(results)}\n\n"

        for result in results:
            output += f"## {result.plugin_name}\n"
            output += f"**Status:** {result.status}\n"
            output += f"**Summary:** {result.summary}\n"

            if result.details:
                output += f"**Details:** "
                output += json.dumps(result.details, indent=2)
                output += "\n"

            output += "\n"

        return output

    async def run(self) -> None:
        """Run the MCP server (stdio transport)."""
        async with self.server:
            pass


def main():
    """Entry point for the MCP server."""
    import sys

    # Initialize with current working directory
    server = WebsiteAnalyzerMCPServer(base_dir=Path.cwd())

    # Run server
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
