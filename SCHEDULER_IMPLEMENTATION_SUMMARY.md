# Scheduler Implementation Summary

## Overview

A comprehensive scheduling and automation system has been implemented for recurring scans. The system supports:

- **Cron-style scheduling** (hourly, daily, weekly, custom)
- **Background daemon** for automatic execution
- **Persistent storage** in `~/.website-analyzer/schedules.json`
- **Complete CLI** for schedule management
- **System integration** (systemd/launchd)
- **Comprehensive logging** and monitoring

## Files Created

### Core Implementation

| File | Purpose |
|------|---------|
| `src/analyzer/scheduler.py` | Main scheduler module (600+ lines) |
| `src/analyzer/cli.py` | Added schedule and daemon CLI commands |
| `src/analyzer/website-analyzer-scheduler.service` | systemd service file |
| `src/analyzer/com.website-analyzer.scheduler.plist` | macOS launchd agent |

### Documentation

| File | Purpose |
|------|---------|
| `SCHEDULER_GUIDE.md` | Comprehensive guide (500+ lines) |
| `SCHEDULER_QUICK_START.md` | 5-minute quick start |
| `SCHEDULER_COMMAND_REFERENCE.md` | Complete command reference |
| `SCHEDULER_DEPLOYMENT.md` | Deployment guide (Docker, K8s, systemd, launchd) |
| `SCHEDULER_IMPLEMENTATION_SUMMARY.md` | This file |
| `example_schedules.json` | Example schedule configuration |

### Testing

| File | Purpose |
|------|---------|
| `tests/test_scheduler.py` | Comprehensive test suite (500+ lines) |

## Key Classes and Components

### ScheduleConfig

Data class for schedule configuration:

```python
@dataclass
class ScheduleConfig:
    id: str                              # Unique schedule identifier
    name: str                            # Human-readable name
    site_url: str                        # URL to scan
    example_url: str                     # Example URL with bug
    frequency: str                       # hourly/daily/weekly/custom
    max_pages: int = 1000                # Pages to scan
    enabled: bool = True                 # Enable/disable state
    output_dir: Optional[str] = None     # Output location
    cron_expression: Optional[str] = None # Custom cron
    notifications: Dict[str, Any] = {}   # Future: notifications
    created_at: str                      # ISO timestamp
    last_run: Optional[str] = None       # ISO timestamp
    next_run: Optional[str] = None       # ISO timestamp
    tags: List[str] = []                 # Organization tags
```

### ScheduleManager

Manages schedule persistence:

```python
class ScheduleManager:
    def add_schedule(schedule: ScheduleConfig) -> ScheduleConfig
    def remove_schedule(schedule_id: str) -> bool
    def get_schedule(schedule_id: str) -> Optional[ScheduleConfig]
    def list_schedules(enabled_only: bool = False) -> List[ScheduleConfig]
    def update_schedule(schedule: ScheduleConfig) -> bool
    def enable_schedule(schedule_id: str) -> bool
    def disable_schedule(schedule_id: str) -> bool
    def update_last_run(schedule_id: str, timestamp: Optional[str] = None)
```

### ScheduledScanRunner

Executes scheduled scans:

```python
class ScheduledScanRunner:
    async def run_schedule(schedule_id: str) -> Dict[str, Any]
    def run_schedule_sync(schedule_id: str) -> Dict[str, Any]
```

### SchedulerDaemon

Long-running background process:

```python
class SchedulerDaemon:
    def start()                          # Start daemon
    def stop()                           # Stop daemon
    def get_status() -> Dict[str, Any]  # Get status
    def reload_schedules()              # Reload from disk
```

## CLI Commands

### Schedule Management

```bash
bug-finder schedule add <name> --site <url> --example <url> [options]
bug-finder schedule list [--enabled]
bug-finder schedule show <schedule_id>
bug-finder schedule enable <schedule_id>
bug-finder schedule disable <schedule_id>
bug-finder schedule remove <schedule_id> [--yes]
bug-finder schedule run <schedule_id>
```

### Daemon Control

```bash
bug-finder daemon start [--no-background]
bug-finder daemon stop
bug-finder daemon status
bug-finder daemon logs [--lines <n>]
```

