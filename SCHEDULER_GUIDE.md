# Scheduler and Automation System

## Overview

The scheduling and automation system enables recurring scans with cron-style scheduling. It includes:

- **Schedule Management**: Create, list, enable/disable, and remove schedules
- **Background Daemon**: Runs scheduled scans automatically in the background
- **Persistent Storage**: Schedules are saved to `~/.website-analyzer/schedules.json`
- **Logging**: All daemon activity is logged to `~/.website-analyzer/logs/scheduler.log`
- **Flexible Scheduling**: Support for hourly, daily, weekly, and custom cron expressions

## Installation

### Prerequisites

```bash
pip install apscheduler
```

The scheduler uses APScheduler for background scheduling. Install it with the main package:

```bash
pip install -e .
```

## CLI Commands

### Schedule Management

#### Create a New Schedule

```bash
bug-finder schedule add "<schedule_name>" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page-with-bug" \
  --frequency daily \
  --max-pages 1000 \
  --tags "production,daily"
```

**Parameters:**
- `<name>` (required): Descriptive name for the schedule
- `--site` (required): Base URL to scan
- `--example` (required): Example URL showing the bug
- `--frequency` (optional): `hourly`, `daily`, `weekly`, or `custom` (default: `daily`)
- `--cron` (optional): Custom cron expression (required if `--frequency custom`)
- `--max-pages` (optional): Maximum pages to scan, 0 for all (default: 1000)
- `--output` (optional): Output directory for results
- `--tags` (optional): Comma-separated tags for organization

**Examples:**

Daily full site scan:
```bash
bug-finder schedule add "Daily Full Scan" \
  --site "https://www.wpr.org" \
  --example "https://www.wpr.org/food/article" \
  --frequency daily \
  --max-pages 0
```

Hourly critical pages check:
```bash
bug-finder schedule add "Hourly Critical Check" \
  --site "https://www.example.com" \
  --example "https://www.example.com/critical" \
  --frequency hourly \
  --max-pages 10
```

Custom schedule (every 6 hours):
```bash
bug-finder schedule add "Every 6 Hours" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency custom \
  --cron "0 */6 * * *"
```

#### List All Schedules

```bash
bug-finder schedule list
```

Show only enabled schedules:
```bash
bug-finder schedule list --enabled
```

#### Show Schedule Details

```bash
bug-finder schedule show <schedule_id>
```

#### Enable a Schedule

```bash
bug-finder schedule enable <schedule_id>
```

#### Disable a Schedule

```bash
bug-finder schedule disable <schedule_id>
```

#### Run Schedule Immediately

Execute a schedule right now (skip the schedule):

```bash
bug-finder schedule run <schedule_id>
```

#### Remove a Schedule

```bash
bug-finder schedule remove <schedule_id>
# Confirm when prompted

# Or skip confirmation
bug-finder schedule remove <schedule_id> --yes
```

### Daemon Control

#### Start the Daemon

```bash
# Start in background (recommended)
bug-finder daemon start

# Start in foreground (for debugging)
bug-finder daemon start --no-background
```

Output:
```
Starting scheduler daemon...
✓ Daemon started in background (PID: 12345)
View logs: tail -f ~/.website-analyzer/logs/scheduler.log
```

#### Stop the Daemon

```bash
bug-finder daemon stop
```

#### Check Daemon Status

```bash
bug-finder daemon status
```

Output:
```
Scheduler Daemon Status

Status:        RUNNING
PID:           12345
Enabled schedules: 3

View logs: tail -f ~/.website-analyzer/logs/scheduler.log
```

#### View Daemon Logs

```bash
# Last 50 lines (default)
bug-finder daemon logs

# Last 100 lines
bug-finder daemon logs --lines 100

# Stream logs in real-time
tail -f ~/.website-analyzer/logs/scheduler.log
```

## Schedule Configuration

### Schedule File Location

Schedules are stored in: `~/.website-analyzer/schedules.json`

### Schedule Format

