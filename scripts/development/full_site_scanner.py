#!/usr/bin/env python3.11
"""
Comprehensive site-wide scanner for WordPress embed bugs.
Crawls EVERY page on the site and tests for pattern matches.

Supports incremental output mode for long-running scans:
- Results written to .partial.json as they're discovered
- File is always valid JSON with metadata about scan progress
- On completion, .partial.json is renamed to final filename
- On interruption, partial results are still usable
"""

import asyncio
import re
import json
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Generated patterns for WordPress embed bug detection
# Auto-generated from pattern_generator.py - tested and validated
# Confidence: high (75% pattern match rate, 100% bug detection accuracy)
# Key fields detected: fid, view_mode, fields, format, alignment, type, field_deltas
#
# Unicode characters handled:
#   '"' - U+2033 (double prime)
#   Plus: " ' ' " " ' ' (regular and curly quotes)

QUOTE_PATTERN = r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]'

PATTERNS = {
    # Opening structure - most lenient, catches [[ followed by { and fid
    'opening_structure': (
        r'\[\[\s*\{'
    ),

    # Opening with fid field - catches the start of embed code
    'opening_with_field': (
        r'\[\[\s*\{\s*' + QUOTE_PATTERN + r'fid' + QUOTE_PATTERN
    ),

    # Multi-field pattern - requires both fid and view_mode
    # This is our BEST detection pattern (100% accuracy in testing)
    'multi_field': (
        QUOTE_PATTERN + r'fid' + QUOTE_PATTERN + r'[^}]{0,500}' +
        QUOTE_PATTERN + r'view_mode' + QUOTE_PATTERN
    ),

    # Type field - matches the type:media indicator
    'type_field': (
        QUOTE_PATTERN + r'type' + QUOTE_PATTERN +
        r'\s*:\s*' +
        QUOTE_PATTERN + r'media' + QUOTE_PATTERN
    ),

    # Individual field patterns
    'field_fid': (
        QUOTE_PATTERN + r'fid' + QUOTE_PATTERN + r'\s*:\s*' + QUOTE_PATTERN
    ),

    'field_view_mode': (
        QUOTE_PATTERN + r'view_mode' + QUOTE_PATTERN + r'\s*:\s*' + QUOTE_PATTERN
    ),
}