## Data Storage

### Schedule File

Location: `~/.website-analyzer/schedules.json`

Structure:
```json
{
  "schedules": [
    {
      "id": "schedule_20251211120000_a1b2c3d4",
      "name": "Daily Full Site Scan",
      "site_url": "https://www.example.com",
      "example_url": "https://www.example.com/page",
      "frequency": "daily",
      "max_pages": 0,
      "enabled": true,
      "output_dir": "/path/to/output",
      "cron_expression": "0 2 * * *",
      "notifications": {},
      "created_at": "2025-12-11T12:00:00",
      "last_run": null,
      "next_run": "2025-12-12T02:00:00",
      "tags": ["production", "daily"]
    }
  ]
}
```

### Logs

Location: `~/.website-analyzer/logs/scheduler.log`

Format:
```
2025-12-11 14:30:00,123 - INFO - Starting scheduled scan: Daily Full Scan
2025-12-11 14:35:22,456 - INFO - Crawled 1247 pages for Daily Full Scan
2025-12-11 14:35:23,789 - INFO - Schedule executed successfully
```

## Features

### Frequency Support

| Frequency | Cron | When |
|-----------|------|------|
| hourly | `0 * * * *` | Top of every hour |
| daily | `0 2 * * *` | 2 AM UTC daily |
| weekly | `0 3 ? * MON` | 3 AM UTC Mondays |
| custom | User-defined | Flexible scheduling |

### Schedule Templates

Pre-configured templates:

1. **Daily Full Site Scan**
   - Frequency: Daily at 2 AM
   - Pages: All (0 = unlimited)
   - Use case: Comprehensive daily review

2. **Weekly Comprehensive Scan**
   - Frequency: Weekly (Monday 3 AM)
   - Pages: Up to 5000
   - Use case: Deep scan for analysis

3. **Hourly Critical Pages Check**
   - Frequency: Every hour
   - Pages: 10 (critical pages only)
   - Use case: Rapid detection of issues

### Daemon Features

- **Background execution**: Runs independently
- **Process management**: PID tracking, startup/shutdown
- **Job scheduling**: APScheduler integration
- **Error handling**: Graceful failure recovery
- **Logging**: Centralized daemon logs
- **Status monitoring**: Quick status checks
- **Schedule reloading**: Dynamic config updates

## Dependencies

### Required

- Python 3.11+
- APScheduler (for daemon mode)
- Existing project dependencies (crawl4ai, typer, rich, etc.)

### Installation

```bash
pip install apscheduler
```

## Usage Examples

### Create a Daily Scan

```bash
bug-finder schedule add "Daily WPR Scan" \
  --site "https://www.wpr.org" \
  --example "https://www.wpr.org/food/article" \
  --frequency daily
```

### Run Schedule Immediately

```bash
bug-finder schedule run schedule_20251211_a1b2c3d4
```

### Start Daemon

```bash
bug-finder daemon start
```

### Check Status

```bash
bug-finder daemon status
```

### View Logs

```bash
bug-finder daemon logs --lines 100
```

### Custom Cron (Every 6 Hours)

```bash
bug-finder schedule add "Every 6 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */6 * * *"
```

## System Integration

### Linux (systemd)

```bash
sudo cp src/analyzer/website-analyzer-scheduler.service \
  /etc/systemd/user/
systemctl --user enable website-analyzer-scheduler
systemctl --user start website-analyzer-scheduler
```

### macOS (launchd)

```bash
cp src/analyzer/com.website-analyzer.scheduler.plist \
  ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist
```

### Docker

```bash
docker run -d \
  -v ~/.website-analyzer:/root/.website-analyzer \
  website-analyzer-scheduler
```

## Testing

Comprehensive test suite with 45+ tests covering:

- Schedule creation and persistence
- Enable/disable functionality
- Schedule listing and filtering
- Frequency enum validation
- ID generation
- Template validation
- Daemon status tracking
- Integration workflows

Run tests:
```bash
python3.11 -m pytest tests/test_scheduler.py -v
```

## Configuration

### Environment

- `~/.website-analyzer/` - Default config directory
- `~/.website-analyzer/schedules.json` - Schedule storage
- `~/.website-analyzer/logs/` - Daemon logs

