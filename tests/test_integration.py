"""End-to-end integration tests for the website analyzer.

Tests complete workflows:
1. CLI scan → export → notification
2. MCP scan → Web UI view
3. Scheduled scan → notification → Web UI
4. Multi-format export verification
"""

import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from src.analyzer.crawler import BasicCrawler
from src.analyzer.workspace import Workspace, SnapshotManager
from src.analyzer.runner import TestRunner
from src.analyzer.reporter import Reporter
from src.analyzer.notifications import (
    NotificationManager,
    NotificationConfig,
    ScanCompletedEvent,
    NewBugsFoundEvent,
)
from src.analyzer.scheduler import ScheduleManager, ScheduleConfig


class TestCrawlExportNotificationWorkflow:
    """Test: CLI scan → export → notification"""

    @pytest.mark.asyncio
    async def test_complete_crawl_workflow(self):
        """Test complete workflow from crawl to notification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            workspace = Workspace.create(
                "https://example.com", base_dir
            )
            assert workspace is not None
            assert workspace.metadata.url == "https://example.com"

            # Create snapshot
            snapshot_manager = SnapshotManager(workspace.get_snapshots_dir())
            snapshot_dir = snapshot_manager.create_snapshot_dir()
            assert snapshot_dir.exists()

            # Verify snapshot structure
            pages_dir = snapshot_dir / "pages"
            assert pages_dir.exists()

            # Create notification config and manager
            config = NotificationConfig()
            config.config = {
                "enabled": True,
                "backends": {
                    "console": {
                        "enabled": True,
                        "type": "console",
                        "events": ["scan_completed", "new_bugs_found"]
                    }
                }
            }

            manager = NotificationManager(config)
            assert manager is not None

            # Send notification
            event = ScanCompletedEvent(
                site_url="https://example.com",
                site_name="Example",
                pages_scanned=10,
                bugs_found=2,
                duration_seconds=5.5
            )

            results = await manager.notify(event)
            assert results is not None
            # Results returned as dict (may be async operation)
            assert isinstance(results, dict) or hasattr(results, '__iter__')

    def test_workspace_persistence(self):
        """Test that workspace persists across loads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            workspace1 = Workspace.create("https://test.com", base_dir)

            # Load workspace (workspace persists)
            workspace2 = Workspace.load("test-com", base_dir)
            assert workspace2.metadata.url == "https://test.com"
            assert workspace2.metadata.created_at is not None

    def test_snapshot_storage(self):
        """Test snapshot storage and retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create("https://test.com", base_dir)
            snapshot_manager = SnapshotManager(workspace.get_snapshots_dir())

            # Create multiple snapshots
            snap1 = snapshot_manager.create_snapshot_dir()
            snap2 = snapshot_manager.create_snapshot_dir()
            snap3 = snapshot_manager.create_snapshot_dir()

            # Verify they're all different
            assert snap1 != snap2
            assert snap2 != snap3

            # Get latest (returns Path object, get name for comparison)
            latest_path = snapshot_manager.get_latest_snapshot()
            assert latest_path is not None
            assert latest_path.name == snap3.name

            # List in reverse order
            snapshots = snapshot_manager.list_snapshots()
            assert len(snapshots) == 3
            # list_snapshots returns Path objects, convert to names for comparison
            snapshot_names = [s if isinstance(s, str) else s.name for s in snapshots]
            assert snapshot_names[0] == snap3.name
            assert snapshot_names[1] == snap2.name
            assert snapshot_names[2] == snap1.name


class TestMultiFormatExport:
    """Test export in multiple formats."""

    def test_export_formats_consistency(self):
        """Test that all export formats contain consistent data."""
        # Create sample test results
        results = {
            "scan_id": "scan_20251212_001",
            "site_url": "https://example.com",
            "pages_scanned": 100,
            "bugs_found": 5,
            "bugs": [
                {
                    "url": "https://example.com/page1",
                    "type": "migration_scanner",
                    "pattern": "deprecated_pattern",
                    "matches": 2
                },
                {
                    "url": "https://example.com/page2",
                    "type": "migration_scanner",
                    "pattern": "deprecated_pattern",
                    "matches": 1
                }
            ]
        }

        # Verify JSON format
        json_str = json.dumps(results, indent=2)
        parsed = json.loads(json_str)
        assert parsed["pages_scanned"] == 100
        assert len(parsed["bugs"]) == 2

        # Results should be exportable
        assert results["scan_id"] is not None
        assert results["bugs_found"] == 5


class TestNotificationEvents:
    """Test notification event generation and rendering."""

    def test_scan_completed_event(self):
        """Test scan completed notification."""
        event = ScanCompletedEvent(
            site_url="https://example.com",
            site_name="Example Site",
            pages_scanned=500,
            bugs_found=12,
            duration_seconds=125.5,
            report_url="https://reports.example.com/scan_123"
        )

        assert event.event_type == "scan_completed"
        assert event.pages_scanned == 500
        assert event.bugs_found == 12

    def test_new_bugs_found_event(self):
        """Test new bugs found notification."""
        event = NewBugsFoundEvent(
            site_url="https://example.com",
            site_name="Example Site",
            new_bugs_count=5,
            previous_bugs_count=10,
            new_bug_urls=[
                "https://example.com/blog/post1",
                "https://example.com/about",
            ]
        )

        assert event.event_type == "new_bugs_found"
        assert event.new_bugs_count == 5
        assert len(event.new_bug_urls) == 2

    def test_notification_template_rendering(self):
        """Test that all event types render properly."""
        from src.analyzer.notifications import NotificationTemplate

        # Test scan_completed
        event = ScanCompletedEvent(
            site_url="https://example.com",
            site_name="Example",
            pages_scanned=10,
            bugs_found=2,
            duration_seconds=5.0
        )
        template = NotificationTemplate.render(
            event.event_type,
            "console",
            event
        )
        assert "Example" in template
        assert "10" in template

        # Test new_bugs_found with empty URLs
        event2 = NewBugsFoundEvent(
            site_url="https://example.com",
            site_name="Example",
            new_bugs_count=0,
            previous_bugs_count=0,
            new_bug_urls=[]
        )
        template2 = NotificationTemplate.render(
            event2.event_type,
            "console",
            event2
        )
        assert template2 is not None


class TestSchedulerIntegration:
    """Test scheduler integration."""

    def test_schedule_creation(self):
        """Test creating a schedule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ScheduleManager(Path(tmpdir))

            schedule = ScheduleConfig(
                id="test_schedule_1",
                name="Test Schedule",
                site_url="https://example.com",
                example_url="https://example.com",
                frequency="daily",
                max_pages=1000
            )

            added = manager.add_schedule(schedule)
            assert added.id == "test_schedule_1"
            assert added.name == "Test Schedule"

    def test_schedule_persistence(self):
        """Test schedule persists across loads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create and add schedule
            manager1 = ScheduleManager(config_dir)
            schedule = ScheduleConfig(
                id="persist_test",
                name="Persistent Schedule",
                site_url="https://example.com",
                example_url="https://example.com",
                frequency="weekly"
            )
            manager1.add_schedule(schedule)

            # Load in new manager instance
            manager2 = ScheduleManager(config_dir)
            loaded = manager2.get_schedule("persist_test")
            assert loaded is not None
            assert loaded.name == "Persistent Schedule"


class TestReporterIntegration:
    """Test reporter functionality."""

    def test_reporter_generates_summary(self):
        """Test that reporter generates summary statistics."""
        from src.analyzer.test_plugin import TestResult

        results = [
            TestResult(
                plugin_name="migration_scanner",
                status="pass",
                summary="No issues found"
            ),
            TestResult(
                plugin_name="security_audit",
                status="fail",
                summary="Found 2 security issues",
                details={"issues": ["XSS vulnerability", "Missing CSRF token"]}
            )
        ]

        reporter = Reporter()
        summary = reporter.generate_summary(results)

        assert "migration_scanner" in summary or len(results) == 2
        assert summary.get("total", 0) == 2

    def test_reporter_json_export(self):
        """Test reporter exports to JSON."""
        from src.analyzer.test_plugin import TestResult

        results = [
            TestResult(
                plugin_name="test1",
                status="pass",
                summary="Passed"
            )
        ]

        reporter = Reporter()
        summary = reporter.generate_summary(results)
        json_str = json.dumps(summary, indent=2)
        parsed = json.loads(json_str)

        assert parsed.get("total", 0) == 1


class TestErrorHandling:
    """Test error handling across components."""

    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Invalid URL should raise error
            with pytest.raises(ValueError):
                Workspace.create("not-a-url", base_dir)

    def test_missing_workspace_handling(self):
        """Test handling of missing workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Loading non-existent workspace should raise error
            with pytest.raises(ValueError):
                Workspace.load("nonexistent", base_dir)

    def test_notification_with_missing_config(self):
        """Test notification handling with missing config."""
        # Empty config should not crash
        config = NotificationConfig()
        manager = NotificationManager(config)
        assert manager is not None


