"""
Bug Finder Web UI Server

FastAPI-based web server for viewing and managing bug-finder scan results.
Provides REST API and HTML dashboard interface.
"""

import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import platform
import subprocess
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

from src.analyzer.web_ui.api import ScanAPI, ProjectAPI


# Pydantic models for API responses
class ScanSummary(BaseModel):
    id: str
    site_url: str
    status: str
    created_at: str
    bug_count: int
    pages_scanned: int


class ProjectOverview(BaseModel):
    slug: str
    url: str
    created_at: str
    last_crawl: Optional[str]
    last_scan: Optional[str]


class ScanDetail(BaseModel):
    id: str
    site_url: str
    example_url: str
    status: str
    created_at: str
    completed_at: Optional[str]
    bugs_found: List[Dict[str, Any]]
    metadata: Dict[str, Any]


def create_app(base_dir: Path = Path("."), debug: bool = False) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        base_dir: Base directory containing projects
        debug: Enable debug mode

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Bug Finder Dashboard",
        description="Web UI for viewing and managing bug-finder scan results",
        version="1.0.0",
    )

    # Initialize APIs
    scan_api = ScanAPI(base_dir)
    project_api = ProjectAPI(base_dir)

    # Get paths for static files
    web_ui_dir = Path(__file__).parent
    static_dir = web_ui_dir / "static"
    templates_dir = web_ui_dir / "templates"

    # Mount static files
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # ============================================================================
    # HTML Pages
    # ============================================================================

    @app.get("/", response_class=HTMLResponse)
    async def home():
        """Home page: Project overview with recent scans."""
        index_file = templates_dir / "index.html"
        if index_file.exists():
            return index_file.read_text()
        return _get_default_home_html()

    @app.get("/project/{slug}", response_class=HTMLResponse)
    async def project_detail(slug: str):
        """Project detail page: Scan history and results."""
        project_file = templates_dir / "project.html"
        if project_file.exists():
            return project_file.read_text()
        return _get_default_project_html(slug)

    @app.get("/scan/{scan_id}", response_class=HTMLResponse)
    async def scan_detail(scan_id: str):
        """Scan results page: Detailed bug list with filtering."""
        results_file = templates_dir / "results.html"
        if results_file.exists():
            return results_file.read_text()
        return _get_default_results_html(scan_id)

    @app.get("/patterns", response_class=HTMLResponse)
    async def patterns_page():
        """Patterns page: Browse and test patterns."""
        patterns_file = templates_dir / "patterns.html"
        if patterns_file.exists():
            return patterns_file.read_text()
        return _get_default_patterns_html()

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page():
        """Settings page: Configuration management."""
        settings_file = templates_dir / "settings.html"
        if settings_file.exists():
            return settings_file.read_text()
        return _get_default_settings_html()

    # ============================================================================
    # API Endpoints
    # ============================================================================

    # Projects
    @app.get("/api/projects")
    async def get_projects():
        """List all projects."""
        return {"projects": project_api.list_projects()}

    @app.get("/api/projects/{slug}")
    async def get_project(slug: str):
        """Get project details."""
        project = project_api.get_project(slug)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    # Scans
    @app.get("/api/scans")
    async def get_scans(
        limit: int = Query(50, le=500),
        status: Optional[str] = None,
        project_slug: Optional[str] = None,
    ):
        """List scans with optional filtering."""
        scans = scan_api.list_scans(
            limit=limit,
            status=status,
            project_slug=project_slug,
        )
        return {"scans": scans, "total": len(scans)}

    @app.get("/api/scans/{scan_id}")
    async def get_scan(scan_id: str):
        """Get scan details."""
        scan = scan_api.get_scan(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scan

    @app.get("/api/scans/{scan_id}/results")
    async def get_scan_results(
        scan_id: str,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        sort_by: str = Query("matches", regex="^(matches|url|status)$"),
        sort_order: str = Query("desc", regex="^(asc|desc)$"),
    ):
        """Get paginated scan results with filtering."""
        results = scan_api.get_scan_results(
            scan_id,
            page=page,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        if results is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        return results

    @app.get("/api/scans/{scan_id}/stats")
    async def get_scan_stats(scan_id: str):
        """Get scan statistics for charts."""
        stats = scan_api.get_scan_stats(scan_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Scan not found")
        return stats

    # Patterns
    @app.get("/api/patterns")
    async def get_patterns():
        """List available patterns."""
        from src.analyzer.pattern_library import PatternLibrary
        try:
            library = PatternLibrary()
            patterns = library.list_patterns()
            return {"patterns": patterns}
        except Exception as e:
            return {"patterns": [], "error": str(e)}

    @app.get("/api/patterns/{pattern_name}")
    async def get_pattern(pattern_name: str):
        """Get pattern details."""
        from src.analyzer.pattern_library import PatternLibrary
        try:
            library = PatternLibrary()
            pattern = library.load_pattern_by_name(pattern_name)
            if not pattern:
                raise HTTPException(status_code=404, detail="Pattern not found")
            return pattern.model_dump() if hasattr(pattern, 'model_dump') else pattern.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Exports
    @app.get("/api/scans/{scan_id}/export")
    async def export_scan(
        scan_id: str,
        format: str = Query("json", regex="^(json|csv|html)$"),
    ):
        """Export scan results in specified format."""
        export_path = scan_api.export_scan(scan_id, format)
        if not export_path or not Path(export_path).exists():
            raise HTTPException(status_code=404, detail="Could not generate export")

        return FileResponse(
            path=export_path,
            filename=f"scan_{scan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
        )

    # Status/Health
    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "base_dir": str(base_dir),
        }

    return app


def _get_default_home_html() -> str:
    """Return default home page HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bug Finder Dashboard</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Bug Finder Dashboard</h1>
                <div class="theme-toggle">
                    <button id="theme-btn">🌙</button>
                </div>
            </header>

            <nav class="nav">
                <a href="/" class="nav-link active">Projects</a>
                <a href="/patterns" class="nav-link">Patterns</a>
                <a href="/settings" class="nav-link">Settings</a>
            </nav>

            <main class="main">
                <section class="section">
                    <h2>Recent Scans</h2>
                    <div id="scans-list" class="scans-grid">
                        <div class="loading">Loading scans...</div>
                    </div>
                </section>

                <section class="section">
                    <h2>Projects</h2>
                    <div id="projects-list" class="projects-list">
                        <div class="loading">Loading projects...</div>
                    </div>
                </section>
            </main>
        </div>

        <script src="/static/js/app.js"></script>
        <script src="/static/js/home.js"></script>
    </body>
    </html>
    """


def _get_default_project_html(slug: str) -> str:
    """Return default project page HTML."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Project: {slug}</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Project: {slug}</h1>
                <div class="theme-toggle">
                    <button id="theme-btn">🌙</button>
                </div>
            </header>

            <nav class="nav">
                <a href="/" class="nav-link">Projects</a>
                <a href="/patterns" class="nav-link">Patterns</a>
                <a href="/settings" class="nav-link">Settings</a>
            </nav>

            <main class="main">
                <section class="section">
                    <h2>Project Details</h2>
                    <div id="project-info" class="info-box">
                        <div class="loading">Loading project...</div>
                    </div>
                </section>

                <section class="section">
                    <h2>Scan History</h2>
                    <div id="scan-history" class="scans-table">
                        <div class="loading">Loading scan history...</div>
                    </div>
                </section>
            </main>
        </div>

        <script src="/static/js/app.js"></script>
        <script>
            const projectSlug = '{slug}';
            // Load project details
            document.addEventListener('DOMContentLoaded', async () => {{
                await loadProjectDetails(projectSlug);
                await loadProjectScans(projectSlug);
            }});

            async function loadProjectDetails(slug) {{
                const response = await fetch(`/api/projects/${{slug}}`);
                if (!response.ok) return;
                const project = await response.json();
                const info = document.getElementById('project-info');
                info.innerHTML = `
                    <p><strong>URL:</strong> ${{project.url}}</p>
                    <p><strong>Created:</strong> ${{new Date(project.created_at).toLocaleString()}}</p>
                    ${{project.last_crawl ? `<p><strong>Last Crawl:</strong> ${{project.last_crawl}}</p>` : ''}}
                    ${{project.last_scan ? `<p><strong>Last Scan:</strong> ${{project.last_scan}}</p>` : ''}}
                `;
            }}

            async function loadProjectScans(slug) {{
                const response = await fetch(`/api/scans?project_slug=${{slug}}&limit=20`);
                if (!response.ok) return;
                const data = await response.json();
                const history = document.getElementById('scan-history');

                if (data.scans.length === 0) {{
                    history.innerHTML = '<p>No scans yet</p>';
                    return;
                }}

                let html = '<table class="results-table"><thead><tr><th>Date</th><th>Status</th><th>Bugs</th><th>Pages</th><th>Action</th></tr></thead><tbody>';
                for (const scan of data.scans) {{
                    html += `<tr>
                        <td>${{new Date(scan.created_at).toLocaleString()}}</td>
                        <td><span class="status-badge status-${{scan.status}}">${{scan.status}}</span></td>
                        <td>${{scan.bug_count}}</td>
                        <td>${{scan.pages_scanned}}</td>
                        <td><a href="/scan/${{scan.id}}" class="btn-link">View</a></td>
                    </tr>`;
                }}
                html += '</tbody></table>';
                history.innerHTML = html;
            }}
        </script>
    </body>
    </html>
    """


def _get_default_results_html(scan_id: str) -> str:
    """Return default results page HTML."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scan Results: {scan_id[:20]}</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Scan Results</h1>
                <div class="theme-toggle">
                    <button id="theme-btn">🌙</button>
                </div>
            </header>

            <nav class="nav">
                <a href="/" class="nav-link">Projects</a>
                <a href="/patterns" class="nav-link">Patterns</a>
                <a href="/settings" class="nav-link">Settings</a>
            </nav>

            <main class="main">
                <div class="controls">
                    <input type="text" id="search-box" placeholder="Search URLs..." class="search-box">
                    <select id="sort-select" class="sort-select">
                        <option value="matches-desc">Most Matches</option>
                        <option value="matches-asc">Fewest Matches</option>
                        <option value="url-asc">URL (A-Z)</option>
                        <option value="url-desc">URL (Z-A)</option>
                    </select>
                    <button id="export-btn" class="btn btn-primary">Export</button>
                </div>

                <section class="section">
                    <h2>Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="stat-bugs">-</div>
                            <div class="stat-label">Total Bugs</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="stat-pages">-</div>
                            <div class="stat-label">Pages Affected</div>
                        </div>
                        <div class="stat-card">
                            <div class="chart-container" style="max-height: 200px;">
                                <canvas id="distribution-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="section">
                    <h2>Results</h2>
                    <div id="results-container" class="results-container">
                        <div class="loading">Loading results...</div>
                    </div>
                    <div class="pagination">
                        <button id="prev-btn" class="btn">Previous</button>
                        <span id="page-info"></span>
                        <button id="next-btn" class="btn">Next</button>
                    </div>
                </section>
            </main>
        </div>

        <script src="/static/js/app.js"></script>
        <script src="/static/js/results.js"></script>
        <script>
            const scanId = '{scan_id}';
            let currentPage = 1;
            let currentSort = 'matches-desc';
            let currentSearch = '';
            let distributionChart = null;

            document.addEventListener('DOMContentLoaded', async () => {{
                await loadResults();
                await loadStats();
                setupEventListeners();
            }});

            async function loadResults(page = 1) {{
                const [sort, order] = currentSort.split('-');
                const response = await fetch(`/api/scans/${{scanId}}/results?page=${{page}}&search=${{currentSearch}}&sort_by=${{sort}}&sort_order=${{order}}`);
                if (!response.ok) return;
                const data = await response.json();
                currentPage = page;

                renderResults(data.results);
                updatePagination(data.page, data.pages);
            }}

            function renderResults(results) {{
                const container = document.getElementById('results-container');
                if (results.length === 0) {{
                    container.innerHTML = '<p>No results found</p>';
                    return;
                }}

                let html = '<table class="results-table"><thead><tr><th>URL</th><th>Matches</th><th>Status</th></tr></thead><tbody>';
                for (const result of results) {{
                    html += `<tr>
                        <td><a href="${{result.url}}" target="_blank">${{result.url}}</a></td>
                        <td>${{result.total_matches}}</td>
                        <td><span class="status-badge">Match</span></td>
                    </tr>`;
                }}
                html += '</tbody></table>';
                container.innerHTML = html;
            }}

            async function loadStats() {{
                const response = await fetch(`/api/scans/${{scanId}}/stats`);
                if (!response.ok) return;
                const stats = await response.json();

                document.getElementById('stat-bugs').textContent = stats.total_bugs;
                document.getElementById('stat-pages').textContent = stats.pages_count;

                // Chart
                const ctx = document.getElementById('distribution-chart');
                if (ctx && stats.distribution) {{
                    if (distributionChart) distributionChart.destroy();
                    distributionChart = new Chart(ctx, {{
                        type: 'doughnut',
                        data: {{
                            labels: stats.distribution.labels,
                            datasets: [{{
                                data: stats.distribution.data,
                                backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    position: 'bottom'
                                }}
                            }}
                        }}
                    }});
                }}
            }}

            function setupEventListeners() {{
                document.getElementById('search-box').addEventListener('input', (e) => {{
                    currentSearch = e.target.value;
                    loadResults(1);
                }});

                document.getElementById('sort-select').addEventListener('change', (e) => {{
                    currentSort = e.target.value;
                    loadResults(1);
                }});

                document.getElementById('export-btn').addEventListener('click', () => {{
                    window.location.href = `/api/scans/${{scanId}}/export?format=json`;
                }});

                document.getElementById('prev-btn').addEventListener('click', () => {{
                    if (currentPage > 1) loadResults(currentPage - 1);
                }});

                document.getElementById('next-btn').addEventListener('click', () => {{
                    loadResults(currentPage + 1);
                }});
            }}

            function updatePagination(page, pages) {{
                document.getElementById('page-info').textContent = `Page ${{page}} of ${{pages}}`;
                document.getElementById('prev-btn').disabled = page === 1;
                document.getElementById('next-btn').disabled = page === pages;
            }}
        </script>
    </body>
    </html>
    """


def _get_default_patterns_html() -> str:
    """Return default patterns page HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pattern Management</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Pattern Management</h1>
                <div class="theme-toggle">
                    <button id="theme-btn">🌙</button>
                </div>
            </header>

            <nav class="nav">
                <a href="/" class="nav-link">Projects</a>
                <a href="/patterns" class="nav-link active">Patterns</a>
                <a href="/settings" class="nav-link">Settings</a>
            </nav>

            <main class="main">
                <section class="section">
                    <h2>Available Patterns</h2>
                    <div id="patterns-list" class="patterns-grid">
                        <div class="loading">Loading patterns...</div>
                    </div>
                </section>

                <section class="section">
                    <h2>Test Pattern</h2>
                    <div class="form-group">
                        <label for="pattern-select">Pattern:</label>
                        <select id="pattern-select"></select>
                    </div>
                    <div class="form-group">
                        <label for="test-content">Content to Test:</label>
                        <textarea id="test-content" rows="5" placeholder="Enter HTML or text content..."></textarea>
                    </div>
                    <button id="test-btn" class="btn btn-primary">Test Pattern</button>
                    <div id="test-results" style="margin-top: 20px;"></div>
                </section>
            </main>
        </div>

        <script src="/static/js/app.js"></script>
        <script src="/static/js/patterns.js"></script>
    </body>
    </html>
    """


def _get_default_settings_html() -> str:
    """Return default settings page HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Settings</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Settings</h1>
                <div class="theme-toggle">
                    <button id="theme-btn">🌙</button>
                </div>
            </header>

            <nav class="nav">
                <a href="/" class="nav-link">Projects</a>
                <a href="/patterns" class="nav-link">Patterns</a>
                <a href="/settings" class="nav-link active">Settings</a>
            </nav>

            <main class="main">
                <section class="section">
                    <h2>Application Settings</h2>

                    <div class="settings-group">
                        <h3>Display</h3>
                        <div class="setting-item">
                            <label for="theme-setting">Theme:</label>
                            <select id="theme-setting">
                                <option value="light">Light</option>
                                <option value="dark">Dark</option>
                                <option value="auto">Auto</option>
                            </select>
                        </div>
                        <div class="setting-item">
                            <label for="items-per-page">Items Per Page:</label>
                            <input type="number" id="items-per-page" min="5" max="100" value="20">
                        </div>
                    </div>

                    <div class="settings-group">
                        <h3>Scan Defaults</h3>
                        <div class="setting-item">
                            <label for="max-pages">Default Max Pages:</label>
                            <input type="number" id="max-pages" min="10" max="10000" value="1000">
                        </div>
                        <div class="setting-item">
                            <label for="timeout">Request Timeout (seconds):</label>
                            <input type="number" id="timeout" min="5" max="300" value="30">
                        </div>
                    </div>

                    <button id="save-settings" class="btn btn-primary">Save Settings</button>
                    <div id="settings-message" style="margin-top: 10px;"></div>
                </section>

                <section class="section">
                    <h2>System Information</h2>
                    <div id="system-info"></div>
                </section>
            </main>
        </div>

        <script src="/static/js/app.js"></script>
        <script src="/static/js/settings.js"></script>
    </body>
    </html>
    """


class DashboardServer:
    """Manages the web dashboard server lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000, base_dir: Path = Path(".")):
        """Initialize server.

        Args:
            host: Server host
            port: Server port
            base_dir: Base directory for projects
        """
        self.host = host
        self.port = port
        self.base_dir = base_dir
        self.app = create_app(base_dir)
        self.url = f"http://{host}:{port}"

    def run(self, auto_open: bool = True):
        """Run the server.

        Args:
            auto_open: Whether to automatically open browser
        """
        if auto_open:
            # Open browser after server starts
            def open_browser():
                asyncio.sleep(1)  # Give server time to start
                webbrowser.open(self.url)

            # Start browser opening in background
            import threading
            threading.Thread(target=lambda: open_browser(), daemon=True).start()

        print(f"\n🚀 Bug Finder Dashboard")
        print(f"   URL: {self.url}")
        print(f"   Host: {self.host}")
        print(f"   Port: {self.port}")
        print(f"   Base Dir: {self.base_dir}")
        print("\nPress Ctrl+C to stop the server\n")

        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bug Finder Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--base-dir", type=Path, default=Path("."), help="Base directory for projects")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")

    args = parser.parse_args()

    server = DashboardServer(
        host=args.host,
        port=args.port,
        base_dir=args.base_dir,
    )
    server.run(auto_open=not args.no_browser)
