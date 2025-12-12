# Scheduler Quick Start Guide

## Installation

```bash
pip install apscheduler
```

## 5-Minute Setup

### 1. Create Your First Schedule

```bash
bug-finder schedule add "My Daily Scan" \
  --site "https://www.example.com" \
  --example "https://www.example.com/page" \
  --frequency daily
```

### 2. List Your Schedules

```bash
bug-finder schedule list
```

You'll see a table with all schedules:

```
Scheduled Scans
┌──────────────┬──────────────────┬───────────┬──────────────────┬────────────┬──────────┬──────────┐
│ ID           │ Name             │ Frequency │ Site             │ Max Pages  │ Status   │ Last Run │
├──────────────┼──────────────────┼───────────┼──────────────────┼────────────┼──────────┼──────────┤
│ schedule_... │ My Daily Scan    │ daily     │ example.com      │ 1000       │ enabled  │ -        │
└──────────────┴──────────────────┴───────────┴──────────────────┴────────────┴──────────┴──────────┘

Total: 1 schedule(s)
```

### 3. Start the Daemon

```bash
bug-finder daemon start
```

Output:
```
Starting scheduler daemon...
✓ Daemon started in background (PID: 12345)
View logs: tail -f ~/.website-analyzer/logs/scheduler.log
```

### 4. Check Status Anytime

```bash
bug-finder daemon status
```

### 5. View Logs

```bash
bug-finder daemon logs
```

## Common Commands

### Create a Schedule

```bash
bug-finder schedule add "<name>" --site <url> --example <url> --frequency <freq>
```

Frequencies: `hourly`, `daily`, `weekly`, or `custom` (with `--cron`)

### Test a Schedule Immediately

```bash
bug-finder schedule run <schedule_id>
```

### Enable/Disable a Schedule

```bash
bug-finder schedule enable <schedule_id>
bug-finder schedule disable <schedule_id>
```

### Delete a Schedule

```bash
bug-finder schedule remove <schedule_id> --yes
```

### Daemon Control

```bash
bug-finder daemon start      # Start daemon
bug-finder daemon stop       # Stop daemon
bug-finder daemon status     # Check if running
bug-finder daemon logs       # View recent logs
bug-finder daemon logs -n 100 # View last 100 lines
```

## Common Schedules

### Daily (2 AM UTC)

```bash
bug-finder schedule add "Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily
```

### Hourly

```bash
bug-finder schedule add "Hourly Check" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency hourly \
  --max-pages 10
```

### Weekly (Monday, 3 AM UTC)

```bash
bug-finder schedule add "Weekly Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency weekly \
  --max-pages 5000
```

### Custom (Every 6 hours)

```bash
bug-finder schedule add "Every 6 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */6 * * *"
```

## Troubleshooting

**Daemon won't start?**

```bash
# Check if already running
ps aux | grep SchedulerDaemon

# Kill if stuck
pkill -f SchedulerDaemon

# Start fresh
bug-finder daemon start
```

**Schedule not running?**

1. Check if daemon is running:
   ```bash
   bug-finder daemon status
   ```

2. Verify schedule is enabled:
   ```bash
   bug-finder schedule show <schedule_id>
   ```

3. Run manually to test:
   ```bash
   bug-finder schedule run <schedule_id>
   ```

4. Check logs:
   ```bash
   bug-finder daemon logs
   ```

**Need to install APScheduler?**

```bash
pip install apscheduler
```

## Configuration File

Schedules are stored in: `~/.website-analyzer/schedules.json`

Manual editing is supported - daemon will reload on restart.

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

## Next Steps

- Read [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) for detailed documentation
- Set up system integration (systemd/launchd)
- Configure cron expressions for custom schedules
- Enable logging and monitoring
- Create a schedule for your site
