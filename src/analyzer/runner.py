"""Test runner orchestration.

Manages the execution of analysis plugins against project snapshots.
"""

import asyncio
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.analyzer.plugin_loader import load_plugins
from src.analyzer.test_plugin import SiteSnapshot, TestResult
from src.analyzer.workspace import SnapshotManager, Workspace


class TestRunner:
    """Orchestrates test execution."""

    DEFAULT_TIMEOUT_SECONDS = 300 # Default timeout for individual plugin execution

    def __init__(self, base_dir: Path):
        """Initialize runner.

        Args:
            base_dir: Base directory containing the 'projects' folder.
        """
        self.base_dir = base_dir

    def save_results(self, workspace: Workspace, results: List[TestResult]) -> Path:
        """Save test results to the workspace.

        Creates a timestamped JSON file in the project's test-results directory.

        Args:
            workspace: Project workspace.
            results: List of TestResult objects to save.

        Returns:
            Path to the saved results file.
        """
        timestamp = SnapshotManager.create_timestamp()
        filename = f"results_{timestamp}.json"
        output_path = workspace.get_test_results_dir() / filename

        data = [r.model_dump() for r in results]
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
        return output_path

    async def run(
        self, 
        slug: str, 
        test_names: Optional[List[str]] = None,
        snapshot_timestamp: Optional[str] = None,
        save: bool = True,
        config: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300
    ) -> List[TestResult]:
        """Run tests on a project snapshot.

        Args:
            slug: Project slug to analyze.
            test_names: Optional list of plugin names to run. If None, runs all.
            snapshot_timestamp: Optional specific snapshot to analyze. 
                                If None, uses latest.
            save: Whether to save results to disk (default True).
            config: Configuration dictionary. 
                    Format: {"plugin_name": {"key": "value"}}
            timeout_seconds: Maximum execution time per plugin in seconds.

        Returns:
            List of TestResult objects.

        Raises:
            ValueError: If project/snapshot not found or no tests match.
        """
        # Load workspace
        workspace = Workspace.load(slug, self.base_dir)
        
        # Determine snapshot directory
        snap_manager = SnapshotManager(workspace.get_snapshots_dir())
        
        if snapshot_timestamp:
            snapshot_dir = workspace.get_snapshots_dir() / snapshot_timestamp
            if not snapshot_dir.exists():
                raise ValueError(f"Snapshot not found: {snapshot_timestamp}")
        else:
            snapshot_dir = snap_manager.get_latest_snapshot()
            if not snapshot_dir:
                raise ValueError(f"No snapshots found for project {slug}")
            
        # Load snapshot data
        try:
            snapshot = SiteSnapshot.load(snapshot_dir)
        except Exception as e:
            raise ValueError(f"Failed to load snapshot: {e}")
        
        # Load plugins
        all_plugins = load_plugins()
        
        # Filter plugins
        plugins_to_run = []
        found_names = set()
        
        if test_names:
            wanted = set(test_names)
            for plugin in all_plugins:
                if plugin.name in wanted:
                    plugins_to_run.append(plugin)
                    found_names.add(plugin.name)
            
            missing = wanted - found_names
            if missing:
                # We could warn or raise. For now, let's raise if NOTHING matches, 
                # but maybe just log missing ones? 
                # User asked for specific tests, so probably expects them.
                if not plugins_to_run:
                     raise ValueError(f"No matching tests found for: {missing}")
        else:
            plugins_to_run = all_plugins
            
        if not plugins_to_run:
            return []

        # Execute tests
        results: List[TestResult] = []
        
        for plugin in plugins_to_run:
            try:
                # Extract config for this plugin
                plugin_config = (config or {}).get(plugin.name, {})
                
                # Run with timeout
                result = await asyncio.wait_for(
                    plugin.analyze(snapshot, **plugin_config), 
                    timeout=timeout_seconds
                )
                results.append(result)
                
            except asyncio.TimeoutError:
                results.append(TestResult(
                    plugin_name=plugin.name,
                    status="error",
                    summary=f"Test timed out after {timeout_seconds}s",
                    details={"timeout_seconds": timeout_seconds}
                ))
                
            except Exception as e:
                # Fallback error result with traceback
                results.append(TestResult(
                    plugin_name=plugin.name,
                    status="error",
                    summary=f"Unhandled exception: {str(e)}",
                    details={
                        "error": str(e), 
                        "type": type(e).__name__,
                        "traceback": traceback.format_exc()
                    }
                ))
                
        if save and results:
            self.save_results(workspace, results)

        return results