class SiteScanner:
    def __init__(self, start_url, max_pages=1000, incremental=False, output_file=None, quiet=False, verbose=False):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.max_pages = max_pages

        self.visited = set()
        self.to_visit = [start_url]
        self.matches_found = []
        self.failed_urls = []

        # Incremental output support
        self.incremental = incremental
        self.output_file = output_file
        self.partial_file = None

        if self.incremental and self.output_file:
            # Convert output_file to Path and create .partial.json version
            output_path = Path(self.output_file)
            self.partial_file = output_path.with_stem(output_path.stem + '.partial')

        self.scan_start_time = None

        # UI configuration
        self.quiet = quiet
        self.verbose = verbose
        self.console = Console()

        # Configure logging for verbose mode
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        elif quiet:
            logging.basicConfig(level=logging.CRITICAL)
        else:
            logging.basicConfig(level=logging.WARNING)

    def normalize_url(self, url):
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        # Remove fragment, trailing slash, lowercase
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    def _write_incremental_results(self, is_final=False):
        """
        Write current results to a partial JSON file.
        The file is always valid JSON with progress metadata.

        Args:
            is_final: If True, indicates scan is complete
        """
        if not self.incremental or not self.partial_file:
            return

        elapsed_seconds = 0
        if self.scan_start_time:
            elapsed_seconds = (datetime.now() - self.scan_start_time).total_seconds()

        # Build output structure with progress metadata
        output_data = {
            "metadata": {
                "scan_date": datetime.now().isoformat(),
                "start_url": self.start_url,
                "pages_scanned": len(self.visited),
                "pages_queued": len(self.to_visit),
                "max_pages": self.max_pages,
                "bugs_found": len(self.matches_found),
                "failed_urls_count": len(self.failed_urls),
                "elapsed_seconds": elapsed_seconds,
                "scan_complete": is_final,
                "status": "complete" if is_final else "in_progress"
            },
            "results": self.matches_found
        }

        # Write to partial file (atomic-ish - write then move)
        try:
            # Write to temporary file first
            temp_file = self.partial_file.with_stem(self.partial_file.stem + '.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            # Move temp to partial (replace if exists)
            temp_file.replace(self.partial_file)
        except Exception as e:
            if not self.quiet:
                self.console.print(f"[yellow]Warning: Failed to write incremental results: {e}[/yellow]")

    def extract_links_from_html(self, html, current_url):
        """Extract all internal links from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)

            # Only same domain, http/https
            if parsed.netloc == self.base_domain and parsed.scheme in ('http', 'https'):
                # Skip anchors, javascript, mailto, etc
                if not parsed.fragment and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                    normalized = self.normalize_url(full_url)
                    if normalized not in self.visited:
                        links.add(normalized)

        return links

    async def check_page_for_patterns(self, url):
        """Check a single page for bug patterns."""
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url)

                if not result.html:
                    return None, set()

                # Extract links for further crawling
                new_links = self.extract_links_from_html(result.html, url)

                # Check for patterns
                page_matches = {}
                for pattern_name, pattern in PATTERNS.items():
                    matches = list(re.finditer(pattern, result.html, re.IGNORECASE | re.DOTALL))
                    if matches:
                        page_matches[pattern_name] = matches

                if page_matches:
                    # Get sample
                    sample_match = list(page_matches.values())[0][0]
                    context_start = max(0, sample_match.start() - 200)
                    context_end = min(len(result.html), sample_match.end() + 200)
                    context = result.html[context_start:context_end]

                    return {
                        'url': url,
                        'patterns': {k: len(v) for k, v in page_matches.items()},
                        'sample_context': context,
                        'total_matches': sum(len(v) for v in page_matches.values())
                    }, new_links

                return None, new_links

        except Exception as e:
            error_msg = str(e)[:100]
            if self.verbose:
                self.console.print(f"[yellow]Error checking {url}: {error_msg}[/yellow]")
            self.failed_urls.append({'url': url, 'error': error_msg})
            return None, set()

    async def scan(self):
        """Perform comprehensive site scan with rich progress bars."""
        # Show header
        if not self.quiet:
            header = Panel(
                f"[bold cyan]Bug Finder Scanner[/bold cyan]\n"
                f"[cyan]Domain:[/cyan] {self.base_domain}\n"
                f"[cyan]Max Pages:[/cyan] {self.max_pages}\n"
                f"[cyan]Incremental:[/cyan] {'Yes' if self.incremental else 'No'}",
                title="[bold]Starting Scan[/bold]",
                border_style="green"
            )
            self.console.print(header)

        self.scan_start_time = datetime.now()
        pages_checked = 0

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TimeElapsedColumn(),
                console=self.console,
                disable=self.quiet,
            ) as progress:
                scan_task = progress.add_task(
                    "[green]Scanning pages...",
                    total=self.max_pages
                )

                while self.to_visit and pages_checked < self.max_pages:
                    url = self.to_visit.pop(0)

                    if url in self.visited:
                        continue

                    self.visited.add(url)
                    pages_checked += 1

                    # Update progress bar description with current page
                    short_url = url[:60] + "..." if len(url) > 60 else url
                    progress.update(
                        scan_task,
                        description=f"[green]Scanning ({pages_checked}/{self.max_pages}): {short_url}",
                        advance=1
                    )

                    match_result, new_links = await self.check_page_for_patterns(url)

                    if match_result:
                        # Bug found - update task with success color
                        if not self.quiet:
                            self.console.print(
                                f"[bold green]✓ FOUND {match_result['total_matches']} bug(s) on {short_url}[/bold green]"
                            )
                        self.matches_found.append(match_result)
                        # Write incremental results after finding a bug
                        self._write_incremental_results(is_final=False)

                    # Add new links to queue
                    for link in new_links:
                        if link not in self.visited and link not in self.to_visit:
                            self.to_visit.append(link)

                    # Periodic incremental write and stats update
                    if pages_checked % 50 == 0 and self.incremental:
                        self._write_incremental_results(is_final=False)

                # Mark task as complete
                progress.update(scan_task, completed=pages_checked)

        except KeyboardInterrupt:
            # Handle scan interruption gracefully
            if not self.quiet:
                self.console.print(
                    "\n[bold yellow]Scan interrupted by user![/bold yellow]"
                )
            self._write_incremental_results(is_final=False)
            raise

        # Generate and display final report
        self._print_summary(pages_checked)

        # Write final results if in incremental mode
        if self.incremental:
            self._write_incremental_results(is_final=True)
            if self.output_file and self.partial_file:
                # Rename partial to final
                output_path = Path(self.output_file)
                try:
                    self.partial_file.replace(output_path)
                    if not self.quiet:
                        self.console.print(
                            f"[green]✓ Final results saved to: {output_path.name}[/green]"
                        )
                except Exception as e:
                    if not self.quiet:
                        self.console.print(
                            f"[yellow]Warning: Failed to rename to final file: {e}[/yellow]"
                        )
                        self.console.print(
                            f"[cyan]Partial results available at: {self.partial_file.name}[/cyan]"
                        )

        return self.matches_found

    def _print_summary(self, pages_checked):
        """Print a formatted summary of the scan results."""
        if self.quiet:
            return

        elapsed = (datetime.now() - self.scan_start_time).total_seconds()
        minutes = elapsed / 60
        seconds = elapsed % 60
        rate = pages_checked / elapsed if elapsed > 0 else 0

        # Create summary table
        table = Table(title="Scan Summary", show_header=False, box=None)
        table.add_row("[cyan]Pages Scanned[/cyan]", f"[bold]{pages_checked}[/bold]")
        table.add_row("[cyan]Bugs Found[/cyan]", f"[bold red]{len(self.matches_found)}[/bold red]")
        table.add_row("[cyan]Failed URLs[/cyan]", f"[yellow]{len(self.failed_urls)}[/yellow]")
        table.add_row("[cyan]Scan Rate[/cyan]", f"{rate:.1f} pages/sec")
        table.add_row("[cyan]Duration[/cyan]", f"{int(minutes)}m {int(seconds)}s")

        if self.to_visit:
            table.add_row("[cyan]Pages Remaining (Not Scanned)[/cyan]", f"{len(self.to_visit)}")

        summary_panel = Panel(
            table,
            title="[bold green]Scan Complete[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(summary_panel)

        # Show bug statistics if any found
        if self.matches_found:
            self.console.print(
                f"\n[bold]Top affected pages:[/bold]"
            )
            for i, match in enumerate(self.matches_found[:5], 1):
                url_display = match['url'][:70] + "..." if len(match['url']) > 70 else match['url']
                self.console.print(
                    f"  {i}. [link]{url_display}[/link] - {match['total_matches']} match(es)"
                )
            if len(self.matches_found) > 5:
                self.console.print(
                    f"  ... and [bold]{len(self.matches_found) - 5}[/bold] more"
                )

        # Show failed URLs if any
        if self.failed_urls:
            self.console.print(
                f"\n[yellow]Warning: {len(self.failed_urls)} URLs failed to scan[/yellow]"
            )

async def main():
    # Configuration
    START_URL = "https://www.wpr.org"
    MAX_PAGES = 5000  # Adjust as needed - can go up to 10,000+

    # Run scan with progress bars
    scanner = SiteScanner(START_URL, max_pages=MAX_PAGES, incremental=False, quiet=False, verbose=False)
    matches = await scanner.scan()

    # Save detailed results
    if matches:
        # Save to JSON
        output_file = f"bug_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'scan_date': datetime.now().isoformat(),
                'start_url': START_URL,
                'pages_scanned': len(scanner.visited),
                'bugs_found': len(matches),
                'results': matches
            }, f, indent=2)

        console = Console()
        console.print(f"[green]✓ Detailed results saved to: {output_file}[/green]\n")

        # Print summary
        for i, match in enumerate(matches[:20], 1):  # Show first 20
            console.print(f"{i}. {match['url']}")
            console.print(f"   Matches: {match['total_matches']} ({', '.join(f'{k}: {v}' for k, v in match['patterns'].items())})")

            # Show clean sample
            sample = match['sample_context'].replace('\n', ' ').replace('\t', ' ')
            sample = re.sub(r'\s+', ' ', sample)
            console.print(f"   Sample: ...{sample[:150]}...")
            console.print()

        if len(matches) > 20:
            console.print(f"   ... and {len(matches) - 20} more (see {output_file} for full list)\n")

        # Save simple list
        list_file = "affected_urls.txt"
        with open(list_file, 'w') as f:
            f.write(f"WordPress Embed Bug - Affected URLs ({len(matches)} pages)\n")
            f.write(f"Scanned: {datetime.now().isoformat()}\n")
            f.write("="*80 + "\n\n")
            for match in matches:
                f.write(f"{match['url']}\n")
                f.write(f"  Matches: {match['total_matches']}\n\n")

        console.print(f"[green]✓ URL list saved to: {list_file}[/green]")

    else:
        console = Console()
        console.print("\n[bold green]✓ No bugs found across the scanned pages.[/bold green]")
        console.print("   This could mean:")
        console.print("   - The bug has been fixed")
        console.print("   - The bug exists on pages not yet discovered")
        console.print("   - Try increasing MAX_PAGES or different URL patterns")

    # Save failed URLs for debugging
    if scanner.failed_urls:
        failed_file = "failed_urls.txt"
        with open(failed_file, 'w') as f:
            for fail in scanner.failed_urls:
                f.write(f"{fail['url']}\n  Error: {fail['error']}\n\n")
        console.print(f"\n[yellow]Warning: {len(scanner.failed_urls)} URLs failed - see {failed_file}[/yellow]")

if __name__ == "__main__":
    asyncio.run(main())
