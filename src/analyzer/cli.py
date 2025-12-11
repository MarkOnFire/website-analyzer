import asyncio
import json
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.console import Console

from src.analyzer.workspace import Workspace, ProjectMetadata, slugify_url, SnapshotManager
from src.analyzer.crawler import BasicCrawler
from src.analyzer.runner import TestRunner
from src.analyzer.test_plugin import TestResult # For type hinting, not directly used here
from src.analyzer.config import ConfigLoader, ConfigMerger, create_example_config
from bug_finder_export import export_results, export_to_html, export_to_json, export_to_csv
from bug_finder_export_markdown import export_to_markdown, export_to_slack_snippet
from datetime import datetime


console = Console()

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
    # Define the async function separately
    async def _run_crawl_async():
        workspace = Workspace.load(slug, base_dir)
        target_url = url if url else workspace.metadata.url
        if not target_url:
            console.print(f"[red]Error: Project '[cyan]{slug}[/cyan]' has no URL specified and none provided.[/red]")
            raise typer.Exit(code=1)

        console.print(f"[bold green]Starting crawl for project '[cyan]{slug}[/cyan]' ([link]{target_url}[/link])...")

        # Initialize crawler with CLI-provided max_pages and max_depth
        crawler = BasicCrawler(max_pages=max_pages, max_depth=max_depth)
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
        cli = BugFinderCLI()

        # Load configuration file if provided
        effective_config = {
            'max_pages': max_pages,
            'format': format,
        }

        if config:
            try:
                console.print(f"[cyan]Loading config from: {config}[/cyan]")
                config_obj = ConfigLoader.load(config)
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
            console.print("[red]Error: --example-url is required[/red]")
            raise typer.Exit(code=1)

        if not site_to_scan:
            console.print("[red]Error: --site is required[/red]")
            raise typer.Exit(code=1)

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
                }

                # Export results in specified format
                export_results(matches, output_file, metadata, format=effective_config['format'])

                # Show what was saved
                if effective_config['format'] == 'all':
                    console.print(f"\n[green]Results saved in all formats:[/green]")
                    console.print(f"  - {output_file}.txt")
                    console.print(f"  - {output_file}.csv")
                    console.print(f"  - {output_file}.html")
                    console.print(f"  - {output_file}.json")
                else:
                    ext = '.txt' if effective_config['format'] == 'txt' else f".{effective_config['format']}"
                    console.print(f"\n[green]Full results saved to: {output_file}{ext}[/green]")
            else:
                console.print("\n[bold green]No bugs found![/bold green]")
                console.print("The site appears clean or bugs are on unscanned pages.")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
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


# Main entry point for the CLI
def main():
    app()

if __name__ == "__main__":
    main()