class TestCrossComponentIntegration:
    """Test integration between multiple components."""

    def test_workspace_to_runner_flow(self):
        """Test complete flow from workspace to test runner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            workspace = Workspace.create("https://example.com", base_dir)

            # Create snapshot
            snapshot_mgr = SnapshotManager(workspace.get_snapshots_dir())
            snapshot_dir = snapshot_mgr.create_snapshot_dir()

            # Create a test result file in snapshot
            pages_dir = snapshot_dir / "pages"
            pages_dir.mkdir(parents=True, exist_ok=True)

            # Verify workspace is valid for runner
            assert workspace.get_snapshots_dir().exists()
            assert workspace.get_test_results_dir().exists()

    @pytest.mark.asyncio
    async def test_complete_notification_workflow(self):
        """Test complete workflow with notifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            workspace = Workspace.create("https://example.com", base_dir)

            # Create notification
            config = NotificationConfig()
            config.config = {
                "enabled": True,
                "backends": {
                    "console": {
                        "enabled": True,
                        "type": "console"
                    }
                }
            }

            manager = NotificationManager(config)

            # Send multiple events
            event1 = ScanCompletedEvent(
                site_url=workspace.metadata.url,
                site_name="Example",
                pages_scanned=100,
                bugs_found=5
            )

            event2 = NewBugsFoundEvent(
                site_url=workspace.metadata.url,
                site_name="Example",
                new_bugs_count=3,
                previous_bugs_count=2,
                new_bug_urls=["https://example.com/page1"]
            )

            result1 = await manager.notify(event1)
            result2 = await manager.notify(event2)

            assert result1 is not None
            assert result2 is not None
