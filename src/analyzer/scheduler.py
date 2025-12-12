"""
Scheduler for recurring scans with cron-style scheduling.

Features:
- Cron-style schedule definitions (hourly, daily, weekly, custom)
- Schedule management (add, remove, list, enable/disable)
- Background daemon for running scheduled scans
- Persistent schedule storage (JSON config file)
"""

import json
import logging
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import time
import signal
import uuid


# Try to import APScheduler, fall back to cron if needed
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


class ScheduleFrequency(str, Enum):
    """Frequency options for scheduling."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled scan."""
    id: str
    name: str
    site_url: str
    example_url: str
    frequency: str  # "hourly", "daily", "weekly", or cron expression
    max_pages: int = 1000
    enabled: bool = True
    output_dir: Optional[str] = None
    cron_expression: Optional[str] = None  # For custom cron
    notifications: Dict[str, Any] = field(default_factory=dict)  # For future use
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScheduleConfig":
        """Create from dictionary."""
        return ScheduleConfig(**data)


class ScheduleManager:
    """Manage schedule storage and retrieval."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize schedule manager.

        Args:
            config_dir: Directory to store schedules.json. Defaults to ~/.website-analyzer/
        """
        if config_dir is None:
            config_dir = Path.home() / ".website-analyzer"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.schedules_file = self.config_dir / "schedules.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure schedules.json exists."""
        if not self.schedules_file.exists():
            self.schedules_file.write_text(json.dumps({"schedules": []}, indent=2))

    def add_schedule(self, schedule: ScheduleConfig) -> ScheduleConfig:
        """Add a new schedule."""
        data = json.loads(self.schedules_file.read_text())

        # Check if schedule ID already exists
        if any(s["id"] == schedule.id for s in data["schedules"]):
            raise ValueError(f"Schedule with ID '{schedule.id}' already exists")

        data["schedules"].append(schedule.to_dict())
        self.schedules_file.write_text(json.dumps(data, indent=2))
        return schedule

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule by ID."""
        data = json.loads(self.schedules_file.read_text())
        original_len = len(data["schedules"])
        data["schedules"] = [s for s in data["schedules"] if s["id"] != schedule_id]

        if len(data["schedules"]) < original_len:
            self.schedules_file.write_text(json.dumps(data, indent=2))
            return True
        return False

    def get_schedule(self, schedule_id: str) -> Optional[ScheduleConfig]:
        """Get a schedule by ID."""
        data = json.loads(self.schedules_file.read_text())

        for s in data["schedules"]:
            if s["id"] == schedule_id:
                return ScheduleConfig.from_dict(s)
        return None

    def list_schedules(self, enabled_only: bool = False) -> List[ScheduleConfig]:
        """List all schedules."""
        data = json.loads(self.schedules_file.read_text())
        schedules = [ScheduleConfig.from_dict(s) for s in data["schedules"]]

        if enabled_only:
            schedules = [s for s in schedules if s.enabled]

        return schedules

    def update_schedule(self, schedule: ScheduleConfig) -> bool:
        """Update a schedule."""
        data = json.loads(self.schedules_file.read_text())

        for i, s in enumerate(data["schedules"]):
            if s["id"] == schedule.id:
                data["schedules"][i] = schedule.to_dict()
                self.schedules_file.write_text(json.dumps(data, indent=2))
                return True
        return False

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = True
            return self.update_schedule(schedule)
        return False

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = False
            return self.update_schedule(schedule)
        return False

    def update_last_run(self, schedule_id: str, timestamp: Optional[str] = None):
        """Update last run timestamp."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            schedule.last_run = timestamp or datetime.now().isoformat()
            self.update_schedule(schedule)