```json
{
  "schedules": [
    {
      "id": "schedule_20251211120000_a1b2c3d4",
      "name": "Daily Full Site Scan",
      "site_url": "https://www.example.com",
      "example_url": "https://www.example.com/page-with-bug",
      "frequency": "daily",
      "max_pages": 0,
      "enabled": true,
      "output_dir": "/path/to/output",
      "cron_expression": "0 2 * * *",
      "notifications": {},
      "created_at": "2025-12-11T12:00:00",
      "last_run": "2025-12-11T12:00:15.123456",
      "next_run": "2025-12-12T02:00:00",
      "tags": ["production", "daily", "full-site"]
    }
  ]
}
```

### Frequency Options

| Frequency | Cron Expression | Notes |
|-----------|-----------------|-------|
| `hourly` | `0 * * * *` | Runs at the top of every hour |
| `daily` | `0 2 * * *` | Runs at 2 AM UTC daily |
| `weekly` | `0 3 ? * MON` | Runs at 3 AM UTC on Mondays |
| `custom` | User-defined | Requires `--cron` parameter |

### Custom Cron Expressions

Use standard cron syntax (5 fields):

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Examples:**

- `0 0 * * *` - Every day at midnight
- `0 9 * * MON-FRI` - Weekdays at 9 AM
- `0 */4 * * *` - Every 4 hours
- `*/15 * * * *` - Every 15 minutes
- `0 2 1 * *` - First day of month at 2 AM
- `0 0 ? * 0` - Every Sunday at midnight

## Example Templates

### Daily Full Site Scan

```bash
bug-finder schedule add "Daily Full Scan" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency daily \
  --max-pages 0 \
  --tags "full-site,daily"
```

Schedule metadata:
- Runs every day at 2 AM UTC
- Scans all pages on the site
- Stores results in projects directory
- Cron: `0 2 * * *`

### Weekly Comprehensive Scan

```bash
bug-finder schedule add "Weekly Comprehensive" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency weekly \
  --max-pages 5000 \
  --tags "comprehensive,weekly"
```

Schedule metadata:
- Runs every Monday at 3 AM UTC
- Deep scan up to 5000 pages
- Cron: `0 3 ? * MON`

### Hourly Critical Page Check

```bash
bug-finder schedule add "Hourly Critical Check" \
  --site "https://www.example.com" \
  --example "https://www.example.com/critical-page" \
  --frequency hourly \
  --max-pages 5 \
  --tags "critical,hourly"
```

Schedule metadata:
- Runs every hour on the hour
- Checks just critical pages
- Quick scan, minimal resources
- Cron: `0 * * * *`

### Custom: Every 6 Hours

```bash
bug-finder schedule add "Every 6 Hours" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency custom \
  --cron "0 */6 * * *" \
  --max-pages 500
```

### Custom: Business Hours Only

```bash
bug-finder schedule add "Business Hours Scan" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency custom \
  --cron "0 9-17 * * MON-FRI" \
  --max-pages 100
```

Runs hourly from 9 AM to 5 PM on weekdays (UTC).

## System Integration

### Linux (systemd)

Install the service file:

```bash
# Copy service file to systemd directory
sudo cp src/analyzer/website-analyzer-scheduler.service \
  /etc/systemd/user/website-analyzer-scheduler.service

# Reload systemd
systemctl --user daemon-reload

# Enable to start on login
systemctl --user enable website-analyzer-scheduler

# Start the service
systemctl --user start website-analyzer-scheduler

# Check status
systemctl --user status website-analyzer-scheduler

# View logs
journalctl --user -u website-analyzer-scheduler -f
```

### macOS (launchd)

Install the launch agent:

```bash
# Copy plist file to LaunchAgents
cp src/analyzer/com.website-analyzer.scheduler.plist \
  ~/Library/LaunchAgents/

# Load the agent
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Unload to disable
launchctl unload ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Check status
launchctl list | grep website-analyzer

# View logs
log stream --predicate 'eventMessage contains[c] "website-analyzer"' --level debug
```

## Logging

### Log File Location

All daemon logs are written to: `~/.website-analyzer/logs/scheduler.log`

### Log Format

```
2025-12-11 14:30:00,123 - INFO - Starting scheduled scan: Daily Full Scan
2025-12-11 14:35:22,456 - INFO - Crawled 1247 pages for Daily Full Scan
2025-12-11 14:35:23,789 - INFO - Added job: Weekly Comprehensive (schedule_20251211_abc123)
```

### Log Levels