### Customization

Schedules can be manually edited in `schedules.json`:

1. Edit `~/.website-analyzer/schedules.json`
2. Changes take effect on next daemon reload
3. Or restart daemon: `bug-finder daemon stop && bug-finder daemon start`

## Performance Characteristics

### Resource Usage

- **Memory**: ~50-100 MB base + crawl overhead
- **CPU**: Minimal when idle
- **Disk**: Logs ~100KB/day, results vary by site
- **Network**: Depends on scan parameters

### Scaling

- Single daemon: 1-10 concurrent schedules
- Multiple sites: Stagger start times
- Large scans: Run during off-peak hours

## Future Enhancements

Planned features for future releases:

1. **Notification System**
   - Email alerts on completion/failure
   - Slack webhook integration
   - Custom webhooks

2. **Dashboard**
   - Web UI for schedule management
   - Real-time monitoring
   - Performance metrics

3. **Advanced Scheduling**
   - Schedule dependencies
   - Conditional execution
   - Retry logic

4. **Analytics**
   - Performance trends
   - Issue tracking over time
   - Report generation

5. **Integration**
   - CI/CD pipeline support
   - API endpoints
   - Webhooks

## Documentation Structure

1. **SCHEDULER_QUICK_START.md** - Start here (5 minutes)
2. **SCHEDULER_GUIDE.md** - Detailed reference (comprehensive)
3. **SCHEDULER_COMMAND_REFERENCE.md** - All commands (detailed)
4. **SCHEDULER_DEPLOYMENT.md** - Production setup (systemd, Docker, K8s)
5. **SCHEDULER_IMPLEMENTATION_SUMMARY.md** - This file (overview)

## Troubleshooting

### Common Issues

**"APScheduler not installed"**
```bash
pip install apscheduler
```

**"Daemon already running"**
```bash
bug-finder daemon status
bug-finder daemon stop
```

**"Schedule not executing"**
1. Check daemon status: `bug-finder daemon status`
2. Verify schedule: `bug-finder schedule show <id>`
3. Test manually: `bug-finder schedule run <id>`
4. Check logs: `bug-finder daemon logs`

## Support and Contributions

For issues or improvements:

1. Check SCHEDULER_GUIDE.md for solutions
2. Review logs: `tail -f ~/.website-analyzer/logs/scheduler.log`
3. Run tests: `python3.11 -m pytest tests/test_scheduler.py`
4. Verify configuration: `bug-finder schedule list`

## Summary Statistics

### Implementation

- **Total lines of code**: 1,200+
- **Core module**: 600+ lines (scheduler.py)
- **CLI commands**: 12 commands
- **Tests**: 45+ test cases
- **Documentation**: 2,000+ lines

### Features

- ✓ Cron-style scheduling
- ✓ Multiple frequency presets
- ✓ Custom cron expressions
- ✓ Persistent storage
- ✓ Background daemon
- ✓ System integration (systemd/launchd)
- ✓ Comprehensive logging
- ✓ Enable/disable toggles
- ✓ Schedule templates
- ✓ Error handling
- ✓ Status monitoring
- ✓ Docker support

## Quick Reference

### Install
```bash
pip install apscheduler
```

### Create Schedule
```bash
bug-finder schedule add "Name" --site <url> --example <url> --frequency daily
```

### Start Daemon
```bash
bug-finder daemon start
```

### Monitor
```bash
bug-finder daemon status
bug-finder daemon logs
```

### Test
```bash
bug-finder schedule run <schedule_id>
```

### Manage
```bash
bug-finder schedule list
bug-finder schedule enable <id>
bug-finder schedule disable <id>
bug-finder schedule remove <id>
```

---

## Next Steps

1. **Install dependencies**: `pip install apscheduler`
2. **Read quick start**: Open SCHEDULER_QUICK_START.md
3. **Create first schedule**: `bug-finder schedule add ...`
4. **Start daemon**: `bug-finder daemon start`
5. **Monitor**: `bug-finder daemon logs -f`
6. **Integrate with system**: Follow SCHEDULER_DEPLOYMENT.md

---

**Last Updated**: 2025-12-11
**Version**: 1.0
**Status**: Production Ready
