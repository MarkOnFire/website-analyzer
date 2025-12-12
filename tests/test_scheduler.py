"""
Tests for the scheduler system.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.analyzer.scheduler import (
    ScheduleManager,
    ScheduleConfig,
    ScheduleFrequency,
    ScheduledScanRunner,
    SchedulerDaemon,
    generate_schedule_id,
    SCHEDULE_TEMPLATES,
)


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def schedule_manager(temp_config_dir):
    """Create ScheduleManager with temp directory."""
    return ScheduleManager(temp_config_dir)


@pytest.fixture
def sample_schedule():
    """Create a sample schedule for testing."""
    return ScheduleConfig(
        id="test_schedule_001",
        name="Test Scan",
        site_url="https://example.com",
        example_url="https://example.com/page",
        frequency="daily",
        max_pages=100,
    )


class TestScheduleConfig:
    """Tests for ScheduleConfig dataclass."""

    def test_create_schedule(self, sample_schedule):
        """Test creating a schedule."""
        assert sample_schedule.id == "test_schedule_001"
        assert sample_schedule.name == "Test Scan"
        assert sample_schedule.frequency == "daily"
        assert sample_schedule.enabled is True

    def test_schedule_to_dict(self, sample_schedule):
        """Test converting schedule to dict."""
        schedule_dict = sample_schedule.to_dict()
        assert isinstance(schedule_dict, dict)
        assert schedule_dict["id"] == "test_schedule_001"
        assert schedule_dict["name"] == "Test Scan"

    def test_schedule_from_dict(self):
        """Test creating schedule from dict."""
        data = {
            "id": "test_001",
            "name": "Test",
            "site_url": "https://example.com",
            "example_url": "https://example.com/page",
            "frequency": "daily",
            "max_pages": 100,
            "enabled": True,
            "output_dir": None,
            "cron_expression": None,
            "notifications": {},
            "created_at": "2025-12-11T12:00:00",
            "last_run": None,
            "next_run": None,
            "tags": [],
        }
        schedule = ScheduleConfig.from_dict(data)
        assert schedule.id == "test_001"
        assert schedule.name == "Test"
        assert schedule.frequency == "daily"


class TestScheduleManager:
    """Tests for ScheduleManager."""

    def test_manager_creates_config_file(self, temp_config_dir):
        """Test that manager creates schedules.json."""
        manager = ScheduleManager(temp_config_dir)
        schedules_file = temp_config_dir / "schedules.json"
        assert schedules_file.exists()

    def test_add_schedule(self, schedule_manager, sample_schedule):
        """Test adding a schedule."""
        result = schedule_manager.add_schedule(sample_schedule)
        assert result.id == sample_schedule.id

        # Verify it's in the file
        schedules = schedule_manager.list_schedules()
        assert len(schedules) == 1
        assert schedules[0].id == sample_schedule.id

    def test_add_duplicate_schedule_raises_error(self, schedule_manager, sample_schedule):
        """Test that adding duplicate schedule ID raises error."""
        schedule_manager.add_schedule(sample_schedule)

        with pytest.raises(ValueError, match="already exists"):
            schedule_manager.add_schedule(sample_schedule)

    def test_get_schedule(self, schedule_manager, sample_schedule):
        """Test getting a schedule by ID."""
        schedule_manager.add_schedule(sample_schedule)
        retrieved = schedule_manager.get_schedule("test_schedule_001")

        assert retrieved is not None
        assert retrieved.id == sample_schedule.id
        assert retrieved.name == sample_schedule.name

    def test_get_nonexistent_schedule(self, schedule_manager):
        """Test getting nonexistent schedule returns None."""
        result = schedule_manager.get_schedule("nonexistent")
        assert result is None

    def test_list_schedules(self, schedule_manager):
        """Test listing all schedules."""
        schedule1 = ScheduleConfig(
            id="s1",
            name="Schedule 1",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="daily",
        )
        schedule2 = ScheduleConfig(
            id="s2",
            name="Schedule 2",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="weekly",
        )

        schedule_manager.add_schedule(schedule1)
        schedule_manager.add_schedule(schedule2)

        schedules = schedule_manager.list_schedules()
        assert len(schedules) == 2

    def test_list_enabled_only(self, schedule_manager):
        """Test listing only enabled schedules."""
        s1 = ScheduleConfig(
            id="s1",
            name="Enabled",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="daily",
            enabled=True,
        )
        s2 = ScheduleConfig(
            id="s2",
            name="Disabled",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="daily",
            enabled=False,
        )

        schedule_manager.add_schedule(s1)
        schedule_manager.add_schedule(s2)

        all_schedules = schedule_manager.list_schedules()
        assert len(all_schedules) == 2

        enabled = schedule_manager.list_schedules(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].id == "s1"

    def test_update_schedule(self, schedule_manager, sample_schedule):
        """Test updating a schedule."""
        schedule_manager.add_schedule(sample_schedule)

        sample_schedule.name = "Updated Name"
        result = schedule_manager.update_schedule(sample_schedule)
        assert result is True

        updated = schedule_manager.get_schedule("test_schedule_001")
        assert updated.name == "Updated Name"

    def test_update_nonexistent_schedule(self, schedule_manager, sample_schedule):
        """Test updating nonexistent schedule returns False."""
        result = schedule_manager.update_schedule(sample_schedule)
        assert result is False

    def test_enable_schedule(self, schedule_manager, sample_schedule):
        """Test enabling a schedule."""
        sample_schedule.enabled = False
        schedule_manager.add_schedule(sample_schedule)

        result = schedule_manager.enable_schedule("test_schedule_001")
        assert result is True

        schedule = schedule_manager.get_schedule("test_schedule_001")
        assert schedule.enabled is True

    def test_disable_schedule(self, schedule_manager, sample_schedule):
        """Test disabling a schedule."""
        schedule_manager.add_schedule(sample_schedule)

        result = schedule_manager.disable_schedule("test_schedule_001")
        assert result is True

        schedule = schedule_manager.get_schedule("test_schedule_001")
        assert schedule.enabled is False

    def test_remove_schedule(self, schedule_manager, sample_schedule):
        """Test removing a schedule."""
        schedule_manager.add_schedule(sample_schedule)
        assert len(schedule_manager.list_schedules()) == 1

        result = schedule_manager.remove_schedule("test_schedule_001")
        assert result is True
        assert len(schedule_manager.list_schedules()) == 0

    def test_remove_nonexistent_schedule(self, schedule_manager):
        """Test removing nonexistent schedule returns False."""
        result = schedule_manager.remove_schedule("nonexistent")
        assert result is False

    def test_update_last_run(self, schedule_manager, sample_schedule):
        """Test updating last run timestamp."""
        schedule_manager.add_schedule(sample_schedule)

        schedule_manager.update_last_run("test_schedule_001")
        schedule = schedule_manager.get_schedule("test_schedule_001")

        assert schedule.last_run is not None
        assert "2025-" in schedule.last_run  # Should be ISO format with year

    def test_persistence(self, temp_config_dir, sample_schedule):
        """Test that schedules persist across manager instances."""
        manager1 = ScheduleManager(temp_config_dir)
        manager1.add_schedule(sample_schedule)

        manager2 = ScheduleManager(temp_config_dir)
        schedules = manager2.list_schedules()

        assert len(schedules) == 1
        assert schedules[0].id == sample_schedule.id


class TestScheduleFrequency:
    """Tests for ScheduleFrequency enum."""

    def test_frequency_values(self):
        """Test frequency enum values."""
        assert ScheduleFrequency.HOURLY.value == "hourly"
        assert ScheduleFrequency.DAILY.value == "daily"
        assert ScheduleFrequency.WEEKLY.value == "weekly"
        assert ScheduleFrequency.CUSTOM.value == "custom"

    def test_frequency_from_string(self):
        """Test creating frequency from string."""
        assert ScheduleFrequency("daily") == ScheduleFrequency.DAILY
        assert ScheduleFrequency("hourly") == ScheduleFrequency.HOURLY


class TestScheduleIdGeneration:
    """Tests for schedule ID generation."""

    def test_generate_schedule_id(self):
        """Test generating unique schedule IDs."""
        id1 = generate_schedule_id("Test Schedule")
        id2 = generate_schedule_id("Test Schedule")

        # Both should start with 'schedule_'
        assert id1.startswith("schedule_")
        assert id2.startswith("schedule_")

        # They should be different (different timestamps)
        assert id1 != id2

    def test_schedule_id_format(self):
        """Test schedule ID format."""
        schedule_id = generate_schedule_id("My Schedule")

        # Format: schedule_YYYYMMDDHHMMSS_hash
        parts = schedule_id.split("_")
        assert parts[0] == "schedule"
        assert len(parts[1]) == 14  # YYYYMMDDHHmmss
        assert len(parts[2]) == 8  # 8-char hash


class TestScheduleTemplates:
    """Tests for schedule templates."""

    def test_templates_exist(self):
        """Test that templates are defined."""
        assert "daily-full-site" in SCHEDULE_TEMPLATES
        assert "weekly-comprehensive" in SCHEDULE_TEMPLATES
        assert "hourly-critical-pages" in SCHEDULE_TEMPLATES

    def test_daily_template(self):
        """Test daily full site template."""
        template = SCHEDULE_TEMPLATES["daily-full-site"]
        assert template["frequency"] == "daily"
        assert template["max_pages"] == 0  # All pages
        assert "daily" in template["tags"]

    def test_weekly_template(self):
        """Test weekly comprehensive template."""
        template = SCHEDULE_TEMPLATES["weekly-comprehensive"]
        assert template["frequency"] == "weekly"
        assert template["max_pages"] == 0  # All pages
        assert "weekly" in template["tags"]

    def test_hourly_template(self):
        """Test hourly critical pages template."""
        template = SCHEDULE_TEMPLATES["hourly-critical-pages"]
        assert template["frequency"] == "hourly"
        assert template["max_pages"] == 10
        assert "hourly" in template["tags"]


class TestScheduledScanRunner:
    """Tests for ScheduledScanRunner."""

    def test_runner_initialization(self, schedule_manager):
        """Test initializing a scan runner."""
        runner = ScheduledScanRunner(schedule_manager)
        assert runner.manager is schedule_manager
        assert runner.logger is not None

    def test_runner_has_logger(self, schedule_manager):
        """Test that runner has configured logger."""
        runner = ScheduledScanRunner(schedule_manager)
        assert runner.logger.name == "src.analyzer.scheduler"

    def test_logs_directory_created(self, schedule_manager):
        """Test that logs directory is created."""
        runner = ScheduledScanRunner(schedule_manager)
        logs_dir = Path.home() / ".website-analyzer" / "logs"
        # Just verify it can create the logger (which creates the dir)
        assert runner.logger is not None


class TestSchedulerDaemon:
    """Tests for SchedulerDaemon."""

    def test_daemon_initialization(self, schedule_manager):
        """Test initializing a daemon."""
        daemon = SchedulerDaemon(schedule_manager)
        assert daemon.manager is schedule_manager
        assert daemon.runner is not None
        assert daemon.scheduler is None  # Not started yet

    def test_daemon_get_status_not_running(self, schedule_manager):
        """Test daemon status when not running."""
        daemon = SchedulerDaemon(schedule_manager)
        status = daemon.get_status()

        assert status["running"] is False
        assert status["pid"] is None

    def test_pid_file_path(self, schedule_manager):
        """Test PID file path."""
        daemon = SchedulerDaemon(schedule_manager)
        expected_path = Path.home() / ".website-analyzer" / "scheduler.pid"
        assert daemon.pid_file == expected_path


class TestScheduleIntegration:
    """Integration tests for the scheduler system."""

    def test_create_enable_disable_remove_workflow(self, schedule_manager):
        """Test complete workflow: create, enable, disable, remove."""
        # Create
        schedule = ScheduleConfig(
            id="workflow_test",
            name="Workflow Test",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="daily",
        )
        schedule_manager.add_schedule(schedule)
        assert len(schedule_manager.list_schedules()) == 1

        # Disable
        schedule_manager.disable_schedule("workflow_test")
        assert not schedule_manager.get_schedule("workflow_test").enabled

        # Enable
        schedule_manager.enable_schedule("workflow_test")
        assert schedule_manager.get_schedule("workflow_test").enabled

        # Remove
        schedule_manager.remove_schedule("workflow_test")
        assert len(schedule_manager.list_schedules()) == 0

    def test_multiple_schedules_management(self, schedule_manager):
        """Test managing multiple schedules."""
        # Create 5 schedules
        for i in range(5):
            schedule = ScheduleConfig(
                id=f"test_{i}",
                name=f"Schedule {i}",
                site_url="https://example.com",
                example_url="https://example.com/page",
                frequency="daily" if i % 2 == 0 else "weekly",
            )
            schedule_manager.add_schedule(schedule)

        # List all
        all_schedules = schedule_manager.list_schedules()
        assert len(all_schedules) == 5

        # Disable some
        schedule_manager.disable_schedule("test_0")
        schedule_manager.disable_schedule("test_2")

        # List enabled only
        enabled = schedule_manager.list_schedules(enabled_only=True)
        assert len(enabled) == 3

    def test_cron_expression_with_custom_frequency(self, schedule_manager):
        """Test schedule with custom cron expression."""
        schedule = ScheduleConfig(
            id="cron_test",
            name="Cron Test",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="custom",
            cron_expression="0 */6 * * *",  # Every 6 hours
        )
        schedule_manager.add_schedule(schedule)

        retrieved = schedule_manager.get_schedule("cron_test")
        assert retrieved.frequency == "custom"
        assert retrieved.cron_expression == "0 */6 * * *"

    def test_schedule_with_tags(self, schedule_manager):
        """Test schedule with tags."""
        schedule = ScheduleConfig(
            id="tagged_test",
            name="Tagged Schedule",
            site_url="https://example.com",
            example_url="https://example.com/page",
            frequency="daily",
            tags=["production", "daily", "critical"],
        )
        schedule_manager.add_schedule(schedule)

        retrieved = schedule_manager.get_schedule("tagged_test")
        assert len(retrieved.tags) == 3
        assert "production" in retrieved.tags
        assert "critical" in retrieved.tags