- `DEBUG` - Detailed information for debugging
- `INFO` - Confirmation that things are working
- `WARNING` - Something unexpected, but the daemon continues
- `ERROR` - A serious problem, a function may not have worked
- `CRITICAL` - A very serious error, the daemon may stop

## Troubleshooting

### Daemon Won't Start

**Error: "APScheduler not installed"**

```bash
pip install apscheduler
```

**Error: "Address already in use"**

The daemon is already running. Check status:

```bash
bug-finder daemon status
```

Stop if needed:

```bash
bug-finder daemon stop
```

### Schedule Not Running

1. Check if daemon is running:
   ```bash
   bug-finder daemon status
   ```

2. Verify schedule is enabled:
   ```bash
   bug-finder schedule show <schedule_id>
   ```

3. Check logs:
   ```bash
   bug-finder daemon logs --lines 100
   ```

4. Run schedule manually to test:
   ```bash
   bug-finder schedule run <schedule_id>
   ```

### Permission Issues

Ensure the `~/.website-analyzer` directory is writable:

```bash
chmod -R u+w ~/.website-analyzer
```

### Memory Issues

If the daemon uses too much memory:

1. Reduce `max-pages` for schedules
2. Run fewer concurrent schedules
3. Add resource limits (systemd/launchd config)

### Cron Expression Not Working

Validate your cron expression:

```bash
# Test with custom schedule
bug-finder schedule add "Test" \
  --site "https://example.com" \
  --example "https://example.com" \
  --frequency custom \
  --cron "0 0 * * *" \
  --max-pages 1

bug-finder daemon logs --lines 20
```

Check common mistakes:
- Month/day of week out of range
- Missing fields (should be 5 fields)
- Invalid day names (use MON, TUE, etc.)

## API Reference

### ScheduleManager

```python
from src.analyzer.scheduler import ScheduleManager, ScheduleConfig

manager = ScheduleManager()

# Add a schedule
schedule = ScheduleConfig(
    id="my-schedule",
    name="My Scan",
    site_url="https://example.com",
    example_url="https://example.com/page",
    frequency="daily",
    max_pages=1000
)
manager.add_schedule(schedule)

# List all
schedules = manager.list_schedules()

# Get one
schedule = manager.get_schedule("my-schedule")

# Enable/disable
manager.enable_schedule("my-schedule")
manager.disable_schedule("my-schedule")

# Remove
manager.remove_schedule("my-schedule")
```

### ScheduledScanRunner

```python
from src.analyzer.scheduler import ScheduledScanRunner

runner = ScheduledScanRunner()

# Run a schedule
result = runner.run_schedule_sync("schedule_id")

# Result structure
{
    "success": True,
    "schedule_id": "schedule_id",
    "schedule_name": "Daily Scan",
    "pages_crawled": 1247,
    "timestamp": "2025-12-11T14:35:23.123456",
    "output_dir": "/path/to/output"
}
```

### SchedulerDaemon

```python
from src.analyzer.scheduler import SchedulerDaemon

daemon = SchedulerDaemon()

# Start the daemon (blocking)
daemon.start()

# Stop the daemon
daemon.stop()

# Get status
status = daemon.get_status()
# Returns: {"running": True, "pid": 12345, "schedules_enabled": 3}

# Reload schedules after config changes
daemon.reload_schedules()
```

## Performance Considerations

### Resource Usage

- **Memory**: ~50-100 MB base + crawl overhead
- **CPU**: Minimal when idle, depends on scan complexity
- **Disk**: Logs ~100KB/day, results vary by site size

### Scaling

For many schedules:

1. Stagger start times to avoid concurrent scans
2. Use `--max-pages` to limit scan scope
3. Monitor logs and resource usage
4. Consider running daemon on dedicated machine

### Best Practices

- Schedule large scans (full site) during off-hours
- Use hourly checks only for critical pages
- Weekly scans can be more comprehensive
- Always enable logging for troubleshooting
- Regularly review and clean up old schedules
- Use tags for organization and filtering

## Future Enhancements

Planned features:

- Notification system (email, Slack, webhooks)
- Schedule templating and presets
- Dashboard for monitoring scans
- Performance metrics and analytics
- Parallel execution of independent schedules
- Schedule dependencies and workflows
- Results archiving and cleanup
- Web UI for schedule management
- Integration with CI/CD pipelines
