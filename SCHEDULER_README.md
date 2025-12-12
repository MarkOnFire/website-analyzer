# Scheduler and Automation System

Welcome to the comprehensive scheduling system for website scans!

This system allows you to create recurring scans on a schedule (hourly, daily, weekly, or custom) and manage them through a simple command-line interface. Schedules run automatically in the background using a daemon process.

## What Can You Do?

### Create Recurring Scans

Define scans that run automatically:
- Daily full-site scans
- Weekly comprehensive reviews
- Hourly critical page checks
- Custom schedules with cron expressions

### Manage Schedules

- Create, list, enable, disable, and remove schedules
- Run schedules immediately for testing
- View detailed schedule information
- Tag schedules for organization

### Automatic Execution

- Background daemon handles all scheduling
- Minimal resource usage when idle
- Robust error handling and logging
- Easy enable/disable without deletion

### System Integration

- Linux: systemd service file included
- macOS: launchd agent included
- Docker: Ready for containerization
- Kubernetes: Ready for orchestration

## Installation

### 1. Install Dependencies

```bash
pip install apscheduler
```

That's it! APScheduler is the only required dependency.

### 2. Optional: System Integration

**Linux (systemd):**
```bash
sudo cp src/analyzer/website-analyzer-scheduler.service /etc/systemd/user/
systemctl --user enable website-analyzer-scheduler
systemctl --user start website-analyzer-scheduler
```

**macOS (launchd):**
```bash
cp src/analyzer/com.website-analyzer.scheduler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist
```

## Quick Start (5 Minutes)

### Step 1: Create a Schedule

```bash
bug-finder schedule add "My Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily
```

You'll see:
```
✓ Schedule created successfully
  ID: schedule_20251211120000_a1b2c3d4
  Name: My Daily Scan
  Frequency: daily
  Site: https://example.com
  Max pages: 1000
```

### Step 2: List Your Schedules

```bash
bug-finder schedule list
```

Shows a table of all your schedules with status.

### Step 3: Start the Daemon

```bash
bug-finder daemon start
```

The daemon is now running in the background. Your schedules will execute automatically according to their schedule.

### Step 4: Check Status

```bash
bug-finder daemon status
```

Shows if daemon is running and how many schedules are enabled.

### Step 5: View Logs

```bash
bug-finder daemon logs
```

See recent log entries from the daemon.

That's it! Your schedules will now run automatically.

## Common Commands

### Create Different Types of Schedules

```bash
# Hourly (quick check of critical pages)
bug-finder schedule add "Hourly Check" \
  --site "https://example.com" \
  --example "https://example.com/critical" \
  --frequency hourly \
  --max-pages 5

# Weekly (comprehensive deep scan)
bug-finder schedule add "Weekly Deep Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency weekly \
  --max-pages 5000

# Custom (every 4 hours)
bug-finder schedule add "Every 4 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */4 * * *"
```

### Manage Schedules

```bash
# List all
bug-finder schedule list

# Show details
bug-finder schedule show <schedule_id>

# Enable/disable
bug-finder schedule enable <schedule_id>
bug-finder schedule disable <schedule_id>

# Test immediately
bug-finder schedule run <schedule_id>

# Remove
bug-finder schedule remove <schedule_id> --yes
```

### Daemon Control

```bash
# Start
bug-finder daemon start

# Stop
bug-finder daemon stop

# Check status
bug-finder daemon status

# View logs
bug-finder daemon logs

# View last 100 lines
bug-finder daemon logs --lines 100

# Stream logs
tail -f ~/.website-analyzer/logs/scheduler.log
```

## Where Are My Schedules?

All schedules are stored in: **`~/.website-analyzer/schedules.json`**

You can view or manually edit this file, but it's safer to use the CLI commands.

## How Do I Use Cron Expressions?

Cron expressions let you schedule tasks with precise timing. Format is:

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

### Common Examples

- `0 0 * * *` - Every day at midnight
- `0 2 * * *` - Every day at 2 AM
- `0 * * * *` - Every hour
- `*/15 * * * *` - Every 15 minutes
- `0 9 * * MON-FRI` - 9 AM on weekdays
- `0 0 1 * *` - First day of month
- `0 */6 * * *` - Every 6 hours

For more examples, see [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md).

## Documentation

Different documents for different needs:

| Document | Use Case |
|----------|----------|
| **This file** | Overview and quick start |
| [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md) | 5-minute setup guide |
| [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) | Complete reference (500+ lines) |
| [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md) | All commands with examples |
| [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md) | Production deployment |
| [SCHEDULER_IMPLEMENTATION_SUMMARY.md](SCHEDULER_IMPLEMENTATION_SUMMARY.md) | Technical overview |

## Troubleshooting

### Q: Is the daemon running?

```bash
bug-finder daemon status
```

Should show:
```
Status: RUNNING
PID: 12345
Enabled schedules: 3
```

### Q: Why isn't my schedule running?

1. Check daemon is running: `bug-finder daemon status`
2. Verify schedule is enabled: `bug-finder schedule show <id>`
3. Test manually: `bug-finder schedule run <id>`
4. Check logs: `bug-finder daemon logs`

### Q: How do I stop a schedule?

