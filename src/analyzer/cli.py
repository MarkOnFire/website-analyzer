import asyncio
import json
import re
import typer
import os
import time
import signal
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import platform
import subprocess
import sys
from datetime import datetime, timedelta

from src.analyzer.workspace import Workspace, ProjectMetadata, slugify_url, SnapshotManager
from src.analyzer.crawler import BasicCrawler
from src.analyzer.runner import TestRunner
from src.analyzer.test_plugin import TestResult # For type hinting, not directly used here
from src.analyzer.config import ConfigLoader, ConfigMerger, create_example_config
from src.analyzer.llm_crawler_sim import (
    LLMCrawlerSimulator,
    KNOWN_LLM_CRAWLERS,
    CRAWLER_CATEGORIES,
    simulate_llm_crawlers,
    generate_robots_txt_rules,
    generate_robots_txt_block_all,
    generate_robots_txt_block_training,
    analyze_robots_txt_for_llm,
)
from bug_finder_export import export_results, export_to_html, export_to_json, export_to_csv
from bug_finder_export_markdown import export_to_markdown, export_to_slack_snippet


console = Console()


# Utility Functions for Enhanced UX
class ScanManager:
    """Manage scan history and metadata."""

    SCAN_REGISTRY = Path.home() / ".bug-finder" / "scans.json"

    @classmethod
    def _ensure_registry(cls):
        """Ensure scan registry file exists."""
        cls.SCAN_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        if not cls.SCAN_REGISTRY.exists():
            cls.SCAN_REGISTRY.write_text(json.dumps({"scans": []}, indent=2))

    @classmethod
    def record_scan(cls, scan_id: str, site_url: str, example_url: str, max_pages: int,
                    status: str = "running", output_file: Optional[str] = None):
        """Record a new scan in registry."""
        cls._ensure_registry()
        data = json.loads(cls.SCAN_REGISTRY.read_text())

        scan = {
            "id": scan_id,
            "site_url": site_url,
            "example_url": example_url,
            "max_pages": max_pages,
            "status": status,
            "output_file": output_file,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }

        data["scans"].append(scan)
        cls.SCAN_REGISTRY.write_text(json.dumps(data, indent=2))

        return scan_id

    @classmethod
    def update_scan(cls, scan_id: str, status: str, output_file: Optional[str] = None):
        """Update scan status."""
        cls._ensure_registry()
        data = json.loads(cls.SCAN_REGISTRY.read_text())

        for scan in data["scans"]:
            if scan["id"] == scan_id:
                scan["status"] = status
                if status == "completed":
                    scan["completed_at"] = datetime.now().isoformat()
                if output_file:
                    scan["output_file"] = output_file
                break

        cls.SCAN_REGISTRY.write_text(json.dumps(data, indent=2))

    @classmethod
    def list_scans(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent scans."""
        cls._ensure_registry()
        data = json.loads(cls.SCAN_REGISTRY.read_text())
        # Return most recent first
        return sorted(data["scans"], key=lambda x: x["started_at"], reverse=True)[:limit]

    @classmethod
    def get_scan(cls, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan details by ID."""
        cls._ensure_registry()
        data = json.loads(cls.SCAN_REGISTRY.read_text())

        for scan in data["scans"]:
            if scan["id"] == scan_id:
                return scan
        return None

    @classmethod
    def generate_scan_id(cls) -> str:
        """Generate unique scan ID."""
        import time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = f"scan_{timestamp}_{int(time.time() * 1000) % 10000:04d}"
        return unique_id


class EnvironmentChecker:
    """Check environment setup and dependencies."""

    @staticmethod
    def check_python_version() -> Dict[str, Any]:
        """Check Python version (needs 3.11+)."""
        version = sys.version_info
        is_valid = version.major > 3 or (version.major == 3 and version.minor >= 11)

        return {
            "name": "Python Version",
            "version": f"{version.major}.{version.minor}.{version.micro}",
            "required": "3.11+",
            "status": "ok" if is_valid else "error",
            "message": "Correct version" if is_valid else "Python 3.11 or higher required",
        }

    @staticmethod
    def check_dependency(module_name: str, import_name: str = None) -> Dict[str, Any]:
        """Check if a dependency is installed."""
        import_as = import_name or module_name

        try:
            __import__(import_as)
            # Try to get version
            version = None
            try:
                version = __import__(import_as).__version__
            except AttributeError:
                pass

            return {
                "name": module_name,
                "status": "ok",
                "version": version or "installed",
            }
        except ImportError:
            return {
                "name": module_name,
                "status": "missing",
                "message": f"Install with: pip install {module_name}",
            }

    @staticmethod
    def check_playwright() -> Dict[str, Any]:
        """Check Playwright/Chromium installation."""
        try:
            __import__("playwright")
            # Check if chromium is installed
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps", "--help"],
                capture_output=True,
                timeout=5,
            )
            return {
                "name": "Playwright",
                "status": "ok",
                "message": "Chromium available",
            }
        except Exception as e:
            return {
                "name": "Playwright",
                "status": "missing",
                "message": "Install with: pip install playwright && python -m playwright install chromium",
            }

    @classmethod
    def run_all_checks(cls) -> List[Dict[str, Any]]:
        """Run all environment checks."""
        checks = [
            cls.check_python_version(),
            cls.check_dependency("crawl4ai"),
            cls.check_dependency("typer"),
            cls.check_dependency("rich"),
            cls.check_dependency("beautifulsoup4", "bs4"),
            cls.check_dependency("requests"),
            cls.check_playwright(),
        ]

        return checks


class SuggestiveErrorHandler:
    """Provide helpful suggestions for common errors."""

    SUGGESTIONS = {
        "url": {
            "pattern": "Could not (fetch|parse|connect)",
            "suggestion": "The URL might be inaccessible. Try:\n"
                         "  - Check the URL is correct and public\n"
                         "  - Use web.archive.org for historical pages\n"
                         "  - Try --dry-run to preview without fetching",
        },
        "url_timeout": {
            "pattern": "timeout|timed out",
            "suggestion": "The page took too long to load. Try:\n"
                         "  - Reduce --max-pages to test with fewer pages\n"
                         "  - Use --dry-run to check if settings are valid\n"
                         "  - Check your internet connection",
        },
        "memory": {
            "pattern": "MemoryError|out of memory",
            "suggestion": "Running out of memory. Try:\n"
                         "  - Reduce --max-pages to scan fewer pages\n"
                         "  - Close other applications\n"
                         "  - Use --incremental for long scans",
        },
        "regex": {
            "pattern": "regex|pattern|invalid expression",
            "suggestion": "Pattern error in your bug text. Try:\n"
                         "  - Check for special regex characters (. * + ? [ ])\n"
                         "  - Use simpler text patterns\n"
                         "  - Test with: bug-finder patterns test",
        },
    }

    @staticmethod
    def suggest_for_error(error_msg: str) -> Optional[str]:
        """Generate suggestion for error message."""
        import re as regex_module

        for key, info in SuggestiveErrorHandler.SUGGESTIONS.items():
            if regex_module.search(info["pattern"], error_msg, regex_module.IGNORECASE):
                return info["suggestion"]
        return None

app = typer.Typer(
    name="website-analyzer",
    help="A comprehensive tool for analyzing website health and performance."
)

project_app = typer.Typer(
    name="project",
    help="Manage website projects."
)
app.add_typer(project_app)

crawl_app = typer.Typer(
    name="crawl",
    help="Crawl websites and create snapshots."
)
app.add_typer(crawl_app)

test_app = typer.Typer(
    name="test",
    help="Run tests on website snapshots."
)
app.add_typer(test_app)

bug_finder_app = typer.Typer(
    name="bug-finder",
    help="Find visual bugs across websites by example."
)
app.add_typer(bug_finder_app)

schedule_app = typer.Typer(
    name="schedule",
    help="Manage recurring scans with cron-style scheduling."
)
app.add_typer(schedule_app)

daemon_app = typer.Typer(
    name="daemon",
    help="Control the scheduler daemon (start/stop/status)."
)
app.add_typer(daemon_app)

notify_app = typer.Typer(
    name="notify",
    help="Configure and test notification system."
)
app.add_typer(notify_app)


@project_app.command("new")
def project_new(
    url: str = typer.Argument(..., help="The URL of the website to create a project for."),
    base_dir: Path = typer.Option(
        Path("."),
        help="Base directory where the 'projects' folder will be created.",
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    )
):
    """
    Create a new project for a given website URL.
    """
    try:
        workspace = Workspace.create(url, base_dir)
        console.print(f"[green]Project '{workspace.metadata.slug}' created for {url} at {workspace.project_dir}[/green]")
    except ValueError as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        raise typer.Exit(code=1)


@project_app.command("list")
def project_list(
    base_dir: Path = typer.Option(
        Path("."),
        help="Base directory containing the 'projects' folder.",
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    )
):
    """
    List all existing projects.
    """
    projects_dir = base_dir / "projects"
    if not projects_dir.is_dir():
        console.print(f"[yellow]No 'projects' directory found at {projects_dir}[/yellow]")
        raise typer.Exit(code=1)

    console.print("[bold green]Existing projects:[/bold green]")
    found_projects = False
    for project_path in projects_dir.iterdir():
        if project_path.is_dir():
            try:
                workspace = Workspace.load(project_path.name, base_dir)
                console.print(f"  - [cyan]{workspace.metadata.slug}[/cyan] ([link]{workspace.metadata.url}[/link])")
                found_projects = True
            except ValueError:
                console.print(f"  - [red]{project_path.name} (Malformed project)[/red]")
                found_projects = True
    if not found_projects:
        console.print("  [yellow]No projects found.[/yellow]")


@project_app.command("snapshots")
def project_snapshots(
    slug: str = typer.Argument(..., help="The slug of the project."),
    base_dir: Path = typer.Option(
        Path("."),
        help="Base directory containing the 'projects' folder.",
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    )
):
    """
    List all snapshots for a given project.
    """
    try:
        workspace = Workspace.load(slug, base_dir)
        snap_manager = SnapshotManager(workspace.get_snapshots_dir())
        snapshots = snap_manager.list_snapshots()

        if not snapshots:
            console.print(f"[yellow]No snapshots found for project '[cyan]{slug}[/cyan]'.[/yellow]")
            return
        
        console.print(f"[bold green]Snapshots for project '[cyan]{slug}[/cyan]':[/bold green]")
        for snap_path in snapshots:
            console.print(f"  - [magenta]{snap_path.name}[/magenta]")

    except ValueError as e:
        console.print(f"[red]Error accessing project: {e}[/red]")
        raise typer.Exit(code=1)