class ScheduledScanRunner:
    """Execute scheduled scans."""

    def __init__(self, schedule_manager: Optional[ScheduleManager] = None):
        """
        Initialize scan runner.

        Args:
            schedule_manager: ScheduleManager instance. Creates new if None.
        """
        self.manager = schedule_manager or ScheduleManager()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Create logs directory
        logs_dir = Path.home() / ".website-analyzer" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        handler = logging.FileHandler(logs_dir / "scheduler.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    async def run_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Run a scheduled scan immediately.

        Returns:
            Dict with execution results
        """
        schedule = self.manager.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule '{schedule_id}' not found")

        if not schedule.enabled:
            raise ValueError(f"Schedule '{schedule_id}' is disabled")

        self.logger.info(f"Starting scheduled scan: {schedule.name}")

        try:
            # Import here to avoid circular imports
            from src.analyzer.crawler import BasicCrawler
            from src.analyzer.runner import TestRunner
            from src.analyzer.workspace import Workspace

            # Create or get workspace
            ws = Workspace.get_or_create(schedule.site_url)

            # Create crawler and run
            crawler = BasicCrawler(
                start_url=schedule.site_url,
                max_pages=schedule.max_pages
            )

            pages = await crawler.crawl()
            self.logger.info(f"Crawled {len(pages)} pages for {schedule.name}")

            # Update schedule metadata
            self.manager.update_last_run(schedule_id)

            return {
                "success": True,
                "schedule_id": schedule_id,
                "schedule_name": schedule.name,
                "pages_crawled": len(pages),
                "timestamp": datetime.now().isoformat(),
                "output_dir": schedule.output_dir or str(ws.project_dir)
            }

        except Exception as e:
            self.logger.error(f"Error running schedule {schedule_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "schedule_id": schedule_id,
                "schedule_name": schedule.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_schedule_sync(self, schedule_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for run_schedule."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_schedule(schedule_id))
        finally:
            loop.close()


class SchedulerDaemon:
    """Background daemon for running scheduled scans."""

    def __init__(self, schedule_manager: Optional[ScheduleManager] = None):
        """
        Initialize scheduler daemon.

        Args:
            schedule_manager: ScheduleManager instance. Creates new if None.
        """
        self.manager = schedule_manager or ScheduleManager()
        self.runner = ScheduledScanRunner(self.manager)
        self.logger = self.runner.logger
        self.scheduler = None
        self.pid_file = Path.home() / ".website-analyzer" / "scheduler.pid"

    def _setup_scheduler(self):
        """Set up APScheduler."""
        if not HAS_APSCHEDULER:
            raise RuntimeError(
                "APScheduler is required for daemon functionality. "
                "Install with: pip install apscheduler"
            )

        self.scheduler = BackgroundScheduler()

        # Add all enabled schedules
        for schedule in self.manager.list_schedules(enabled_only=True):
            self._add_job(schedule)

    def _add_job(self, schedule: ScheduleConfig):
        """Add a job to the scheduler."""
        if not self.scheduler:
            return

        try:
            if schedule.frequency == ScheduleFrequency.HOURLY.value:
                trigger = CronTrigger(minute=0)
            elif schedule.frequency == ScheduleFrequency.DAILY.value:
                trigger = CronTrigger(hour=0, minute=0)
            elif schedule.frequency == ScheduleFrequency.WEEKLY.value:
                trigger = CronTrigger(day_of_week=0, hour=0, minute=0)  # Monday
            elif schedule.frequency == ScheduleFrequency.CUSTOM.value:
                if not schedule.cron_expression:
                    self.logger.warning(f"No cron expression for schedule {schedule.id}")
                    return
                trigger = CronTrigger.from_crontab(schedule.cron_expression)
            else:
                self.logger.warning(f"Unknown frequency: {schedule.frequency}")
                return

            self.scheduler.add_job(
                self.runner.run_schedule_sync,
                trigger=trigger,
                args=[schedule.id],
                id=schedule.id,
                name=schedule.name,
                replace_existing=True
            )
            self.logger.info(f"Added job: {schedule.name} ({schedule.id})")

        except Exception as e:
            self.logger.error(f"Failed to add job {schedule.id}: {str(e)}")

    def start(self):
        """Start the daemon."""
        if self.scheduler is not None:
            self.logger.warning("Scheduler already running")
            return

        self._setup_scheduler()

        # Write PID file
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))

        self.logger.info("Scheduler daemon starting")
        self.scheduler.start()

        # Handle shutdown gracefully
        def signal_handler(sig, frame):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep daemon running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the daemon."""
        if self.scheduler:
            self.logger.info("Scheduler daemon stopping")
            self.scheduler.shutdown()
            self.scheduler = None

            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                # Check if process exists
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
                return {
                    "running": True,
                    "pid": pid,
                    "schedules_enabled": len(self.manager.list_schedules(enabled_only=True))
                }
            except (ValueError, ProcessLookupError, OSError):
                # PID file is stale
                self.pid_file.unlink()

        return {
            "running": False,
            "pid": None,
            "schedules_enabled": len(self.manager.list_schedules(enabled_only=True))
        }

    def reload_schedules(self):
        """Reload schedules (useful when config changes)."""
        if self.scheduler:
            # Remove all existing jobs
            for job in self.scheduler.get_jobs():
                job.remove()

            # Re-add all enabled schedules
            for schedule in self.manager.list_schedules(enabled_only=True):
                self._add_job(schedule)

            self.logger.info("Schedules reloaded")


def generate_schedule_id(name: str) -> str:
    """Generate a unique schedule ID from name."""
    import hashlib
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # Use first 8 chars of UUID for true uniqueness
    unique_suffix = str(uuid.uuid4()).replace("-", "")[:8]
    name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
    return f"schedule_{timestamp}_{unique_suffix}"


# Example schedule templates
SCHEDULE_TEMPLATES = {
    "daily-full-site": {
        "name": "Daily Full Site Scan",
        "frequency": ScheduleFrequency.DAILY.value,
        "max_pages": 0,  # 0 means scan all pages
        "cron_expression": "0 2 * * *",  # 2 AM daily
        "tags": ["full-site", "daily"],
    },
    "weekly-comprehensive": {
        "name": "Weekly Comprehensive Scan",
        "frequency": ScheduleFrequency.WEEKLY.value,
        "max_pages": 0,  # 0 means scan all pages
        "cron_expression": "0 3 ? * MON",  # Monday 3 AM
        "tags": ["full-site", "weekly"],
    },
    "hourly-critical-pages": {
        "name": "Hourly Critical Pages Check",
        "frequency": ScheduleFrequency.HOURLY.value,
        "max_pages": 10,  # Just critical pages
        "cron_expression": "0 * * * *",  # Every hour
        "tags": ["critical", "hourly"],
    },
}
