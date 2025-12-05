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


# Main entry point for the CLI
def main():
    app()

if __name__ == "__main__":
    main()