@crawl_app.command("start")
def crawl_start(
    slug: str = typer.Argument(..., help="The slug of the project to crawl."),
    url: Optional[str] = typer.Option(
        None,
        help="Override the project's URL for this crawl. If not provided, uses the URL from project metadata."
    ),
    max_pages: int = typer.Option(
        BasicCrawler.DEFAULT_MAX_PAGES, help="Maximum number of pages to crawl."
    ),
    max_depth: Optional[int] = typer.Option(
        BasicCrawler.DEFAULT_MAX_DEPTH, help="Maximum crawl depth (0 for current page only, None for unlimited)."
    ),
    stealth: bool = typer.Option(
        False,
        "--stealth",
        help="Enable stealth mode to bypass bot detection (e.g., Cloudflare). Use when sites block headless browsers."
    ),
    header: Optional[List[str]] = typer.Option(
        None,
        "--header", "-H",
        help="Custom HTTP header in 'Name:Value' format. Can be repeated. Example: -H 'X-Crawler-Token:secret'"
    ),
    base_dir: Path = typer.Option(
        Path("."),
        help="Base directory containing the 'projects' folder.",
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
):
    """
    Start crawling a website for a given project.
    """
    # Parse headers from "Name:Value" format to dict
    headers_dict: dict[str, str] = {}
    if header:
        for h in header:
            if ":" in h:
                key, value = h.split(":", 1)
                headers_dict[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Warning: Invalid header format '{h}' - expected 'Name:Value'. Skipping.[/yellow]")

    # Define the async function separately
    async def _run_crawl_async():
        workspace = Workspace.load(slug, base_dir)
        target_url = url if url else workspace.metadata.url
        if not target_url:
            console.print(f"[red]Error: Project '[cyan]{slug}[/cyan]' has no URL specified and none provided.[/red]")
            raise typer.Exit(code=1)

        console.print(f"[bold green]Starting crawl for project '[cyan]{slug}[/cyan]' ([link]{target_url}[/link])...")
        if stealth:
            console.print("[yellow]Stealth mode enabled - bypassing bot detection[/yellow]")
        if headers_dict:
            console.print(f"[yellow]Custom headers: {', '.join(headers_dict.keys())}[/yellow]")

        # Initialize crawler with CLI-provided max_pages and max_depth
        crawler = BasicCrawler(max_pages=max_pages, max_depth=max_depth, stealth=stealth, headers=headers_dict)
        snap_manager = SnapshotManager(workspace.get_snapshots_dir())
        snapshot_dir = snap_manager.create_snapshot_dir()

        # Queue for URLs to visit
        queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        queue.put_nowait((target_url, 0)) # (url, depth)
        
        seen_urls: Set[str] = set()
        crawled_count = 0
        
        # Use Rich Progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Set total to max_pages from CLI or None for indeterminate
            crawl_task = progress.add_task("[green]Crawling...", total=max_pages if max_pages > 0 else None)

            while not queue.empty() and (max_pages == 0 or crawled_count < max_pages):
                current_url, current_depth = await queue.get()

                # Normalize and check if already seen
                normalized_url = BasicCrawler.normalize_url(current_url)
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url) # Mark as seen when added to queue

                # Check max_depth
                if max_depth is not None and current_depth > max_depth:
                    continue

                progress.update(crawl_task, description=f"[green]Fetching: {current_url}[/green]")
                
                results = await crawler.crawl_urls(
                    urls=[current_url],
                    # No direct progress_callback here because crawl_urls only takes a single URL per task.
                    # The overall progress is managed by the loop and queue.
                )
                
                if not results:
                    progress.console.print(f"[yellow]Warning: Failed to crawl {current_url}. Skipping.[/yellow]")
                    continue # Skip if crawl failed

                result = results[0]
                crawled_count += 1
                progress.update(crawl_task, advance=1, description=f"[green]Crawled: {current_url}[/green]")

                # Save result
                # Pass crawler's configured max_pages/max_depth for internal link filtering in save_snapshot
                crawler.save_snapshot(
                    result,
                    snapshot_dir,
                    current_depth=current_depth,
                    include_subdomains=crawler.include_subdomains,
                    allowed_subdomains=crawler.allowed_subdomains,
                    blocked_subdomains=crawler.blocked_subdomains,
                    include_patterns=crawler.include_patterns,
                    exclude_patterns=crawler.exclude_patterns,
                )
                
                # Discover new links
                links_from_page = BasicCrawler.filter_internal_links(
                    base_url=current_url,
                    links=result.links or [],
                    # Use crawler's configured max_pages/max_depth for filtering links on this page
                    max_pages=crawler.max_pages,
                    current_depth=current_depth + 1,
                    max_depth=crawler.max_depth,
                    include_subdomains=crawler.include_subdomains,
                    allowed_subdomains=crawler.allowed_subdomains,
                    blocked_subdomains=crawler.blocked_subdomains,
                    include_patterns=crawler.include_patterns,
                    exclude_patterns=crawler.exclude_patterns,
                )

                for link in links_from_page:
                    norm_link = BasicCrawler.normalize_url(link)
                    # Add to queue only if not already seen globally and within page/depth limits
                    if norm_link not in seen_urls and (max_pages == 0 or crawled_count < max_pages):
                        queue.put_nowait((link, current_depth + 1))
            
            progress.update(crawl_task, description="[bold green]Crawl complete![/bold green]", completed=crawled_count)


        console.print(f"[bold green]Crawl complete.[/bold green] Snapshot created at [magenta]{snapshot_dir.name}[/magenta]")
        # Update workspace metadata
        workspace.metadata = ProjectMetadata(
            url=workspace.metadata.url,
            slug=workspace.metadata.slug,
            created_at=workspace.metadata.created_at,
            last_crawl=snapshot_dir.name # Store timestamp of snapshot
        )
        workspace.save_metadata()
    
    # Call the async function from the sync typer command
    try:
        asyncio.run(_run_crawl_async())
    except ValueError as e:
        console.print(f"[red]Error during crawl: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]An unexpected error occurred during crawl: {e}[/red]")
        # TODO: Log full traceback (Feature 125)
        raise typer.Exit(code=1)


@test_app.command("run")
def test_run(
    slug: str = typer.Argument(..., help="The slug of the project to run tests on."),
    test_names: Optional[List[str]] = typer.Option(
        None, "--test", "-t", help="Specific test plugin names to run. Can be repeated."
    ),
    snapshot_timestamp: Optional[str] = typer.Option(
        None, "--snapshot", "-s", help="Specific snapshot timestamp to use. Defaults to latest."
    ),
    save_results: bool = typer.Option(
        True, "--save/--no-save", help="Whether to save test results to disk."
    ),
    timeout: int = typer.Option(
        TestRunner.DEFAULT_TIMEOUT_SECONDS, # Define a default in TestRunner for clarity
        help="Maximum execution time per plugin in seconds."
    ),
    base_dir: Path = typer.Option(
        Path("."),
        help="Base directory containing the 'projects' folder.",
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    config: Optional[List[str]] = typer.Option(
        None, "--config", "-c", 
        help="JSON string for plugin configuration, e.g., 'migration-scanner:{\"pattern\":\".*\"}'. Can be repeated."
    ),
):
    """
    Run tests on a project's website snapshot.
    """
    processed_config: Dict[str, Any] = {}
    if config:
        for item in config:
            try:
                plugin_name, json_str = item.split(":", 1)
                processed_config[plugin_name] = json.loads(json_str)
            except ValueError:
                console.print(f"[red]Invalid config format: '{item}'. Expected 'plugin_name:{{json_string}}'.[/red]")
                raise typer.Exit(code=1)
            except json.JSONDecodeError:
                console.print(f"[red]Invalid JSON in config for '{item}'.[/red]")
                raise typer.Exit(code=1)

    try:
        runner = TestRunner(base_dir)
        
        async def _run_tests_async():
            results = await runner.run(
                slug=slug,
                test_names=test_names,
                snapshot_timestamp=snapshot_timestamp,
                save=save_results,
                config=processed_config,
                timeout_seconds=timeout,
            )
            if results:
                console.print("\n[bold green]--- Test Results Summary ---[/bold green]")
                for r in results:
                    status_color = "green" if r.status == "pass" else "red" if r.status == "error" or r.status == "fail" else "yellow"
                    console.print(f"  - [cyan]{r.plugin_name}[/cyan]: [{status_color}]{r.status.upper()}[/{status_color}] - {r.summary}")
            else:
                console.print("[yellow]No tests were run or no results were generated.[/yellow]")
                
        asyncio.run(_run_tests_async())

    except ValueError as e:
        console.print(f"[red]Error running tests: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]An unexpected error occurred during test run: {e}[/red]")
        # TODO: Log full traceback (Feature 125)
        raise typer.Exit(code=1)


@test_app.command("llm-access")
def test_llm_access(
    url: str = typer.Argument(..., help="URL to test LLM crawler access for."),
    crawlers: Optional[List[str]] = typer.Option(
        None, "--crawler", "-c",
        help="Specific crawler(s) to test. Can be repeated. Default: all known crawlers."
    ),
    crawl: bool = typer.Option(
        False, "--crawl",
        help="Crawl the site first to discover and test multiple pages."
    ),
    max_pages: int = typer.Option(
        10, "--max-pages", "-n",
        help="Maximum number of pages to test when using --crawl."
    ),
    show_content: bool = typer.Option(
        False, "--show-content",
        help="Show content preview for each crawler response."
    ),
    json_output: bool = typer.Option(
        False, "--json",
        help="Output results as JSON."
    ),
):
    """
    Test how LLM training crawlers see your website.

    Simulates access from major LLM crawlers (GPTBot, ClaudeBot, CCBot, etc.)
    using their real User-Agent strings to show what content they would see
    during training data collection.

    Unlike headless browsers, this uses simple HTTP requests - exactly how
    real LLM crawlers operate.

    Examples:
        python -m src.analyzer.cli test llm-access https://example.com
        python -m src.analyzer.cli test llm-access https://example.com --crawl -n 20
        python -m src.analyzer.cli test llm-access https://example.com -c GPTBot -c ClaudeBot
        python -m src.analyzer.cli test llm-access https://example.com --json
    """
    async def _run_simulation():
        console.print(f"\n[bold]Testing LLM Crawler Access for:[/bold] [link]{url}[/link]\n")

        # Show which crawlers we're testing
        simulator = LLMCrawlerSimulator()
        if crawlers:
            crawler_set = set(c.lower() for c in crawlers)
            simulator.crawlers = [
                c for c in KNOWN_LLM_CRAWLERS
                if c.name.lower() in crawler_set
            ]
            if not simulator.crawlers:
                console.print(f"[red]No matching crawlers found. Available: {', '.join(c.name for c in KNOWN_LLM_CRAWLERS)}[/red]")
                raise typer.Exit(code=1)

        # Multi-page crawl mode
        if crawl:
            await _run_multi_page_simulation(simulator, url, max_pages, json_output)
            return

        console.print(f"[dim]Testing {len(simulator.crawlers)} crawler(s): {', '.join(c.name for c in simulator.crawlers)}[/dim]\n")

        with console.status("[bold green]Simulating LLM crawler access..."):
            result = await simulator.simulate(url)

        if json_output:
            # JSON output mode
            output = {
                "url": result.url,
                "timestamp": result.timestamp,
                "summary": result.summary,
                "robots_txt_blocks": result.robots_txt_blocks,
                "responses": [
                    {
                        "crawler": r.crawler.name,
                        "organization": r.crawler.organization,
                        "status_code": r.status_code,
                        "is_blocked": r.is_blocked,
                        "block_reason": r.block_reason,
                        "has_meaningful_content": r.has_meaningful_content,
                        "content_length": r.content_length,
                        "title": r.title,
                        "response_time_ms": round(r.response_time_ms, 1),
                        "redirect_url": r.redirect_url,
                        "error": r.error,
                    }
                    for r in result.responses
                ],
            }
            # Add content analysis if available
            if result.content_analysis:
                ca = result.content_analysis
                output["content_analysis"] = {
                    "llm_readiness_score": ca.llm_readiness_score,
                    "title": ca.title,
                    "title_length": ca.title_length,
                    "meta_description": ca.meta_description,
                    "meta_description_length": ca.meta_description_length,
                    "has_og_tags": ca.has_og_tags,
                    "has_twitter_cards": ca.has_twitter_cards,
                    "has_schema_markup": ca.has_schema_markup,
                    "h1_count": ca.h1_count,
                    "h2_count": ca.h2_count,
                    "h3_count": ca.h3_count,
                    "has_good_heading_hierarchy": ca.has_good_heading_hierarchy,
                    "semantic_tags_used": list(ca.semantic_tags_used),
                    "uses_semantic_html": ca.uses_semantic_html,
                    "word_count": ca.word_count,
                    "has_substantial_content": ca.has_substantial_content,
                    "internal_link_count": ca.internal_link_count,
                    "external_link_count": ca.external_link_count,
                    "issues": ca.issues,
                    "recommendations": ca.recommendations,
                }
            console.print(json.dumps(output, indent=2))
            return

        # Pretty output mode
        # Summary panel
        summary = result.summary
        exposure_color = "green" if summary["training_exposure"] == "high" else "yellow" if summary["training_exposure"] == "medium" else "red"

        summary_text = f"""[bold]Accessibility Score:[/bold] {summary['accessibility_score']}%
[bold]Training Data Exposure:[/bold] [{exposure_color}]{summary['training_exposure'].upper()}[/{exposure_color}]
[bold]Crawlers Blocked:[/bold] {summary['crawlers_blocked']}/{summary['total_crawlers_tested']}
[bold]Crawlers with Content:[/bold] {summary['crawlers_with_meaningful_content']}/{summary['total_crawlers_tested']}
[bold]robots.txt Blocks:[/bold] {summary['robots_txt_blocks']}"""

        console.print(Panel(summary_text, title="Summary", border_style="blue"))

        # Results table
        table = Table(title="Crawler Access Results", show_header=True, header_style="bold magenta")
        table.add_column("Crawler", style="cyan")
        table.add_column("Org", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Blocked?", justify="center")
        table.add_column("Content", justify="center")
        table.add_column("robots.txt", justify="center")
        table.add_column("Time (ms)", justify="right")

        for r in result.responses:
            status_style = "green" if r.status_code == 200 else "red" if r.status_code >= 400 else "yellow"
            blocked_style = "red" if r.is_blocked else "green"
            content_style = "green" if r.has_meaningful_content else "red"
            robots_blocked = result.robots_txt_blocks.get(r.crawler.name, False)
            robots_style = "red" if robots_blocked else "green"

            table.add_row(
                r.crawler.name,
                r.crawler.organization,
                f"[{status_style}]{r.status_code}[/{status_style}]",
                f"[{blocked_style}]{'Yes: ' + (r.block_reason or 'unknown') if r.is_blocked else 'No'}[/{blocked_style}]",
                f"[{content_style}]{'Yes' if r.has_meaningful_content else 'No'}[/{content_style}]",
                f"[{robots_style}]{'Blocked' if robots_blocked else 'Allowed'}[/{robots_style}]",
                f"{r.response_time_ms:.0f}",
            )

        console.print(table)

        # Show block reasons if any
        if summary["block_reasons"]:
            console.print("\n[bold yellow]Block Reasons:[/bold yellow]")
            for reason, affected_crawlers in summary["block_reasons"].items():
                console.print(f"  • {reason}: {', '.join(affected_crawlers)}")

        # Show content preview if requested
        if show_content:
            console.print("\n[bold]Content Previews:[/bold]")
            for r in result.responses:
                if r.content_preview and not r.is_blocked:
                    console.print(f"\n[cyan]{r.crawler.name}[/cyan] - Title: {r.title or 'None'}")
                    console.print(Panel(r.content_preview[:300] + "...", border_style="dim"))

        # Content Quality Analysis
        if result.content_analysis:
            ca = result.content_analysis
            score_color = "green" if ca.llm_readiness_score >= 7 else "yellow" if ca.llm_readiness_score >= 5 else "red"

            quality_text = f"""[bold]LLM Readiness Score:[/bold] [{score_color}]{ca.llm_readiness_score:.1f}/10[/{score_color}]

[bold]Content Metrics:[/bold]
  • Title: {ca.title[:50] + '...' if ca.title and len(ca.title) > 50 else ca.title or '[missing]'} ({ca.title_length} chars)
  • Meta Description: {'Yes' if ca.meta_description else '[red]Missing[/red]'} ({ca.meta_description_length} chars)
  • Schema Markup: {'[green]Yes[/green]' if ca.has_schema_markup else '[yellow]No[/yellow]'}
  • Open Graph: {'[green]Yes[/green]' if ca.has_og_tags else '[dim]No[/dim]'}

[bold]Content Structure:[/bold]
  • Word Count: {ca.word_count} {'[green](substantial)[/green]' if ca.has_substantial_content else '[yellow](light)[/yellow]'}
  • Headings: H1={ca.h1_count}, H2={ca.h2_count}, H3={ca.h3_count} {'[green](good hierarchy)[/green]' if ca.has_good_heading_hierarchy else '[yellow](needs work)[/yellow]'}
  • Semantic HTML: {', '.join(ca.semantic_tags_used) if ca.semantic_tags_used else '[yellow]None[/yellow]'}
  • Internal Links: {ca.internal_link_count}"""

            console.print(Panel(quality_text, title="Content Quality for LLM Training", border_style="cyan"))

            # Content issues
            if ca.issues:
                console.print("\n[bold yellow]Content Issues Found:[/bold yellow]")
                for issue in ca.issues[:8]:  # Show first 8
                    console.print(f"  • {issue}")
                if len(ca.issues) > 8:
                    console.print(f"  [dim]... and {len(ca.issues) - 8} more[/dim]")

            # Content recommendations
            if ca.recommendations:
                console.print("\n[bold green]Content Recommendations:[/bold green]")
                for rec in ca.recommendations[:5]:  # Show first 5
                    console.print(f"  • {rec}")
                if len(ca.recommendations) > 5:
                    console.print(f"  [dim]... and {len(ca.recommendations) - 5} more[/dim]")

        # Access Recommendations
        console.print("\n[bold]Access Recommendations:[/bold]")
        if summary["crawlers_blocked"] > 0:
            console.print("  • [yellow]Some crawlers are being blocked. Review your bot protection settings.[/yellow]")
        if summary["robots_txt_blocks"] > 0:
            console.print("  • [yellow]robots.txt is blocking some LLM crawlers. This is intentional if you want to opt out of training.[/yellow]")
        if summary["training_exposure"] == "high":
            console.print("  • [green]Your content is accessible to most LLM training crawlers.[/green]")
        elif summary["training_exposure"] == "low":
            console.print("  • [red]Most LLM crawlers cannot access your content. Check if this is intentional.[/red]")

    async def _run_multi_page_simulation(simulator, start_url: str, max_pages: int, json_out: bool):
        """Crawl site and test multiple pages for LLM accessibility."""
        import aiohttp
        from urllib.parse import urljoin, urlparse

        console.print(f"[bold]Multi-page LLM Access Test[/bold]")
        console.print(f"[dim]Discovering up to {max_pages} pages from {start_url}...[/dim]\n")

        # Discover pages by following links
        discovered_urls: Set[str] = set()
        to_visit = [start_url]
        base_domain = urlparse(start_url).netloc

        async with aiohttp.ClientSession() as session:
            with console.status("[bold green]Discovering pages...") as status:
                while to_visit and len(discovered_urls) < max_pages:
                    current_url = to_visit.pop(0)
                    if current_url in discovered_urls:
                        continue

                    try:
                        async with session.get(current_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                                discovered_urls.add(current_url)
                                status.update(f"[bold green]Discovered {len(discovered_urls)} pages...")

                                # Extract links if we need more pages
                                if len(discovered_urls) < max_pages:
                                    html = await response.text()
                                    # Simple link extraction
                                    import re
                                    links = re.findall(r'href=["\']([^"\']+)["\']', html)
                                    for link in links:
                                        if link.startswith('#') or link.startswith('javascript:'):
                                            continue
                                        absolute = urljoin(current_url, link)
                                        if urlparse(absolute).netloc == base_domain and absolute not in discovered_urls:
                                            to_visit.append(absolute)
                    except Exception:
                        continue

        if not discovered_urls:
            console.print("[red]No pages discovered. Check the URL and try again.[/red]")
            return

        console.print(f"[green]Discovered {len(discovered_urls)} pages to test[/green]\n")

        # Test each page
        all_results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Testing pages...", total=len(discovered_urls))

            for page_url in discovered_urls:
                progress.update(task, description=f"Testing {page_url[:50]}...")
                result = await simulator.simulate(page_url)
                all_results.append(result)
                progress.advance(task)

        if json_out:
            # JSON output for all pages
            output = {
                "base_url": start_url,
                "pages_tested": len(all_results),
                "pages": [
                    {
                        "url": r.url,
                        "accessibility_score": r.summary.get("accessibility_score", 0),
                        "llm_readiness_score": r.content_analysis.llm_readiness_score if r.content_analysis else None,
                        "training_exposure": r.summary.get("training_exposure", "unknown"),
                        "crawlers_blocked": r.summary.get("crawlers_blocked", 0),
                        "content_analysis": {
                            "title": r.content_analysis.title if r.content_analysis else None,
                            "word_count": r.content_analysis.word_count if r.content_analysis else 0,
                            "issues": r.content_analysis.issues if r.content_analysis else [],
                        } if r.content_analysis else None,
                    }
                    for r in all_results
                ]
            }
            console.print(json.dumps(output, indent=2))
            return

        # Summary table
        table = Table(title=f"LLM Access Results - {len(all_results)} Pages", show_header=True, header_style="bold magenta")
        table.add_column("URL", style="cyan", max_width=50)
        table.add_column("Access", justify="center")
        table.add_column("LLM Score", justify="center")
        table.add_column("Words", justify="right")
        table.add_column("Issues", justify="right")

        total_accessibility = 0
        total_readiness = 0
        pages_with_analysis = 0

        for r in all_results:
            access_score = r.summary.get("accessibility_score", 0)
            total_accessibility += access_score
            access_color = "green" if access_score >= 80 else "yellow" if access_score >= 50 else "red"

            if r.content_analysis:
                pages_with_analysis += 1
                llm_score = r.content_analysis.llm_readiness_score
                total_readiness += llm_score
                score_color = "green" if llm_score >= 7 else "yellow" if llm_score >= 5 else "red"
                word_count = r.content_analysis.word_count
                issues_count = len(r.content_analysis.issues)
            else:
                llm_score = None
                score_color = "dim"
                word_count = 0
                issues_count = 0

            # Truncate URL for display
            display_url = r.url
            if len(display_url) > 50:
                display_url = display_url[:47] + "..."

            table.add_row(
                display_url,
                f"[{access_color}]{access_score:.0f}%[/{access_color}]",
                f"[{score_color}]{llm_score:.1f}[/{score_color}]" if llm_score else "[dim]N/A[/dim]",
                str(word_count),
                str(issues_count),
            )

        console.print(table)

        # Overall summary
        avg_accessibility = total_accessibility / len(all_results) if all_results else 0
        avg_readiness = total_readiness / pages_with_analysis if pages_with_analysis else 0

        console.print(f"\n[bold]Site-wide Averages:[/bold]")
        console.print(f"  • Average Accessibility: {avg_accessibility:.1f}%")
        console.print(f"  • Average LLM Readiness: {avg_readiness:.1f}/10")
        console.print(f"  • Pages Tested: {len(all_results)}")

        # Find worst pages
        if all_results:
            worst_by_readiness = sorted(
                [r for r in all_results if r.content_analysis],
                key=lambda r: r.content_analysis.llm_readiness_score
            )[:3]
            if worst_by_readiness:
                console.print(f"\n[bold yellow]Pages Needing Improvement:[/bold yellow]")
                for r in worst_by_readiness:
                    console.print(f"  • {r.url[:60]} - Score: {r.content_analysis.llm_readiness_score:.1f}/10")
                    if r.content_analysis.issues:
                        console.print(f"    Issues: {', '.join(r.content_analysis.issues[:3])}")

    try:
        asyncio.run(_run_simulation())
    except Exception as e:
        console.print(f"[red]Error during LLM crawler simulation: {e}[/red]")
        raise typer.Exit(code=1)


@test_app.command("llm-crawlers")
def test_llm_crawlers_list():
    """
    List all known LLM crawlers that can be simulated.
    """
    table = Table(title="Known LLM Crawlers", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Organization", style="green")
    table.add_column("robots.txt Token")
    table.add_column("Description")

    for crawler in KNOWN_LLM_CRAWLERS:
        table.add_row(
            crawler.name,
            crawler.organization,
            crawler.robots_txt_token,
            crawler.description,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(KNOWN_LLM_CRAWLERS)} crawlers[/dim]")


@test_app.command("llm-robots")
def test_llm_robots(
    url: Optional[str] = typer.Argument(
        None,
        help="URL to analyze current robots.txt (optional). If not provided, generates rules only."
    ),
    block: str = typer.Option(
        "training",
        "--block", "-b",
        help="What to block: 'training' (default), 'all', 'inference', or comma-separated crawler names."
    ),
    allow_paths: Optional[str] = typer.Option(
        None,
        "--allow-paths",
        help="Comma-separated paths to allow even for blocked crawlers (e.g., '/public,/api/docs')."
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Write output to file instead of stdout."
    ),
    analyze_only: bool = typer.Option(
        False,
        "--analyze-only",
        help="Only analyze current robots.txt without generating new rules."
    ),
):
    """
    Generate or analyze robots.txt rules for LLM crawler management.

    This command helps you control which LLM crawlers can access your content
    for training purposes.

    Categories:
      - training: Crawlers used for LLM training (GPTBot, ClaudeBot, CCBot, etc.)
      - inference: Crawlers used for search/browsing (ChatGPT-User, PerplexityBot)
      - all: All known LLM crawlers

    Examples:
        # Generate rules to block training crawlers (recommended default)
        python -m src.analyzer.cli test llm-robots

        # Block all LLM crawlers
        python -m src.analyzer.cli test llm-robots --block all

        # Block specific crawlers only
        python -m src.analyzer.cli test llm-robots --block "GPTBot,ClaudeBot"

        # Analyze current robots.txt for a site
        python -m src.analyzer.cli test llm-robots https://example.com --analyze-only

        # Generate and save to file
        python -m src.analyzer.cli test llm-robots -o robots-llm.txt
    """
    async def _analyze_url(site_url: str):
        """Fetch and analyze robots.txt from a URL."""
        simulator = LLMCrawlerSimulator()
        robots_content = await simulator.fetch_robots_txt(site_url)
        return analyze_robots_txt_for_llm(robots_content)

    # Analyze existing robots.txt if URL provided
    if url:
        console.print(f"\n[bold]Analyzing robots.txt for:[/bold] [link]{url}[/link]\n")

        analysis = asyncio.run(_analyze_url(url))

        # Show analysis results
        status_color = "green" if analysis.total_blocked > 0 else "yellow"
        console.print(Panel(
            f"""[bold]robots.txt found:[/bold] {'Yes' if analysis.has_robots_txt else 'No'}
[bold]Training crawlers blocked:[/bold] [{status_color}]{analysis.training_crawlers_blocked}/{len(CRAWLER_CATEGORIES['training'])}[/{status_color}]
[bold]Inference crawlers blocked:[/bold] {analysis.inference_crawlers_blocked}/{len(CRAWLER_CATEGORIES['inference'])}
[bold]Total LLM crawlers blocked:[/bold] {analysis.total_blocked}/{len(KNOWN_LLM_CRAWLERS)}""",
            title="Current Status",
            border_style="blue"
        ))

        # Show per-crawler status
        table = Table(title="Crawler Block Status", show_header=True, header_style="bold magenta")
        table.add_column("Crawler", style="cyan")
        table.add_column("Category")
        table.add_column("Status", justify="center")

        for crawler in KNOWN_LLM_CRAWLERS:
            is_blocked = analysis.blocks_by_crawler.get(crawler.robots_txt_token, False)
            category = "training" if crawler.robots_txt_token in CRAWLER_CATEGORIES["training"] else "inference"
            status = "[red]Blocked[/red]" if is_blocked else "[green]Allowed[/green]"
            table.add_row(crawler.robots_txt_token, category, status)

        console.print(table)

        # Show recommendations
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in analysis.recommendations:
            console.print(f"  • {rec}")

        if analyze_only:
            if analysis.suggested_additions:
                console.print("\n[bold yellow]Suggested additions to robots.txt:[/bold yellow]")
                console.print(Panel(analysis.suggested_additions, border_style="yellow"))
            return

        console.print("\n" + "─" * 60 + "\n")

    # Generate new rules
    console.print("[bold]Generated robots.txt Rules:[/bold]\n")

    # Parse block parameter
    allow_path_list = [p.strip() for p in allow_paths.split(",")] if allow_paths else None

    if block.lower() in ["training", "all", "inference"]:
        rules = generate_robots_txt_rules(
            block_category=block.lower(),
            allow_paths=allow_path_list,
        )
    else:
        # Assume comma-separated crawler names
        crawler_list = [c.strip() for c in block.split(",")]
        rules = generate_robots_txt_rules(
            block_crawlers=crawler_list,
            allow_paths=allow_path_list,
        )

    if output_file:
        output_file.write_text(rules)
        console.print(f"[green]Rules written to: {output_file}[/green]")
    else:
        console.print(Panel(rules, title="robots.txt", border_style="green"))

    console.print("\n[dim]Add these rules to your robots.txt file to control LLM crawler access.[/dim]")
    console.print("[dim]Note: These rules are advisory - well-behaved crawlers respect them, but enforcement requires server-side blocking.[/dim]")


@bug_finder_app.command("scan")
def bug_finder_scan(
    example_url: Optional[str] = typer.Option(
        None, "--example-url", "-e",
        help="URL of a page showing the bug (e.g., archived page)."
    ),
    site_to_scan: Optional[str] = typer.Option(
        None, "--site", "-s",
        help="Base URL of site to scan for similar bugs."
    ),
    max_pages: Optional[int] = typer.Option(
        None, "--max-pages", "-m",
        help="Maximum number of pages to scan. Overrides config file setting."
    ),
    bug_text: Optional[str] = typer.Option(
        None, "--bug-text", "-b",
        help="Provide bug text directly instead of auto-extracting from URL."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path (default: auto-generated based on site URL)."
    ),
    format: Optional[str] = typer.Option(
        None, "--format", "-f",
        help="Output format: txt, csv, html, json, or all. Overrides config file setting."
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c",
        help="Path to configuration file (JSON or YAML) with default scan settings.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    incremental: bool = typer.Option(
        False, "--incremental", "-i",
        help="Enable incremental output. Results written to .partial.json as they're found, useful for long scans."
    ),
    pattern_file: Optional[List[str]] = typer.Option(
        None, "--pattern-file",
        help="Load custom pattern(s) from pattern library. Can specify multiple times."
    ),
    load_all_patterns: bool = typer.Option(
        False, "--load-all-patterns",
        help="Load all available patterns from the pattern library."
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Minimal output. Only show errors and final results."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Detailed debug output. Shows all scanner activities and errors."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Preview what the scan would do without actually running it. Validates settings and shows plan."
    ),
):
    """
    Scan a website for visual bugs similar to a provided example.

    This command:
    1. Extracts bug pattern from example URL (or uses provided bug text)
    2. Generates flexible search patterns
    3. Scans the target site for similar bugs
    4. Reports all affected pages

    Configuration:
    - Use --config to load default settings from file (JSON or YAML)
    - CLI arguments override config file settings
    - Site-specific settings can be configured in config file

    Custom Patterns:
    - Use --pattern-file to load a single pattern from the pattern library
    - Specify multiple times to load multiple patterns
    - Use --load-all-patterns to load all available patterns
    - Patterns must exist in the patterns/ directory

    Incremental Mode:
    - With --incremental, results are written to .partial.json as matches are found
    - File always contains valid JSON with scan progress metadata
    - On completion, .partial.json is renamed to the final filename
    - On interruption (Ctrl+C), partial results are still usable

    Example without config:
        python -m src.analyzer.cli bug-finder scan \\
            --example-url "https://archive.org/web/.../page-with-bug" \\
            --site "https://www.example.com" \\
            --max-pages 100

    Example with custom pattern:
        python -m src.analyzer.cli bug-finder scan \\
            --site "https://www.example.com" \\
            --pattern-file wordpress_embed_bug \\
            --max-pages 500

    Example with multiple patterns:
        python -m src.analyzer.cli bug-finder scan \\
            --site "https://www.example.com" \\
            --pattern-file wordpress_embed_bug \\
            --pattern-file missing_alt_text

    Example with all patterns:
        python -m src.analyzer.cli bug-finder scan \\
            --site "https://www.example.com" \\
            --load-all-patterns

    Example with incremental mode:
        python -m src.analyzer.cli bug-finder scan \\
            --example-url "https://archive.org/web/.../page-with-bug" \\
            --site "https://www.example.com" \\
            --max-pages 1000 \\
            --incremental

    Example with config file:
        python -m src.analyzer.cli bug-finder scan \\
            --config bug-finder-config.json \\
            --site "https://www.example.com"
    """
    async def _run_scan_async():
        from bug_finder_cli import BugFinderCLI
        cli = BugFinderCLI(quiet=quiet, verbose=verbose)

        # Load configuration file if provided
        effective_config = {
            'max_pages': max_pages,
            'format': format,
        }

        if config:
            try:
                if not quiet:
                    console.print(f"[cyan]Loading config from: {config}[/cyan]")
                config_obj = ConfigLoader.load(config)
                if not quiet:
                    console.print(f"[green]✓ Config loaded[/green]")

                # Merge config with CLI overrides
                merged = ConfigMerger.merge(
                    config_obj,
                    {
                        'max_pages': max_pages,
                        'format': format,
                    },
                    site_url=site_to_scan
                )
                effective_config.update(merged)
            except FileNotFoundError:
                console.print(f"[red]Error: Config file not found: {config}[/red]")
                raise typer.Exit(code=1)
            except ValueError as e:
                console.print(f"[red]Error loading config: {e}[/red]")
                raise typer.Exit(code=1)
        else:
            # Use defaults if no config provided
            effective_config['max_pages'] = max_pages or 1000
            effective_config['format'] = format or 'txt'

        # Validate required arguments
        if not example_url:
            suggestion = "You need to provide a URL showing the bug.\n" \
                        "  - Use --example-url with a page that shows the bug\n" \
                        "  - Archive pages work great: web.archive.org/web/..."
            console.print("[red]Error: --example-url is required[/red]")
            console.print(f"[yellow]{suggestion}[/yellow]")
            raise typer.Exit(code=1)

        if not site_to_scan:
            suggestion = "You need to provide the site to scan.\n" \
                        "  - Use --site with your website's base URL\n" \
                        "  - Example: --site https://www.example.com"
            console.print("[red]Error: --site is required[/red]")
            console.print(f"[yellow]{suggestion}[/yellow]")
            raise typer.Exit(code=1)

        # Handle dry-run mode
        if dry_run:
            if not quiet:
                console.print("[bold cyan]DRY RUN - Preview Mode[/bold cyan]")
                console.print()
                console.print("[cyan]Scan Configuration:[/cyan]")
                console.print(f"  Example URL: {example_url}")
                console.print(f"  Site to scan: {site_to_scan}")
                console.print(f"  Max pages: {effective_config['max_pages']}")
                console.print(f"  Output format: {effective_config['format']}")
                console.print(f"  Incremental: {'Yes' if incremental else 'No'}")
                if config:
                    console.print(f"  Config file: {config}")
                console.print()

                console.print("[yellow]What will happen when you run without --dry-run:[/yellow]")
                console.print("  1. Fetch content from example URL")
                console.print("  2. Analyze and extract bug pattern")
                console.print("  3. Generate search patterns")
                console.print(f"  4. Scan up to {effective_config['max_pages']} pages from {site_to_scan}")
                console.print("  5. Report all pages containing similar bugs")
                console.print()
                console.print("[green]Settings look valid![/green]")
                console.print("[dim]To run the actual scan, remove --dry-run[/dim]")
            return

        if not quiet:
            console.print("[bold green]Bug Finder - Visual Bug Scanner[/bold green]")
            console.print(f"Example URL: {example_url}")
            console.print(f"Site to scan: {site_to_scan}")
            console.print(f"Max pages: {effective_config['max_pages']}")
            if incremental:
                console.print(f"Incremental output: [cyan]ENABLED[/cyan]")
            if config:
                console.print(f"Config file: {config}")
            console.print()

        # Determine output file for incremental mode
        incremental_output_file = None
        if incremental:
            if output:
                incremental_output_file = str(output.with_suffix(''))  # Remove extension for .partial.json
            else:
                from urllib.parse import urlparse
                parsed = urlparse(site_to_scan)
                site_slug = parsed.netloc.replace('www.', '').replace('.', '-')
                project_dir = Path("projects") / site_slug
                scans_dir = project_dir / "scans"
                scans_dir.mkdir(parents=True, exist_ok=True)
                incremental_output_file = str(scans_dir / f"bug_results_{site_slug}")

        # Generate scan ID for tracking
        scan_id = ScanManager.generate_scan_id()
        ScanManager.record_scan(scan_id, site_to_scan, example_url, effective_config['max_pages'])

        if not quiet:
            console.print(f"[dim]Scan ID: {scan_id}[/dim]")

        try:
            matches = await cli.find_bugs(
                example_url=example_url,
                site_to_scan=site_to_scan,
                max_pages=effective_config['max_pages'],
                bug_text=bug_text,
                incremental=incremental,
                output_file=incremental_output_file
            )

            if matches:
                if not quiet:
                    console.print(f"\n[bold red]Found {len(matches)} pages with bugs![/bold red]")
                    console.print("\nTop 10 affected pages:")
                    for i, match in enumerate(matches[:10], 1):
                        console.print(f"  {i}. [link]{match['url']}[/link]")
                        console.print(f"     Matches: {match['total_matches']} pattern(s)")

                    if len(matches) > 10:
                        console.print(f"\n  ... and {len(matches) - 10} more")

                # Output file - use projects directory structure
                if output:
                    output_file = Path(output)
                else:
                    from pathlib import Path
                    from urllib.parse import urlparse

                    # Create project slug from site URL
                    parsed = urlparse(site_to_scan)
                    site_slug = parsed.netloc.replace('www.', '').replace('.', '-')

                    # Ensure project directory exists
                    project_dir = Path("projects") / site_slug
                    scans_dir = project_dir / "scans"
                    scans_dir.mkdir(parents=True, exist_ok=True)

                    # Default output in scans subdirectory
                    output_file = scans_dir / f"bug_results_{site_slug}"

                # Prepare metadata for export
                metadata = {
                    'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'site_scanned': site_to_scan,
                    'example_url': example_url,
                    'pages_scanned': effective_config['max_pages'],
                    'config_file': str(config) if config else None,
                    'scan_id': scan_id,
                }

                # Export results in specified format
                export_results(matches, output_file, metadata, format=effective_config['format'])

                # Update scan registry
                ScanManager.update_scan(scan_id, "completed", str(output_file))

                # Show what was saved
                if not quiet:
                    if effective_config['format'] == 'all':
                        console.print(f"\n[green]Results saved in all formats:[/green]")
                        console.print(f"  - {output_file}.txt")
                        console.print(f"  - {output_file}.csv")
                        console.print(f"  - {output_file}.html")
                        console.print(f"  - {output_file}.json")
                    else:
                        ext = '.txt' if effective_config['format'] == 'txt' else f".{effective_config['format']}"
                        console.print(f"\n[green]Full results saved to: {output_file}{ext}[/green]")

                    console.print()
                    console.print("[cyan]Next steps:[/cyan]")
                    console.print(f"  1. Review results: {output_file}.txt")
                    console.print(f"  2. Compare with another scan: bug-finder compare")
                    console.print(f"  3. Resume if needed: bug-finder scan --resume {scan_id}")
            else:
                ScanManager.update_scan(scan_id, "completed_clean")
                if not quiet:
                    console.print("\n[bold green]No bugs found![/bold green]")
                    console.print("The site appears clean or bugs are on unscanned pages.")

        except ValueError as e:
            error_msg = str(e)
            ScanManager.update_scan(scan_id, "error")
            console.print(f"[red]Error: {error_msg}[/red]")

            # Provide helpful suggestions
            suggestion = SuggestiveErrorHandler.suggest_for_error(error_msg)
            if suggestion:
                console.print(f"\n[yellow]Suggestions:[/yellow]")
                console.print(f"[yellow]{suggestion}[/yellow]")

            raise typer.Exit(code=1)
        except Exception as e:
            error_msg = str(e)
            ScanManager.update_scan(scan_id, "error")
            console.print(f"[red]Unexpected error: {error_msg}[/red]")

            # Provide helpful suggestions
            suggestion = SuggestiveErrorHandler.suggest_for_error(error_msg)
            if suggestion:
                console.print(f"\n[yellow]Suggestions:[/yellow]")
                console.print(f"[yellow]{suggestion}[/yellow]")

            raise typer.Exit(code=1)

    try:
        asyncio.run(_run_scan_async())
    except Exception as e:
        console.print(f"[red]Failed to run bug finder: {e}[/red]")
        raise typer.Exit(code=1)


@bug_finder_app.command("config-example")
def bug_finder_config_example(
    output: Path = typer.Option(
        Path("bug-finder-config.json"), "--output", "-o",
        help="Output path for example config file (e.g., config.json or config.yaml)."
    ),
):
    """
    Generate an example configuration file for bug-finder.

    Creates a template config file showing all available options for:
    - Scan settings (max pages, depth, output format)
    - Output directory preferences
    - Pattern matching configuration
    - Site-specific overrides

    Example:
        python -m src.analyzer.cli bug-finder config-example
        python -m src.analyzer.cli bug-finder config-example --output my-config.yaml

    The generated file can be modified and used with:
        python -m src.analyzer.cli bug-finder scan --config my-config.json
    """
    try:
        # Detect format from file extension
        format_map = {
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }
        suffix = output.suffix.lower()
        format = format_map.get(suffix, 'json')

        console.print(f"[cyan]Generating example config file...[/cyan]")
        create_example_config(output, format=format)

        console.print(f"[green]✓ Example config created: {output}[/green]")
        console.print(f"[cyan]Format: {format.upper()}[/cyan]")
        console.print()
        console.print("[bold]How to use:[/bold]")
        console.print(f"1. Edit {output} to customize your settings")
        console.print(f"2. Run: python -m src.analyzer.cli bug-finder scan --config {output} --site <URL>")
        console.print()
        console.print("[dim]Config file will be saved with example site-specific settings.[/dim]")

    except Exception as e:
        console.print(f"[red]Error generating config: {e}[/red]")
        raise typer.Exit(code=1)


@bug_finder_app.command("export")
def bug_finder_export(
    input: Path = typer.Option(
        ..., "--input", "-i",
        help="Path to JSON results file (required).",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f",
        help="Output format: markdown, slack, or html (default: markdown)."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Custom output path (optional). If not specified, auto-determined based on input file."
    ),
):
    """
    Export bug scan results to various formats.

    Supports:
    - markdown: Standard markdown report for documentation/chat
    - slack: Ultra-concise text snippet for Slack/chat pasting
    - html: Professional HTML report with styling and interactivity

    Example:
        python -m src.analyzer.cli bug-finder export \\
            --input projects/wpr-org/scans/bug_results_wpr_complete.json \\
            --format markdown
    """
    try:
        # Validate format
        valid_formats = ['markdown', 'slack', 'html']
        if format not in valid_formats:
            console.print(f"[red]Error: Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}[/red]")
            raise typer.Exit(code=1)

        # Load JSON results file
        console.print(f"[cyan]Loading results from: {input}[/cyan]")
        try:
            with open(input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON file: {e}[/red]")
            raise typer.Exit(code=1)
        except IOError as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            raise typer.Exit(code=1)

        # Extract results and metadata
        matches = data.get('results', [])
        metadata = data.get('metadata', {})

        if not matches:
            console.print("[yellow]Warning: No results found in JSON file.[/yellow]")
            return

        console.print(f"[cyan]Found {len(matches)} pages with bugs[/cyan]")

        # Determine output path if not specified
        if output is None:
            input_path = Path(input)
            if format == 'markdown':
                output_path = input_path.with_suffix('.md')
            elif format == 'slack':
                output_path = input_path.with_stem(input_path.stem + '_slack').with_suffix('.txt')
            elif format == 'html':
                output_path = input_path.with_suffix('.html')
        else:
            output_path = Path(output)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export based on format
        console.print(f"[cyan]Exporting to {format.upper()} format...[/cyan]")

        if format == 'markdown':
            export_to_markdown(matches, output_path, metadata)
        elif format == 'slack':
            export_to_slack_snippet(matches, output_path, metadata)
        elif format == 'html':
            export_to_html(matches, output_path, metadata, include_fixes=False)

        console.print(f"[green]✓ Export successful![/green]")
        console.print(f"[green]Output saved to: {output_path}[/green]")
        console.print(f"[cyan]Format: {format.upper()}[/cyan]")
        console.print(f"[cyan]Pages exported: {len(matches)}[/cyan]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(code=1)


@bug_finder_app.command("patterns")
def bug_finder_patterns_root():
    """
    Manage custom bug patterns for scanning.

    Patterns are reusable bug definitions that can be shared across projects.
    Use subcommands to list, add, test, or manage patterns.

    Available subcommands:
        list    - Show all available patterns
        add     - Create a new pattern interactively
        test    - Test a pattern against content or URL
        template - Get a pattern template
    """
    console.print("[bold cyan]Bug Finder Pattern Management[/bold cyan]")
    console.print()
    console.print("Use one of these subcommands:")
    console.print("  list       - List all available patterns")
    console.print("  add        - Create a new pattern")
    console.print("  test       - Test a pattern against content or URL")
    console.print("  template   - Show pattern template")
    console.print()
    console.print("Examples:")
    console.print("  python -m src.analyzer.cli bug-finder patterns list")
    console.print("  python -m src.analyzer.cli bug-finder patterns add")
    console.print("  python -m src.analyzer.cli bug-finder patterns test --pattern wordpress_embed_bug")


patterns_app = typer.Typer(
    name="patterns",
    help="Manage custom bug patterns for scanning."
)
bug_finder_app.add_typer(patterns_app)


@patterns_app.command("list")
def patterns_list(
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed information about each pattern."
    ),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="Output format: table, json, or csv."
    ),
):
    """
    List all available bug patterns.

    Shows pattern names, descriptions, and severity levels.
    Use --verbose for detailed information including tags, author, and timestamps.

    Example:
        python -m src.analyzer.cli bug-finder patterns list
        python -m src.analyzer.cli bug-finder patterns list --verbose
        python -m src.analyzer.cli bug-finder patterns list --format json
    """
    from src.analyzer.pattern_library import PatternLibrary

    try:
        library = PatternLibrary()
        patterns = library.list_patterns()

        if not patterns:
            console.print("[yellow]No patterns found in the pattern library.[/yellow]")
            console.print()
            console.print("To create your first pattern, run:")
            console.print("  python -m src.analyzer.cli bug-finder patterns add")
            return

        console.print(f"[bold cyan]Available Patterns ({len(patterns)})[/bold cyan]")
        console.print()

        if format == "json":
            import json
            console.print_json(data=patterns)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if patterns and "error" not in patterns[0]:
                writer = csv.DictWriter(output, fieldnames=patterns[0].keys())
                writer.writeheader()
                for p in patterns:
                    if "error" not in p:
                        writer.writerow(p)
            console.print(output.getvalue())
        else:  # table format
            from rich.table import Table

            table = Table(title="Bug Patterns")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Severity", style="yellow")
            table.add_column("Patterns", justify="right", style="magenta")

            if verbose:
                table.add_column("Tags", style="green")
                table.add_column("Author", style="blue")
                table.add_column("Created", style="dim")

            for p in patterns:
                if "error" in p:
                    table.add_row(
                        p["filename"],
                        f"[red]Error: {p['error']}[/red]",
                        "",
                        ""
                    )
                else:
                    severity_color = {
                        "low": "yellow",
                        "medium": "yellow",
                        "high": "red",
                        "critical": "bold red",
                    }.get(p.get("severity", "medium"), "yellow")

                    row = [
                        p["name"],
                        p["description"][:50] + "..." if len(p["description"]) > 50 else p["description"],
                        f"[{severity_color}]{p['severity']}[/{severity_color}]",
                        str(p["patterns_count"]),
                    ]

                    if verbose:
                        tags = ", ".join(p.get("tags", [])[:3])
                        if len(p.get("tags", [])) > 3:
                            tags += "..."
                        row.extend([
                            tags,
                            p.get("author", "Unknown")[:15] if p.get("author") else "-",
                            p.get("created_at", "N/A")[:10] if p.get("created_at") else "-",
                        ])

                    table.add_row(*row)

            console.print(table)

        console.print()
        console.print(f"[dim]Patterns directory: {library.patterns_dir}[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading patterns: {e}[/red]")
        raise typer.Exit(code=1)


@patterns_app.command("add")
def patterns_add(
    name: Optional[str] = typer.Option(
        None, "--name", "-n",
        help="Pattern name (e.g., my_pattern)."
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d",
        help="Pattern description."
    ),
    severity: str = typer.Option(
        "medium", "--severity", "-s",
        help="Severity level: low, medium, high, or critical."
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f",
        help="Load pattern from existing JSON file instead of interactive mode."
    ),
):
    """
    Create a new bug pattern interactively.

    Guides you through creating a new pattern with:
    - Pattern name and description
    - Regular expressions to match bugs
    - Example matches
    - Severity and tags

    Example interactive:
        python -m src.analyzer.cli bug-finder patterns add

    Example from file:
        python -m src.analyzer.cli bug-finder patterns add --file my_pattern.json

    Example with options:
        python -m src.analyzer.cli bug-finder patterns add \\
            --name "my_pattern" \\
            --description "Detects my specific bug" \\
            --severity high
    """
    from src.analyzer.pattern_library import PatternLibrary, Pattern
    import sys

    try:
        library = PatternLibrary()

        if file:
            # Load from existing file
            if not file.exists():
                console.print(f"[red]Error: File not found: {file}[/red]")
                raise typer.Exit(code=1)

            try:
                pattern = library.load_pattern_file(file)
                saved_path = library.save_pattern(pattern, file.name)
                console.print(f"[green]✓ Pattern loaded and saved: {saved_path}[/green]")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(code=1)
            return

        # Interactive mode
        console.print("[bold cyan]Create New Pattern[/bold cyan]")
        console.print()

        # Get pattern name
        if name is None:
            name = typer.prompt("Pattern name (lowercase, underscores)", default="new_pattern")

        if not name:
            console.print("[red]Error: Pattern name is required[/red]")
            raise typer.Exit(code=1)

        # Check for duplicates
        if library.load_pattern_by_name(name):
            console.print(f"[red]Error: Pattern '{name}' already exists[/red]")
            raise typer.Exit(code=1)

        # Get description
        if description is None:
            description = typer.prompt("Description", default="")

        if not description:
            console.print("[red]Error: Description is required[/red]")
            raise typer.Exit(code=1)

        # Get regex patterns
        console.print()
        console.print("[cyan]Enter regex patterns (one per line, empty line to finish):[/cyan]")
        patterns = []
        pattern_num = 1

        while True:
            pattern_input = typer.prompt(f"Pattern {pattern_num}", default="")
            if not pattern_input:
                if patterns:
                    break
                console.print("[yellow]At least one pattern is required[/yellow]")
                continue

            # Validate regex
            try:
                re.compile(pattern_input)
                patterns.append(pattern_input)
                pattern_num += 1
            except re.error as e:
                console.print(f"[red]Invalid regex: {e}[/red]")

        # Get examples
        console.print()
        console.print("[cyan]Enter examples (one per line, empty line to finish):[/cyan]")
        examples = []
        example_num = 1

        while True:
            example_input = typer.prompt(f"Example {example_num}", default="")
            if not example_input:
                if examples:
                    break
                console.print("[yellow]At least one example is required[/yellow]")
                continue

            examples.append(example_input)
            example_num += 1

        # Get tags
        console.print()
        tags_input = typer.prompt(
            "Tags (comma-separated, optional)",
            default=""
        )
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

        # Get author
        author = typer.prompt("Author (optional)", default="")

        # Create pattern
        pattern = library.create_pattern_from_template(
            name=name,
            description=description,
            regex_patterns=patterns,
            severity=severity,
            examples=examples,
            tags=tags or None,
            author=author or None,
        )

        # Save pattern
        saved_path = library.save_pattern(pattern)

        console.print()
        console.print(f"[green]✓ Pattern created successfully![/green]")
        console.print(f"[green]Saved to: {saved_path}[/green]")
        console.print()
        console.print(f"[cyan]Pattern details:[/cyan]")
        console.print(f"  Name: {pattern.name}")
        console.print(f"  Severity: {pattern.severity}")
        console.print(f"  Patterns: {len(pattern.patterns)}")
        console.print(f"  Examples: {len(pattern.examples)}")

        # Test the pattern
        console.print()
        test_pattern = typer.confirm("Test pattern now?", default=True)

        if test_pattern and pattern.examples:
            console.print()
            console.print("[cyan]Testing pattern on examples...[/cyan]")

            result = library.test_pattern_on_content(pattern, " ".join(pattern.examples))

            if result["total_matches"] > 0:
                console.print(f"[green]✓ Pattern matched {result['total_matches']} time(s) in examples[/green]")
            else:
                console.print(f"[yellow]⚠ Pattern didn't match any examples (may need adjustment)[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@patterns_app.command("test")
def patterns_test(
    pattern: Optional[str] = typer.Option(
        None, "--pattern", "-p",
        help="Pattern name to test (e.g., wordpress_embed_bug)."
    ),
    content: Optional[str] = typer.Option(
        None, "--content", "-c",
        help="Content to test against (HTML or text)."
    ),
    url: Optional[str] = typer.Option(
        None, "--url", "-u",
        help="URL to fetch and test against."
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f",
        help="File containing content to test (HTML or text)."
    ),
):
    """
    Test a pattern against content or a URL.

    Test patterns in three ways:
    1. Against provided text content
    2. Against a file's content
    3. Against a live URL (requires crawl4ai)

    Example with text:
        python -m src.analyzer.cli bug-finder patterns test \\
            --pattern wordpress_embed_bug \\
            --content "<div>field[0]</div>"

    Example with URL:
        python -m src.analyzer.cli bug-finder patterns test \\
            --pattern missing_alt_text \\
            --url https://example.com/page

    Example with file:
        python -m src.analyzer.cli bug-finder patterns test \\
            --pattern broken_image_tag \\
            --file test_page.html
    """
    from src.analyzer.pattern_library import PatternLibrary

    try:
        library = PatternLibrary()

        if not pattern:
            console.print("[red]Error: --pattern is required[/red]")
            raise typer.Exit(code=1)

        # Load the pattern
        loaded_pattern = library.load_pattern_by_name(pattern)
        if not loaded_pattern:
            console.print(f"[red]Error: Pattern '{pattern}' not found[/red]")
            raise typer.Exit(code=1)

        console.print(f"[bold cyan]Testing Pattern: {loaded_pattern.name}[/bold cyan]")
        console.print(f"Description: {loaded_pattern.description}")
        console.print(f"Severity: {loaded_pattern.severity}")
        console.print()

        # Determine test content
        test_content = None

        if content:
            test_content = content
            source = "provided text"
        elif file:
            if not file.exists():
                console.print(f"[red]Error: File not found: {file}[/red]")
                raise typer.Exit(code=1)
            with open(file, "r", encoding="utf-8") as f:
                test_content = f.read()
            source = f"file: {file}"
        elif url:
            console.print(f"[cyan]Fetching content from URL...[/cyan]")
            result = library.test_pattern_on_url(loaded_pattern, url)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                raise typer.Exit(code=1)

            console.print(f"[cyan]URL: {result.get('url', url)}[/cyan]")
            console.print(f"[cyan]HTML length: {result.get('html_length', 'unknown')} bytes[/cyan]")
            console.print(f"[cyan]Total matches: {result.get('total_matches', 0)}[/cyan]")
            console.print()

            if result.get("total_matches", 0) > 0:
                console.print("[green]Pattern Matches:[/green]")
                for regex, match_info in result.get("matches_by_pattern", {}).items():
                    if "count" in match_info:
                        console.print(f"  [cyan]{regex}[/cyan]")
                        console.print(f"    Count: {match_info['count']}")
                        if match_info.get("matches"):
                            for i, m in enumerate(match_info["matches"][:3], 1):
                                preview = str(m)[:80]
                                console.print(f"    {i}. {preview}...")
            else:
                console.print("[yellow]No matches found[/yellow]")

            return

        if not test_content:
            console.print("[red]Error: Must provide one of: --content, --url, or --file[/red]")
            raise typer.Exit(code=1)

        # Test against provided content
        console.print(f"[cyan]Testing against: {source}[/cyan]")
        console.print(f"[cyan]Content length: {len(test_content)} bytes[/cyan]")
        console.print()

        result = library.test_pattern_on_content(loaded_pattern, test_content)

        if result["total_matches"] > 0:
            console.print(f"[green]Found {result['total_matches']} match(es)[/green]")
            console.print()
            console.print("[green]Pattern Matches:[/green]")

            for regex, match_info in result["matches_by_pattern"].items():
                if "count" in match_info:
                    console.print(f"  [cyan]{regex}[/cyan]")
                    console.print(f"    Count: {match_info['count']}")

                    if match_info.get("matches"):
                        console.print(f"    Samples (first 3):")
                        for i, m in enumerate(match_info["matches"][:3], 1):
                            preview = str(m)[:100]
                            console.print(f"      {i}. {preview}")
                elif "error" in match_info:
                    console.print(f"  [red]{regex}[/red]")
                    console.print(f"    Error: {match_info['error']}")
        else:
            console.print("[yellow]No matches found[/yellow]")
            console.print()
            console.print("This could mean:")
            console.print("  1. The content doesn't contain the pattern")
            console.print("  2. The regex needs adjustment")
            console.print("  3. The pattern is working correctly (negative test)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@patterns_app.command("template")
def patterns_template(
    format: str = typer.Option(
        "json", "--format", "-f",
        help="Output format: json or yaml."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Save template to file instead of printing."
    ),
):
    """
    Get a template for creating new patterns.

    The template shows the structure and all available fields for defining
    a custom bug pattern.

    Example print to console:
        python -m src.analyzer.cli bug-finder patterns template

    Example save to file:
        python -m src.analyzer.cli bug-finder patterns template \\
            --output my_pattern_template.json

    Example with YAML:
        python -m src.analyzer.cli bug-finder patterns template \\
            --format yaml \\
            --output my_pattern_template.yaml
    """
    from src.analyzer.pattern_library import PatternLibrary
    import json

    try:
        library = PatternLibrary()
        template = library.get_pattern_template()

        if format == "yaml":
            try:
                import yaml
                content = yaml.dump(template, default_flow_style=False, sort_keys=False)
            except ImportError:
                console.print("[red]Error: PyYAML not installed. Use --format json instead.[/red]")
                raise typer.Exit(code=1)
        else:
            content = json.dumps(template, indent=2, ensure_ascii=False)

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]✓ Template saved to: {output}[/green]")
            console.print()
            console.print("[cyan]To use this template:[/cyan]")
            console.print(f"1. Edit {output}")
            console.print(f"2. Run: python -m src.analyzer.cli bug-finder patterns add --file {output}")
        else:
            console.print(f"[bold cyan]Pattern Template ({format.upper()})[/bold cyan]")
            console.print()
            console.print(content)
            console.print()
            console.print("[dim]Save this template with: --output filename.json[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


# New usability enhancement commands
@bug_finder_app.command("list-scans")
def bug_finder_list_scans(
    limit: int = typer.Option(
        20, "--limit", "-l",
        help="Maximum number of scans to display."
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Filter by status: running, completed, completed_clean, or error."
    ),
):
    """
    List recent bug-finder scans and their status.

    Shows a table of your recent scans including:
    - Scan ID (for use with --resume)
    - Site scanned
    - Number of pages
    - Status (running, completed, error, etc.)
    - When it was started
    - Duration or completion time

    Examples:
        python -m src.analyzer.cli bug-finder list-scans
        python -m src.analyzer.cli bug-finder list-scans --limit 10
        python -m src.analyzer.cli bug-finder list-scans --status error
        python -m src.analyzer.cli bug-finder list-scans --status completed
    """
    try:
        scans = ScanManager.list_scans(limit=limit)

        if not scans:
            console.print("[yellow]No scans found. Start your first scan with:[/yellow]")
            console.print()
            console.print("  python -m src.analyzer.cli bug-finder scan \\")
            console.print("    --example-url <archived_page> \\")
            console.print("    --site <your_website>")
            return

        # Filter by status if provided
        if status:
            scans = [s for s in scans if s["status"] == status]

            if not scans:
                console.print(f"[yellow]No scans with status '{status}'[/yellow]")
                return

        console.print(f"[bold cyan]Recent Bug Finder Scans ({len(scans)})[/bold cyan]")
        console.print()

        table = Table(title="Scan History")
        table.add_column("Scan ID", style="cyan", overflow="fold")
        table.add_column("Site", style="green")
        table.add_column("Pages", justify="right")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="dim")
        table.add_column("Duration", justify="right")

        for scan in scans:
            # Calculate duration
            try:
                started = datetime.fromisoformat(scan["started_at"])
                if scan["completed_at"]:
                    completed = datetime.fromisoformat(scan["completed_at"])
                    duration = completed - started
                    duration_str = f"{duration.total_seconds():.0f}s"
                else:
                    # Still running
                    duration = datetime.now() - started
                    duration_str = f"{duration.total_seconds():.0f}s (running)"
            except Exception:
                duration_str = "-"

            # Status color
            status_color = {
                "completed": "green",
                "completed_clean": "blue",
                "error": "red",
                "running": "yellow",
            }.get(scan["status"], "white")

            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(scan["site_url"]).netloc.replace("www.", "")

            table.add_row(
                scan["id"][:20] + "...",
                domain,
                str(scan["max_pages"]),
                f"[{status_color}]{scan['status']}[/{status_color}]",
                scan["started_at"].split("T")[0],
                duration_str,
            )

        console.print(table)
        console.print()
        console.print("[cyan]Tips:[/cyan]")
        console.print("  - Use scan ID with: bug-finder scan --resume <scan_id>")
        console.print("  - Compare scans with: bug-finder compare --scan1 <id1> --scan2 <id2>")
        console.print("  - Filter by status: --status completed")

    except Exception as e:
        console.print(f"[red]Error loading scans: {e}[/red]")
        raise typer.Exit(code=1)


@bug_finder_app.command("doctor")
def bug_finder_doctor():
    """
    Check your environment setup for Bug Finder.

    Verifies:
    - Python version (3.11+)
    - Required dependencies (crawl4ai, typer, rich, etc.)
    - Playwright/Chromium installation
    - File permissions and disk space

    Run this if you're having issues with Bug Finder or after updating.

    Example:
        python -m src.analyzer.cli bug-finder doctor
    """
    console.print("[bold cyan]Bug Finder Environment Check[/bold cyan]")
    console.print()

    # Run all checks
    checks = EnvironmentChecker.run_all_checks()

    # Display results
    table = Table(title="Environment Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    all_ok = True
    for check in checks:
        status = check.get("status", "unknown")
        status_color = {
            "ok": "green",
            "missing": "red",
            "error": "red",
            "warning": "yellow",
        }.get(status, "white")

        status_str = f"[{status_color}]{status.upper()}[/{status_color}]"

        details = ""
        if status == "ok":
            if "version" in check:
                details = f"v{check['version']}"
            elif "message" in check:
                details = check["message"]
        elif "message" in check:
            details = check["message"]
            all_ok = False
        else:
            all_ok = False

        table.add_row(check["name"], status_str, details)

    console.print(table)
    console.print()

    if all_ok:
        console.print("[bold green]All systems ready![/bold green]")
        console.print()
        console.print("You can start using Bug Finder:")
        console.print("  python -m src.analyzer.cli bug-finder scan \\")
        console.print("    --example-url <url> \\")
        console.print("    --site <website>")
    else:
        console.print("[bold yellow]Some components need attention[/bold yellow]")
        console.print()
        console.print("Follow the instructions above to install missing dependencies.")
        console.print()
        console.print("Common fix:")
        console.print("  pip install crawl4ai")
        console.print("  python -m playwright install chromium")
        raise typer.Exit(code=1)


@bug_finder_app.command("compare")
def bug_finder_compare(
    scan1: Optional[str] = typer.Option(
        None, "--scan1", "-a",
        help="First scan ID to compare (or use most recent)."
    ),
    scan2: Optional[str] = typer.Option(
        None, "--scan2", "-b",
        help="Second scan ID to compare."
    ),
    file1: Optional[Path] = typer.Option(
        None, "--file1", "-f",
        help="Path to first results file (alternative to scan ID)."
    ),
    file2: Optional[Path] = typer.Option(
        None, "--file2", "-g",
        help="Path to second results file (alternative to scan ID)."
    ),
):
    """
    Compare results between two scans.

    Shows:
    - New bugs (in scan2 but not in scan1)
    - Fixed bugs (in scan1 but not in scan2)
    - Unchanged bugs (in both)
    - URLs that changed status

    Examples:
        python -m src.analyzer.cli bug-finder compare
        python -m src.analyzer.cli bug-finder compare --scan1 scan_001 --scan2 scan_002
        python -m src.analyzer.cli bug-finder compare --file1 results1.json --file2 results2.json
    """
    try:
        # Determine which scans to compare
        if file1 and file2:
            # Load from files
            console.print(f"[cyan]Loading results from files...[/cyan]")
            with open(file1, 'r', encoding='utf-8') as f:
                data1 = json.load(f)
            with open(file2, 'r', encoding='utf-8') as f:
                data2 = json.load(f)

            results1 = data1.get('results', [])
            results2 = data2.get('results', [])
            metadata1 = data1.get('metadata', {})
            metadata2 = data2.get('metadata', {})

        else:
            # Load from scan IDs
            scans = ScanManager.list_scans(limit=100)

            if not scans or len(scans) < 2:
                console.print("[yellow]Not enough scans to compare. Need at least 2 completed scans.[/yellow]")
                raise typer.Exit(code=1)

            # Use provided IDs or most recent two
            if not scan1:
                scan1_data = scans[0]
            else:
                scan1_data = ScanManager.get_scan(scan1)
                if not scan1_data:
                    console.print(f"[red]Scan '{scan1}' not found[/red]")
                    raise typer.Exit(code=1)

            if not scan2:
                scan2_data = scans[1]
            else:
                scan2_data = ScanManager.get_scan(scan2)
                if not scan2_data:
                    console.print(f"[red]Scan '{scan2}' not found[/red]")
                    raise typer.Exit(code=1)

            # Load results from files
            if not scan1_data.get("output_file") or not scan2_data.get("output_file"):
                console.print("[red]Error: Scans don't have output files recorded[/red]")
                raise typer.Exit(code=1)

            # Try loading JSON results
            try:
                file1_path = Path(scan1_data["output_file"] + ".json")
                file2_path = Path(scan2_data["output_file"] + ".json")

                with open(file1_path, 'r', encoding='utf-8') as f:
                    data1 = json.load(f)
                with open(file2_path, 'r', encoding='utf-8') as f:
                    data2 = json.load(f)

                results1 = data1.get('results', [])
                results2 = data2.get('results', [])
                metadata1 = data1.get('metadata', {})
                metadata2 = data2.get('metadata', {})

            except FileNotFoundError as e:
                console.print(f"[red]Error: Results file not found: {e}[/red]")
                raise typer.Exit(code=1)

        # Extract URLs from results
        urls1 = {r['url'] for r in results1}
        urls2 = {r['url'] for r in results2}

        # Calculate differences
        new_bugs = urls2 - urls1
        fixed_bugs = urls1 - urls2
        unchanged = urls1 & urls2

        # Display comparison
        console.print("[bold cyan]Scan Comparison Report[/bold cyan]")
        console.print()

        console.print("[cyan]Scan 1 (older):[/cyan]")
        console.print(f"  Date: {metadata1.get('scan_date', 'Unknown')}")
        console.print(f"  Site: {metadata1.get('site_scanned', 'Unknown')}")
        console.print(f"  Results: {len(results1)} pages with bugs")
        console.print()

        console.print("[cyan]Scan 2 (newer):[/cyan]")
        console.print(f"  Date: {metadata2.get('scan_date', 'Unknown')}")
        console.print(f"  Site: {metadata2.get('site_scanned', 'Unknown')}")
        console.print(f"  Results: {len(results2)} pages with bugs")
        console.print()

        # Summary
        table = Table(title="Comparison Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="yellow")
        table.add_column("Change", justify="right")

        table.add_row("New bugs", str(len(new_bugs)), f"[green]+{len(new_bugs)}[/green]")
        table.add_row("Fixed bugs", str(len(fixed_bugs)), f"[red]-{len(fixed_bugs)}[/red]")
        table.add_row("Unchanged", str(len(unchanged)), "[blue]=" + str(len(unchanged)) + "[/blue]")

        console.print(table)
        console.print()

        # Show details if not too many
        if new_bugs:
            console.print("[bold green]New Bugs Found:[/bold green]")
            for i, url in enumerate(sorted(new_bugs)[:10], 1):
                console.print(f"  {i}. {url}")
            if len(new_bugs) > 10:
                console.print(f"  ... and {len(new_bugs) - 10} more")
            console.print()

        if fixed_bugs:
            console.print("[bold blue]Bugs Fixed:[/bold blue]")
            for i, url in enumerate(sorted(fixed_bugs)[:10], 1):
                console.print(f"  {i}. {url}")
            if len(fixed_bugs) > 10:
                console.print(f"  ... and {len(fixed_bugs) - 10} more")
            console.print()

        if not new_bugs and not fixed_bugs:
            console.print("[green]No changes detected between scans.[/green]")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing results file: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


# ============================================================================
# SCHEDULER COMMANDS
# ============================================================================

@schedule_app.command("add")
def schedule_add(
    name: str = typer.Argument(..., help="Name for this schedule"),
    site_url: str = typer.Option(..., "--site", help="Site URL to scan"),
    example_url: str = typer.Option(..., "--example", help="Example URL with the bug"),
    frequency: str = typer.Option(
        "daily",
        "--frequency",
        help="Frequency: hourly, daily, weekly, or custom"
    ),
    max_pages: int = typer.Option(
        1000,
        "--max-pages",
        help="Maximum pages to scan (0 for all)"
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
        help="Custom cron expression (required if frequency=custom)"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output",
        help="Output directory for results"
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        help="Comma-separated tags"
    ),
):
    """Create a new scheduled scan."""
    try:
        from src.analyzer.scheduler import (
            ScheduleManager, ScheduleConfig, ScheduleFrequency, generate_schedule_id
        )

        # Validate frequency
        valid_frequencies = [f.value for f in ScheduleFrequency]
        if frequency not in valid_frequencies:
            console.print(f"[red]Invalid frequency. Must be one of: {', '.join(valid_frequencies)}[/red]")
            raise typer.Exit(code=1)

        # Validate cron expression for custom frequency
        if frequency == "custom" and not cron:
            console.print("[red]--cron expression required when frequency=custom[/red]")
            raise typer.Exit(code=1)

        # Generate schedule ID
        schedule_id = generate_schedule_id(name)

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # Create schedule
        schedule = ScheduleConfig(
            id=schedule_id,
            name=name,
            site_url=site_url,
            example_url=example_url,
            frequency=frequency,
            max_pages=max_pages,
            cron_expression=cron,
            output_dir=output_dir,
            tags=tag_list,
        )

        manager = ScheduleManager()
        manager.add_schedule(schedule)

        console.print(f"[green]✓ Schedule created successfully[/green]")
        console.print(f"  ID: {schedule_id}")
        console.print(f"  Name: {name}")
        console.print(f"  Frequency: {frequency}")
        if cron:
            console.print(f"  Cron: {cron}")
        console.print(f"  Site: {site_url}")
        console.print(f"  Max pages: {max_pages}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("list")
def schedule_list(
    enabled_only: bool = typer.Option(
        False,
        "--enabled",
        help="Show only enabled schedules"
    ),
):
    """List all scheduled scans."""
    try:
        from src.analyzer.scheduler import ScheduleManager

        manager = ScheduleManager()
        schedules = manager.list_schedules(enabled_only=enabled_only)

        if not schedules:
            console.print("[yellow]No schedules found[/yellow]")
            return

        table = Table(title="Scheduled Scans")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Frequency", style="blue")
        table.add_column("Site", style="magenta")
        table.add_column("Max Pages", justify="right")
        table.add_column("Status")
        table.add_column("Last Run")

        for schedule in schedules:
            status = "[green]enabled[/green]" if schedule.enabled else "[red]disabled[/red]"
            last_run = schedule.last_run[:10] if schedule.last_run else "-"

            table.add_row(
                schedule.id[:16] + "...",
                schedule.name,
                schedule.frequency,
                schedule.site_url[:30] + "..." if len(schedule.site_url) > 30 else schedule.site_url,
                str(schedule.max_pages),
                status,
                last_run,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(schedules)} schedule(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("show")
def schedule_show(
    schedule_id: str = typer.Argument(..., help="Schedule ID"),
):
    """Show details of a specific schedule."""
    try:
        from src.analyzer.scheduler import ScheduleManager

        manager = ScheduleManager()
        schedule = manager.get_schedule(schedule_id)

        if not schedule:
            console.print(f"[red]Schedule '{schedule_id}' not found[/red]")
            raise typer.Exit(code=1)

        console.print(f"[bold]Schedule Details[/bold]\n")
        console.print(f"ID:              {schedule.id}")
        console.print(f"Name:            {schedule.name}")
        console.print(f"Site URL:        {schedule.site_url}")
        console.print(f"Example URL:     {schedule.example_url}")
        console.print(f"Frequency:       {schedule.frequency}")
        console.print(f"Max Pages:       {schedule.max_pages}")
        console.print(f"Status:          {'[green]enabled[/green]' if schedule.enabled else '[red]disabled[/red]'}")

        if schedule.cron_expression:
            console.print(f"Cron:            {schedule.cron_expression}")
        if schedule.output_dir:
            console.print(f"Output Dir:      {schedule.output_dir}")
        if schedule.tags:
            console.print(f"Tags:            {', '.join(schedule.tags)}")

        console.print(f"Created:         {schedule.created_at[:10]}")
        if schedule.last_run:
            console.print(f"Last Run:        {schedule.last_run[:19]}")
        if schedule.next_run:
            console.print(f"Next Run:        {schedule.next_run[:19]}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("remove")
def schedule_remove(
    schedule_id: str = typer.Argument(..., help="Schedule ID to remove"),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation"
    ),
):
    """Delete a scheduled scan."""
    try:
        from src.analyzer.scheduler import ScheduleManager

        manager = ScheduleManager()
        schedule = manager.get_schedule(schedule_id)

        if not schedule:
            console.print(f"[red]Schedule '{schedule_id}' not found[/red]")
            raise typer.Exit(code=1)

        if not confirm:
            console.print(f"Remove schedule '[bold]{schedule.name}[/bold]' ({schedule_id})?")
            if not typer.confirm("Continue"):
                console.print("[yellow]Cancelled[/yellow]")
                return

        manager.remove_schedule(schedule_id)
        console.print(f"[green]✓ Schedule removed[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("enable")
def schedule_enable(
    schedule_id: str = typer.Argument(..., help="Schedule ID to enable"),
):
    """Enable a disabled schedule."""
    try:
        from src.analyzer.scheduler import ScheduleManager

        manager = ScheduleManager()
        if manager.enable_schedule(schedule_id):
            schedule = manager.get_schedule(schedule_id)
            console.print(f"[green]✓ Schedule enabled: {schedule.name}[/green]")
        else:
            console.print(f"[red]Schedule '{schedule_id}' not found[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("disable")
def schedule_disable(
    schedule_id: str = typer.Argument(..., help="Schedule ID to disable"),
):
    """Disable a schedule."""
    try:
        from src.analyzer.scheduler import ScheduleManager

        manager = ScheduleManager()
        if manager.disable_schedule(schedule_id):
            schedule = manager.get_schedule(schedule_id)
            console.print(f"[green]✓ Schedule disabled: {schedule.name}[/green]")
        else:
            console.print(f"[red]Schedule '{schedule_id}' not found[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@schedule_app.command("run")
def schedule_run(
    schedule_id: str = typer.Argument(..., help="Schedule ID to run"),
):
    """Run a schedule immediately (skip the schedule)."""
    try:
        from src.analyzer.scheduler import ScheduledScanRunner

        runner = ScheduledScanRunner()
        result = runner.run_schedule_sync(schedule_id)

        if result["success"]:
            console.print(f"[green]✓ Scan completed successfully[/green]")
            console.print(f"  Pages crawled: {result['pages_crawled']}")
            console.print(f"  Output dir: {result['output_dir']}")
        else:
            console.print(f"[red]✗ Scan failed[/red]")
            console.print(f"  Error: {result['error']}")
            raise typer.Exit(code=1)

    except ValueError as e:
        console.print(f"[red]Schedule not found: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


# ============================================================================
# DAEMON COMMANDS
# ============================================================================

@daemon_app.command("start")
def daemon_start(
    background: bool = typer.Option(
        True,
        "--background",
        help="Run daemon in background"
    ),
):
    """Start the scheduler daemon."""
    try:
        from src.analyzer.scheduler import SchedulerDaemon

        daemon = SchedulerDaemon()
        status = daemon.get_status()

        if status["running"]:
            console.print(f"[yellow]Daemon already running (PID: {status['pid']})[/yellow]")
            return

        console.print("[cyan]Starting scheduler daemon...[/cyan]")

        if background:
            # Fork to background using subprocess
            import subprocess
            import sys

            python_exe = sys.executable
            script_code = (
                "from src.analyzer.scheduler import SchedulerDaemon; "
                "daemon = SchedulerDaemon(); "
                "daemon.start()"
            )

            process = subprocess.Popen(
                [python_exe, "-c", script_code],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            console.print(f"[green]✓ Daemon started in background (PID: {process.pid})[/green]")
            console.print(f"[dim]View logs: tail -f ~/.website-analyzer/logs/scheduler.log[/dim]")
        else:
            # Run in foreground (blocks)
            daemon.start()

    except ImportError:
        console.print("[red]APScheduler not installed. Install with: pip install apscheduler[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@daemon_app.command("stop")
def daemon_stop():
    """Stop the scheduler daemon."""
    try:
        from src.analyzer.scheduler import SchedulerDaemon
        import signal

        daemon = SchedulerDaemon()
        status = daemon.get_status()

        if not status["running"]:
            console.print("[yellow]Daemon is not running[/yellow]")
            return

        pid = status["pid"]
        console.print(f"[cyan]Stopping daemon (PID: {pid})...[/cyan]")

        # Send SIGTERM to the daemon
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)

        # Verify it stopped
        status = daemon.get_status()
        if status["running"]:
            console.print("[red]Daemon did not stop gracefully, killing...[/red]")
            os.kill(pid, signal.SIGKILL)
        else:
            console.print("[green]✓ Daemon stopped[/green]")

    except ProcessLookupError:
        console.print("[yellow]Daemon process not found (may have already stopped)[/yellow]")
        # Clean up PID file
        from src.analyzer.scheduler import SchedulerDaemon
        daemon = SchedulerDaemon()
        if daemon.pid_file.exists():
            daemon.pid_file.unlink()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@daemon_app.command("status")
def daemon_status():
    """Show scheduler daemon status."""
    try:
        from src.analyzer.scheduler import SchedulerDaemon

        daemon = SchedulerDaemon()
        status = daemon.get_status()

        console.print("[bold]Scheduler Daemon Status[/bold]\n")

        if status["running"]:
            console.print(f"Status:        [green]RUNNING[/green]")
            console.print(f"PID:           {status['pid']}")
        else:
            console.print(f"Status:        [red]STOPPED[/red]")

        console.print(f"Enabled schedules: {status['schedules_enabled']}")

        if status["running"]:
            console.print(f"\n[dim]View logs: tail -f ~/.website-analyzer/logs/scheduler.log[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@daemon_app.command("logs")
def daemon_logs(
    lines: int = typer.Option(
        50,
        "--lines",
        "-n",
        help="Number of lines to show"
    ),
):
    """View scheduler daemon logs."""
    try:
        log_file = Path.home() / ".website-analyzer" / "logs" / "scheduler.log"

        if not log_file.exists():
            console.print("[yellow]No logs found yet[/yellow]")
            return

        # Read last N lines
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        console.print(f"[bold]Last {len(recent_lines)} log entries:[/bold]\n")
        for line in recent_lines:
            console.print(line.rstrip())

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


# ============================================================================
# NOTIFICATION COMMANDS
# ============================================================================

@notify_app.command("test")
def notify_test(
    event_type: str = typer.Option(
        "scan_completed",
        "--event",
        "-e",
        help="Event type to test: scan_completed, scan_failed, new_bugs_found, bugs_fixed, threshold_alert"
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to notification configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
):
    """Send a test notification to all configured backends.

    Tests your notification configuration by sending sample events.
    Useful for verifying email, Slack, and webhook settings.

    Examples:
        python -m src.analyzer.cli notify test
        python -m src.analyzer.cli notify test --event threshold_alert
        python -m src.analyzer.cli notify test --config notifications.json
    """
    from src.analyzer.notifications import (
        NotificationManager, ScanCompletedEvent, ScanFailedEvent,
        NewBugsFoundEvent, BugsFixedEvent, ThresholdAlertEvent
    )

    try:
        # Load configuration
        config_path = config if config else Path("notifications.json")
        manager = NotificationManager(config_path if config_path.exists() else None)

        if not manager.backends:
            console.print("[yellow]No notification backends configured![/yellow]")
            console.print()
            console.print("To set up notifications:")
            console.print("  1. Copy notifications.example.json to notifications.json")
            console.print("  2. Edit notifications.json with your settings")
            console.print("  3. Set environment variables for credentials (see .env.example)")
            console.print("  4. Run: python -m src.analyzer.cli notify test")
            return

        # Create sample event based on type
        events = {
            "scan_completed": ScanCompletedEvent(
                site_name="example.com",
                site_url="https://example.com",
                scan_id="test_scan_001",
                pages_scanned=150,
                bugs_found=42,
                duration_seconds=125.5,
                output_file="/path/to/results.json",
                report_url="https://example.com/reports/test"
            ),
            "scan_failed": ScanFailedEvent(
                site_name="example.com",
                site_url="https://example.com",
                scan_id="test_scan_002",
                error_message="Connection timeout after 300 seconds",
                error_details="The server stopped responding during page fetch",
                duration_seconds=300.0
            ),
            "new_bugs_found": NewBugsFoundEvent(
                site_name="example.com",
                site_url="https://example.com",
                scan_id="test_scan_003",
                new_bugs_count=15,
                previous_bugs_count=27,
                new_bug_urls=[
                    "https://example.com/page1",
                    "https://example.com/page2",
                    "https://example.com/page3",
                ]
            ),
            "bugs_fixed": BugsFixedEvent(
                site_name="example.com",
                site_url="https://example.com",
                scan_id="test_scan_004",
                fixed_bugs_count=12,
                remaining_bugs_count=15,
                fixed_bug_urls=[
                    "https://example.com/fixed1",
                    "https://example.com/fixed2",
                ]
            ),
            "threshold_alert": ThresholdAlertEvent(
                site_name="example.com",
                site_url="https://example.com",
                scan_id="test_scan_005",
                threshold=50,
                actual_count=127,
                exceeded_by=77,
                severity="critical"
            ),
        }

        event = events.get(event_type)
        if not event:
            console.print(f"[red]Unknown event type: {event_type}[/red]")
            console.print(f"[yellow]Valid types: {', '.join(events.keys())}[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"[bold cyan]Sending test {event_type} notification...[/bold cyan]")
        console.print()

        # Send notification
        async def _send_test():
            return await manager.notify(event)

        results = asyncio.run(_send_test())

        # Display results
        console.print("[bold green]Notification Results:[/bold green]")
        for backend_name, success in results.items():
            status = "[green]✓ SUCCESS[/green]" if success else "[red]✗ FAILED[/red]"
            console.print(f"  {backend_name}: {status}")

        console.print()
        if all(results.values()):
            console.print("[bold green]All notifications sent successfully![/bold green]")
        else:
            failed = [k for k, v in results.items() if not v]
            console.print(f"[yellow]Some backends failed: {', '.join(failed)}[/yellow]")
            console.print("[dim]Check your configuration and environment variables[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@notify_app.command("configure")
def notify_configure(
    output: Path = typer.Option(
        Path("notifications.json"),
        "--output",
        "-o",
        help="Output path for configuration file"
    ),
):
    """Interactive setup wizard for notification configuration.

    Guides you through setting up email, Slack, and webhook notifications.
    Creates a configuration file with your choices.

    Example:
        python -m src.analyzer.cli notify configure
        python -m src.analyzer.cli notify configure --output my-notifications.json
    """
    from src.analyzer.notifications import NotificationConfig

    try:
        console.print("[bold cyan]Bug Finder Notification Configuration Wizard[/bold cyan]")
        console.print()

        # Ask what to configure
        backends_to_setup = []

        console.print("[cyan]Which notification backends would you like to set up?[/cyan]")
        console.print()

        if typer.confirm("Set up Console notifications (for testing)?", default=True):
            backends_to_setup.append("console")

        if typer.confirm("Set up Email notifications?", default=False):
            backends_to_setup.append("email")

        if typer.confirm("Set up Slack notifications?", default=False):
            backends_to_setup.append("slack")

        if typer.confirm("Set up Webhook notifications?", default=False):
            backends_to_setup.append("webhook")

        if not backends_to_setup:
            console.print("[yellow]No backends selected. Exiting.[/yellow]")
            return

        console.print()

        # Create configuration
        config = NotificationConfig()

        # Console is always enabled for testing
        if "console" in backends_to_setup:
            config.add_backend("console", "console", {
                "enabled": True,
                "events": ["scan_completed"]
            })
            console.print("[green]✓ Console backend configured[/green]")

        # Email setup
        if "email" in backends_to_setup:
            console.print()
            console.print("[cyan]Email Configuration[/cyan]")
            console.print("[dim]Leave blank to skip[/dim]")

            backend_name = typer.prompt("Backend name", default="email_production")
            smtp_host = typer.prompt("SMTP Host", default="smtp.gmail.com")
            smtp_port = typer.prompt("SMTP Port", default="587")
            smtp_user = typer.prompt("SMTP User (email address)")
            from_address = typer.prompt("From Address", default=smtp_user)
            to_address = typer.prompt("To Address(es) - comma separated")

            if smtp_user and to_address:
                config.add_backend(backend_name, "email", {
                    "enabled": True,
                    "events": ["scan_completed", "scan_failed", "threshold_alert"],
                    "smtp_host": "${SMTP_HOST}",
                    "smtp_port": int(smtp_port),
                    "smtp_user": "${SMTP_USER}",
                    "smtp_password": "${SMTP_PASSWORD}",
                    "from_address": from_address,
                    "to_addresses": [a.strip() for a in to_address.split(",")],
                    "use_tls": True
                })
                console.print(f"[green]✓ Email backend '{backend_name}' configured[/green]")
                console.print(f"[yellow]⚠ Set environment variables: SMTP_HOST, SMTP_USER, SMTP_PASSWORD[/yellow]")

        # Slack setup
        if "slack" in backends_to_setup:
            console.print()
            console.print("[cyan]Slack Configuration[/cyan]")

            backend_name = typer.prompt("Backend name", default="slack_main")
            console.print("[dim]Go to: https://api.slack.com/messaging/webhooks[/dim]")
            console.print("[dim]Create an Incoming Webhook and paste the URL below[/dim]")
            webhook_url = typer.prompt("Webhook URL")

            if webhook_url:
                config.add_backend(backend_name, "slack", {
                    "enabled": True,
                    "events": ["scan_completed", "new_bugs_found", "bugs_fixed", "threshold_alert"],
                    "webhook_url": "${SLACK_WEBHOOK_URL}"
                })
                console.print(f"[green]✓ Slack backend '{backend_name}' configured[/green]")
                console.print(f"[yellow]⚠ Set environment variable: SLACK_WEBHOOK_URL[/yellow]")

        # Webhook setup
        if "webhook" in backends_to_setup:
            console.print()
            console.print("[cyan]Webhook Configuration[/cyan]")

            backend_name = typer.prompt("Backend name", default="webhook_custom")
            webhook_url = typer.prompt("Webhook URL", default="https://api.example.com/webhooks/bug-finder")

            config.add_backend(backend_name, "webhook", {
                "enabled": True,
                "events": ["scan_completed", "threshold_alert"],
                "webhook_url": webhook_url,
                "headers": {"Authorization": "Bearer ${WEBHOOK_TOKEN}"}
            })
            console.print(f"[green]✓ Webhook backend '{backend_name}' configured[/green]")

        # Save configuration
        config.save(output)

        console.print()
        console.print(f"[bold green]Configuration saved to: {output}[/bold green]")
        console.print()
        console.print("[cyan]Next steps:[/cyan]")
        console.print(f"  1. Review {output} and adjust as needed")
        console.print("  2. Create .env file with credentials (copy from .env.example)")
        console.print("  3. Test notifications: python -m src.analyzer.cli notify test")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@notify_app.command("list-backends")
def notify_list_backends(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to notification configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
):
    """List all configured notification backends.

    Shows which notification backends are available and their status.

    Example:
        python -m src.analyzer.cli notify list-backends
        python -m src.analyzer.cli notify list-backends --config notifications.json
    """
    from src.analyzer.notifications import NotificationManager

    try:
        config_path = config if config else Path("notifications.json")
        manager = NotificationManager(config_path if config_path.exists() else None)

        backends = manager.backends
        if not backends:
            console.print("[yellow]No notification backends configured[/yellow]")
            return

        console.print("[bold cyan]Configured Notification Backends[/bold cyan]")
        console.print()

        table = Table(title="Backends")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Events", style="magenta")

        for name, backend in backends.items():
            backend_type = backend.config.get("type", "unknown")
            status = "[green]ENABLED[/green]" if backend.enabled else "[red]DISABLED[/red]"
            events = ", ".join(backend.supported_events) if backend.supported_events else "All"

            table.add_row(name, backend_type, status, events)

        console.print(table)
        console.print()
        console.print(f"[dim]Total backends: {len(backends)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@notify_app.command("generate-example")
def notify_generate_example(
    output: Path = typer.Option(
        Path("notifications.example.json"),
        "--output",
        "-o",
        help="Output path for example configuration"
    ),
):
    """Generate an example notification configuration file.

    Creates a template with all available notification backends and options.

    Example:
        python -m src.analyzer.cli notify generate-example
    """
    try:
        import shutil

        example_path = Path(__file__).parent.parent.parent / "notifications.example.json"

        if example_path.exists():
            shutil.copy(example_path, output)
            console.print(f"[green]✓ Example config created: {output}[/green]")
            console.print()
            console.print("[cyan]To use this configuration:[/cyan]")
            console.print(f"  1. cp {output} notifications.json")
            console.print("  2. Edit notifications.json with your settings")
            console.print("  3. Set environment variables for credentials")
            console.print("  4. Run: python -m src.analyzer.cli notify test")
        else:
            console.print("[red]Example configuration file not found[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


# ============================================================================
# WEB UI COMMANDS
# ============================================================================

web_app = typer.Typer(
    name="serve",
    help="Launch web-based dashboard for viewing scan results."
)
app.add_typer(web_app)


@web_app.command("start")
def serve_dashboard(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Server host (default: 127.0.0.1)"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Server port (default: 8000)"
    ),
    base_dir: Path = typer.Option(
        Path("."),
        "--base-dir",
        "-d",
        help="Base directory containing projects",
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Don't automatically open browser"
    ),
):
    """
    Launch the web-based Bug Finder Dashboard.

    The dashboard provides:
    - Project overview with recent scans
    - Interactive results viewer (sortable, filterable)
    - Visual bug distribution charts
    - Scan progress monitoring
    - Pattern management UI
    - Export functionality (JSON, CSV, HTML)
    - Dark/light theme toggle

    Features:
    - Real-time updates from CLI scans
    - Detailed filtering and search
    - Multiple export formats
    - Responsive design (works on mobile)

    Examples:

        # Start dashboard on default port (8000)
        python -m src.analyzer.cli serve start

        # Use custom port and host
        python -m src.analyzer.cli serve start --host 0.0.0.0 --port 3000

        # Don't auto-open browser
        python -m src.analyzer.cli serve start --no-browser

        # Specify custom projects directory
        python -m src.analyzer.cli serve start --base-dir /path/to/projects
    """
    try:
        from src.analyzer.web_ui import DashboardServer

        server = DashboardServer(
            host=host,
            port=port,
            base_dir=base_dir,
        )
        server.run(auto_open=not no_browser)

    except ImportError:
        console.print("[red]Error: FastAPI dependencies not installed[/red]")
        console.print()
        console.print("[yellow]To use the web dashboard, install required packages:[/yellow]")
        console.print("  pip install fastapi uvicorn")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"[red]Error starting dashboard: {e}[/red]")
        raise typer.Exit(code=1)


# Main entry point for the CLI
def main():
    app()

if __name__ == "__main__":
    main()