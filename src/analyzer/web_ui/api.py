"""
Bug Finder Web UI API

Handles data retrieval and processing for the web dashboard.
Interfaces with scan results, projects, and patterns.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import csv
import io


@dataclass
class ScanData:
    """Scan data structure."""
    id: str
    site_url: str
    example_url: Optional[str]
    status: str
    created_at: str
    completed_at: Optional[str]
    bug_count: int
    pages_scanned: int
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ScanAPI:
    """API for accessing scan data."""

    SCAN_REGISTRY = Path.home() / ".bug-finder" / "scans.json"

    def __init__(self, base_dir: Path = Path(".")):
        """Initialize API.

        Args:
            base_dir: Base directory for projects
        """
        self.base_dir = Path(base_dir)

    def _load_registry(self) -> Dict[str, Any]:
        """Load scan registry."""
        if not self.SCAN_REGISTRY.exists():
            return {"scans": []}
        try:
            return json.loads(self.SCAN_REGISTRY.read_text())
        except Exception:
            return {"scans": []}

    def _load_scan_results(self, output_file: str) -> tuple[List[Dict], Dict]:
        """Load scan results from file.

        Args:
            output_file: Path to results file (without extension)

        Returns:
            Tuple of (results, metadata)
        """
        # Try loading JSON results
        json_path = Path(f"{output_file}.json")
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text())
                return data.get("results", []), data.get("metadata", {})
            except Exception:
                pass

        # Try loading partial results
        partial_path = Path(f"{output_file}.partial.json")
        if partial_path.exists():
            try:
                data = json.loads(partial_path.read_text())
                return data.get("results", []), data.get("metadata", {})
            except Exception:
                pass

        return [], {}

    def list_scans(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        project_slug: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List scans with filtering.

        Args:
            limit: Maximum number of scans
            status: Filter by status
            project_slug: Filter by project slug

        Returns:
            List of scan summaries
        """
        registry = self._load_registry()
        scans = registry.get("scans", [])

        # Filter by status
        if status:
            scans = [s for s in scans if s.get("status") == status]

        # Filter by project slug (extract from site URL)
        if project_slug:
            scans = [
                s for s in scans
                if self._extract_slug_from_url(s.get("site_url", "")) == project_slug
            ]

        # Sort by date (newest first)
        scans = sorted(scans, key=lambda x: x.get("started_at", ""), reverse=True)

        # Add bug count if available
        result = []
        for scan in scans[:limit]:
            scan_copy = dict(scan)
            if scan.get("output_file"):
                results, _ = self._load_scan_results(scan["output_file"])
                scan_copy["bug_count"] = len(results)
            else:
                scan_copy["bug_count"] = 0
            scan_copy["created_at"] = scan.get("started_at", "")
            result.append(scan_copy)

        return result

    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan details.

        Args:
            scan_id: Scan ID

        Returns:
            Scan details or None
        """
        registry = self._load_registry()
        for scan in registry.get("scans", []):
            if scan.get("id") == scan_id:
                result = dict(scan)
                if scan.get("output_file"):
                    results, metadata = self._load_scan_results(scan["output_file"])
                    result["results"] = results
                    result["metadata"] = metadata
                    result["bug_count"] = len(results)
                else:
                    result["results"] = []
                    result["metadata"] = {}
                    result["bug_count"] = 0
                result["created_at"] = scan.get("started_at", "")
                return result
        return None

    def get_scan_results(
        self,
        scan_id: str,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        sort_by: str = "matches",
        sort_order: str = "desc",
    ) -> Optional[Dict[str, Any]]:
        """Get paginated scan results.

        Args:
            scan_id: Scan ID
            page: Page number
            per_page: Results per page
            search: Search term for URL filtering
            sort_by: Sort field (matches, url, status)
            sort_order: Sort order (asc, desc)

        Returns:
            Paginated results or None
        """
        scan = self.get_scan(scan_id)
        if not scan:
            return None

        results = scan.get("results", [])

        # Filter by search
        if search:
            search_lower = search.lower()
            results = [r for r in results if search_lower in r.get("url", "").lower()]

        # Sort
        sort_key = {
            "matches": lambda r: r.get("total_matches", 0),
            "url": lambda r: r.get("url", "").lower(),
            "status": lambda r: r.get("status", ""),
        }.get(sort_by, lambda r: r.get("total_matches", 0))

        results = sorted(results, key=sort_key, reverse=(sort_order == "desc"))

        # Paginate
        total = len(results)
        pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated = results[start:end]

        return {
            "results": paginated,
            "page": page,
            "pages": pages,
            "total": total,
            "per_page": per_page,
        }

    def get_scan_stats(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan statistics for charts.

        Args:
            scan_id: Scan ID

        Returns:
            Statistics or None
        """
        scan = self.get_scan(scan_id)
        if not scan:
            return None

        results = scan.get("results", [])

        # Calculate statistics
        total_bugs = sum(r.get("total_matches", 0) for r in results)
        pages_count = len(results)

        # Distribution by match count
        distribution = {}
        for result in results:
            matches = result.get("total_matches", 0)
            key = f"{matches} matches"
            distribution[key] = distribution.get(key, 0) + 1

        return {
            "total_bugs": total_bugs,
            "pages_count": pages_count,
            "avg_bugs_per_page": total_bugs / pages_count if pages_count > 0 else 0,
            "distribution": {
                "labels": list(distribution.keys()),
                "data": list(distribution.values()),
            },
        }

    def export_scan(self, scan_id: str, format: str = "json") -> Optional[str]:
        """Export scan results.

        Args:
            scan_id: Scan ID
            format: Export format (json, csv, html)

        Returns:
            Path to exported file or None
        """
        scan = self.get_scan(scan_id)
        if not scan:
            return None

        results = scan.get("results", [])
        export_dir = Path(".") / "exports"
        export_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"scan_{scan_id[:16]}_{timestamp}"

        try:
            if format == "json":
                export_path = export_file.with_suffix(".json")
                data = {
                    "scan_id": scan_id,
                    "exported_at": datetime.now().isoformat(),
                    "results": results,
                    "metadata": scan.get("metadata", {}),
                }
                export_path.write_text(json.dumps(data, indent=2))
                return str(export_path)

            elif format == "csv":
                export_path = export_file.with_suffix(".csv")
                with open(export_path, "w", newline="", encoding="utf-8") as f:
                    if results:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=results[0].keys(),
                        )
                        writer.writeheader()
                        writer.writerows(results)
                return str(export_path)

            elif format == "html":
                export_path = export_file.with_suffix(".html")
                html = self._generate_html_export(scan, results)
                export_path.write_text(html)
                return str(export_path)

        except Exception:
            return None

        return None

    def _generate_html_export(
        self,
        scan: Dict[str, Any],
        results: List[Dict[str, Any]],
    ) -> str:
        """Generate HTML export.

        Args:
            scan: Scan data
            results: Results list

        Returns:
            HTML string
        """
        total_bugs = sum(r.get("total_matches", 0) for r in results)

        rows = "".join(
            f"""
            <tr>
                <td><a href="{r.get('url', '')}" target="_blank">{r.get('url', '')}</a></td>
                <td>{r.get('total_matches', 0)}</td>
                <td>Match</td>
            </tr>
            """
            for r in results[:100]  # Limit to 100 for HTML export
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Scan Results Export</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                h1 {{ color: #333; }}
                .metadata {{ background: white; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; background: white; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Bug Finder Scan Results</h1>
            <div class="metadata">
                <p><strong>Scan ID:</strong> {scan.get('id', 'N/A')}</p>
                <p><strong>Site:</strong> {scan.get('site_url', 'N/A')}</p>
                <p><strong>Status:</strong> {scan.get('status', 'N/A')}</p>
                <p><strong>Total Bugs Found:</strong> {total_bugs}</p>
                <p><strong>Pages Affected:</strong> {len(results)}</p>
                <p><strong>Exported:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <h2>Results ({len(results)} pages)</h2>
            <table>
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Match Count</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """

    @staticmethod
    def _extract_slug_from_url(url: str) -> str:
        """Extract project slug from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "").replace(".", "-")


class ProjectAPI:
    """API for accessing project data."""

    def __init__(self, base_dir: Path = Path(".")):
        """Initialize API.

        Args:
            base_dir: Base directory for projects
        """
        self.base_dir = Path(base_dir)

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects.

        Returns:
            List of project summaries
        """
        projects_dir = self.base_dir / "projects"
        if not projects_dir.exists():
            return []

        projects = []
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Try to load project metadata
            metadata_file = project_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                    projects.append({
                        "slug": metadata.get("slug", project_dir.name),
                        "url": metadata.get("url", ""),
                        "created_at": metadata.get("created_at", ""),
                        "last_crawl": metadata.get("last_crawl"),
                        "last_scan": self._get_last_scan(project_dir),
                    })
                except Exception:
                    pass

        return sorted(projects, key=lambda p: p.get("created_at", ""), reverse=True)

    def get_project(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get project details.

        Args:
            slug: Project slug

        Returns:
            Project details or None
        """
        projects_dir = self.base_dir / "projects"
        project_dir = projects_dir / slug

        if not project_dir.exists():
            return None

        metadata_file = project_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            metadata = json.loads(metadata_file.read_text())
            return {
                "slug": slug,
                "url": metadata.get("url", ""),
                "created_at": metadata.get("created_at", ""),
                "last_crawl": metadata.get("last_crawl"),
                "last_scan": self._get_last_scan(project_dir),
            }
        except Exception:
            return None

    def _get_last_scan(self, project_dir: Path) -> Optional[str]:
        """Get last scan timestamp.

        Args:
            project_dir: Project directory

        Returns:
            Last scan timestamp or None
        """
        scan_registry = Path.home() / ".bug-finder" / "scans.json"
        if not scan_registry.exists():
            return None

        try:
            data = json.loads(scan_registry.read_text())
            # Find scans for this project
            project_slug = project_dir.name
            for scan in sorted(data.get("scans", []), key=lambda x: x.get("started_at", ""), reverse=True):
                # Check if scan matches this project
                if project_slug in scan.get("site_url", ""):
                    return scan.get("started_at")
        except Exception:
            pass

        return None