Disable it (keeps it for later):
```bash
bug-finder schedule disable <schedule_id>
```

Or remove it permanently:
```bash
bug-finder schedule remove <schedule_id> --yes
```

### Q: Can I edit schedules manually?

Yes, you can edit `~/.website-analyzer/schedules.json` directly. The daemon will pick up changes when restarted.

### Q: What if APScheduler isn't installed?

Install it:
```bash
pip install apscheduler
```

### Q: Where are the logs?

```bash
~/.website-analyzer/logs/scheduler.log
```

View them:
```bash
tail -f ~/.website-analyzer/logs/scheduler.log
```

## Example Scenarios

### Scenario 1: Daily Production Monitoring

```bash
# Create daily full scan at 2 AM
bug-finder schedule add "Daily Production Scan" \
  --site "https://www.mycompany.com" \
  --example "https://www.mycompany.com/article" \
  --frequency daily \
  --max-pages 0 \
  --tags "production,daily"

# Start daemon
bug-finder daemon start

# Check status
bug-finder daemon status

# View logs
tail -f ~/.website-analyzer/logs/scheduler.log
```

### Scenario 2: Critical Page Monitoring

```bash
# Check critical pages every hour
bug-finder schedule add "Critical Pages Monitor" \
  --site "https://api.example.com" \
  --example "https://api.example.com/status" \
  --frequency hourly \
  --max-pages 5 \
  --tags "critical,api"

# Enable daemon if not running
bug-finder daemon start

# Monitor logs
bug-finder daemon logs --lines 50
```

### Scenario 3: Weekly Deep Analysis

```bash
# Comprehensive scan every Monday at 3 AM
bug-finder schedule add "Weekly Analysis" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency weekly \
  --max-pages 10000 \
  --tags "analysis,weekly"

# Start and monitor
bug-finder daemon start
sleep 2
bug-finder daemon status
```

### Scenario 4: Business Hours Only

```bash
# Scan every hour 9 AM to 5 PM, weekdays only
bug-finder schedule add "Business Hours Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 9-17 * * MON-FRI" \
  --max-pages 500

bug-finder daemon start
```

## Key Features

✅ **Easy to Use**
- Simple CLI commands
- Clear help text
- Sensible defaults

✅ **Reliable**
- Persistent storage
- Error handling
- Comprehensive logging

✅ **Flexible**
- Multiple frequency options
- Custom cron expressions
- Enable/disable without deletion

✅ **Scalable**
- Handle multiple schedules
- Stagger concurrent execution
- Resource-aware scheduling

✅ **Well Integrated**
- Works with systemd (Linux)
- Works with launchd (macOS)
- Docker ready
- Kubernetes compatible

## Advanced Features

### Tags for Organization

```bash
bug-finder schedule add "My Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily \
  --tags "production,critical,daily"
```

### Custom Output Directory

```bash
bug-finder schedule add "My Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily \
  --output "/var/scans/my-site"
```

### Dynamic Enable/Disable

```bash
# Disable before maintenance
bug-finder schedule disable <schedule_id>

# Do maintenance...

# Re-enable
bug-finder schedule enable <schedule_id>
```

## Performance Tips

1. **Stagger schedules**: Don't run all full scans at once
2. **Limit page counts**: Use `--max-pages` to control resource usage
3. **Use hourly for critical**: Only critical pages for frequent checks
4. **Off-peak scheduling**: Run large scans during low-traffic times
5. **Monitor logs**: Watch for errors and optimize accordingly

## Getting Help

### View a Command's Help

```bash
bug-finder schedule add --help
bug-finder daemon start --help
```

### Check the Documentation

- [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) - Comprehensive guide
- [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md) - All commands
- [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md) - Deployment guide

### Check the Logs

```bash
bug-finder daemon logs
```

## Example Schedules

See [example_schedules.json](example_schedules.json) for example configurations you can use as a reference.

## API Usage (Python)

If you want to use the scheduler from Python code:

```python
from src.analyzer.scheduler import (
    ScheduleManager, ScheduleConfig, ScheduledScanRunner, SchedulerDaemon
)

# Create manager
manager = ScheduleManager()

# Add a schedule
schedule = ScheduleConfig(
    id="my_schedule",
    name="My Scan",
    site_url="https://example.com",
    example_url="https://example.com/page",
    frequency="daily",
    max_pages=1000
)
manager.add_schedule(schedule)

# List schedules
schedules = manager.list_schedules()

# Run a schedule
runner = ScheduledScanRunner()
result = runner.run_schedule_sync("my_schedule")

# Start daemon
daemon = SchedulerDaemon()
daemon.start()
```

For more API details, see [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md).

## What's Next?

1. **Create your first schedule**: `bug-finder schedule add ...`
2. **Start the daemon**: `bug-finder daemon start`
3. **Monitor execution**: `bug-finder daemon logs -f`
4. **Read more docs**: [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)
5. **Deploy to production**: [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md)

## Support

For issues or questions:

1. Check the FAQ in [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)
2. Review [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md) for command syntax
3. Check logs: `bug-finder daemon logs`
4. Verify configuration: `bug-finder schedule list`

---

**Happy Scheduling!** 🚀

For complete documentation, start with [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md) or [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md).
