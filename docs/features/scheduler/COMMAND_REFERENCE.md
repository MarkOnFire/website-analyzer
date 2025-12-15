# Scheduler Commands Reference

## Schedule Management (`bug-finder schedule`)

### `bug-finder schedule add`

Create a new scheduled scan.

**Syntax:**
```bash
bug-finder schedule add <name> \
  --site <url> \
  --example <url> \
  [--frequency <freq>] \
  [--max-pages <num>] \
  [--cron <expression>] \
  [--output <dir>] \
  [--tags <tag1,tag2>]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<name>` | Yes | - | Descriptive name for the schedule |
| `--site` | Yes | - | Base URL to scan (e.g., `https://example.com`) |
| `--example` | Yes | - | Example URL showing the bug |
| `--frequency` | No | `daily` | `hourly`, `daily`, `weekly`, or `custom` |
| `--max-pages` | No | `1000` | Max pages to scan (0 = all pages) |
| `--cron` | No | - | Custom cron expression (required if frequency=custom) |
| `--output` | No | - | Output directory for results |
| `--tags` | No | - | Comma-separated tags (e.g., `production,critical`) |

**Examples:**

```bash
# Daily scan
bug-finder schedule add "Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily

# Hourly critical check (limited pages)
bug-finder schedule add "Hourly Check" \
  --site "https://example.com" \
  --example "https://example.com/critical" \
  --frequency hourly \
  --max-pages 5 \
  --tags "critical,hourly"

# Custom cron (every 4 hours)
bug-finder schedule add "Every 4 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */4 * * *"

# With output directory
bug-finder schedule add "Custom Output" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency weekly \
  --output "/var/scans/results"
```

**Output:**
```
✓ Schedule created successfully
  ID: schedule_20251211120000_a1b2c3d4
  Name: Daily Scan
  Frequency: daily
  Site: https://example.com
  Max pages: 1000
```

---

### `bug-finder schedule list`

Show all scheduled scans.

**Syntax:**
```bash
bug-finder schedule list [--enabled]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--enabled` | Show only enabled schedules |

**Examples:**

```bash
# List all schedules
bug-finder schedule list

# List only enabled
bug-finder schedule list --enabled
```

**Output:**
```
Scheduled Scans
┌──────────────────────────┬────────────────────┬───────────┬──────────────────┬────────────┬──────────┬────────────┐
│ ID                       │ Name               │ Frequency │ Site             │ Max Pages  │ Status   │ Last Run   │
├──────────────────────────┼────────────────────┼───────────┼──────────────────┼────────────┼──────────┼────────────┤
│ schedule_20251211_a1b2c3 │ Daily Scan         │ daily     │ example.com      │ 1000       │ enabled  │ 2025-12-11 │
│ schedule_20251211_d4e5f6 │ Weekly Comprehensive│ weekly    │ example.com      │ 5000       │ enabled  │ -          │
│ schedule_20251211_g7h8i9 │ Hourly Check       │ hourly    │ example.com      │ 10         │ disabled │ -          │
└──────────────────────────┴────────────────────┴───────────┴──────────────────┴────────────┴──────────┴────────────┘

Total: 3 schedule(s)
```

---

### `bug-finder schedule show`

Show details of a specific schedule.

**Syntax:**
```bash
bug-finder schedule show <schedule_id>
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<schedule_id>` | Yes | Full or partial schedule ID |

**Examples:**

```bash
bug-finder schedule show schedule_20251211_a1b2c3d4
```

**Output:**
```
Schedule Details

ID:              schedule_20251211_a1b2c3d4
Name:            Daily Scan
Site URL:        https://example.com
Example URL:     https://example.com/page
Frequency:       daily
Max Pages:       1000
Status:          enabled
Cron:            0 2 * * *
Output Dir:      /var/scans/results
Tags:            production, daily, full-site
Created:         2025-12-11
Last Run:        2025-12-11 14:30:22
Next Run:        2025-12-12 02:00:00
```

---

### `bug-finder schedule enable`

Enable a disabled schedule.

**Syntax:**
```bash
bug-finder schedule enable <schedule_id>
```

**Examples:**

```bash
bug-finder schedule enable schedule_20251211_a1b2c3d4
```

**Output:**
```
✓ Schedule enabled: Daily Scan
```

---

### `bug-finder schedule disable`

Disable a schedule.

**Syntax:**
```bash
bug-finder schedule disable <schedule_id>
```

**Examples:**

```bash
bug-finder schedule disable schedule_20251211_a1b2c3d4
```

**Output:**
```
✓ Schedule disabled: Daily Scan
```

---

### `bug-finder schedule remove`

Delete a scheduled scan.

**Syntax:**
```bash
bug-finder schedule remove <schedule_id> [--yes]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--yes`, `-y` | Skip confirmation prompt |

**Examples:**

```bash
# With confirmation
bug-finder schedule remove schedule_20251211_a1b2c3d4
# Prompts: Remove schedule 'Daily Scan' (schedule_20251211_a1b2c3d4)?

# Skip confirmation
bug-finder schedule remove schedule_20251211_a1b2c3d4 --yes
```

**Output:**
```
✓ Schedule removed
```

---

### `bug-finder schedule run`

Run a schedule immediately (skip the schedule).

**Syntax:**
```bash
bug-finder schedule run <schedule_id>
```

**Examples:**

```bash
bug-finder schedule run schedule_20251211_a1b2c3d4
```

**Output:**
```
✓ Scan completed successfully
  Pages crawled: 1247
  Output dir: /var/scans/results
```

---

## Daemon Control (`bug-finder daemon`)

### `bug-finder daemon start`

Start the scheduler daemon in background.

**Syntax:**
```bash
bug-finder daemon start [--no-background]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--no-background` | Run in foreground (for debugging) |

**Examples:**

```bash
# Start in background
bug-finder daemon start

# Run in foreground
bug-finder daemon start --no-background
```

**Output:**
```
Starting scheduler daemon...
✓ Daemon started in background (PID: 12345)
View logs: tail -f ~/.website-analyzer/logs/scheduler.log
```

---

### `bug-finder daemon stop`

Stop the scheduler daemon.

**Syntax:**
```bash
bug-finder daemon stop
```

**Examples:**

```bash
bug-finder daemon stop
```

**Output:**
```
Stopping daemon (PID: 12345)...
✓ Daemon stopped
```

---

### `bug-finder daemon status`

Check daemon status.

**Syntax:**
```bash
bug-finder daemon status
```

**Examples:**

```bash
bug-finder daemon status
```

**Output (Running):**
```
Scheduler Daemon Status

Status:           RUNNING
PID:              12345
Enabled schedules: 3

View logs: tail -f ~/.website-analyzer/logs/scheduler.log
```

**Output (Stopped):**
```
Scheduler Daemon Status

Status:           STOPPED
Enabled schedules: 3
```

---

### `bug-finder daemon logs`

View scheduler daemon logs.

**Syntax:**
```bash
bug-finder daemon logs [--lines <num>]
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--lines`, `-n` | `50` | Number of lines to show |

**Examples:**

```bash
# Last 50 lines (default)
bug-finder daemon logs

# Last 100 lines
bug-finder daemon logs --lines 100

# Stream logs in real-time
tail -f ~/.website-analyzer/logs/scheduler.log
```

**Output:**
```
Last 10 log entries:

2025-12-11 14:30:00,123 - INFO - Starting scheduled scan: Daily Scan
2025-12-11 14:35:22,456 - INFO - Crawled 1247 pages for Daily Scan
2025-12-11 14:35:23,789 - INFO - Schedule executed successfully
2025-12-11 15:00:00,000 - INFO - Starting scheduled scan: Hourly Check
2025-12-11 15:05:10,111 - INFO - Crawled 5 pages for Hourly Check
...
```

---

## Cron Expression Guide

### Common Patterns

| Pattern | Description |
|---------|-------------|
| `0 0 * * *` | Every day at midnight |
| `0 2 * * *` | Every day at 2 AM |
| `0 * * * *` | Every hour on the hour |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 ? * MON` | Every Monday at midnight |
| `0 0 1 * *` | First day of month at midnight |
| `0 9-17 * * MON-FRI` | Every hour 9 AM-5 PM weekdays |
| `0 */6 * * *` | Every 6 hours |
| `0 2 ? * MON,WED,FRI` | 2 AM on Mon, Wed, Fri |

### Cron Field Reference

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

**Special Values:**
- `*` - Any value
- `,` - Value list separator (e.g., `MON,WED,FRI`)
- `-` - Value range (e.g., `9-17`)
- `/` - Step values (e.g., `*/15` = every 15)
- `?` - No specific value (day/day of week only)
- `L` - Last (e.g., `L` = last day of month)
- `#` - Nth occurrence (e.g., `3#2` = 2nd Tuesday)

### Day of Week

| Number | Day | Short |
|--------|-----|-------|
| 0 | Sunday | SUN |
| 1 | Monday | MON |
| 2 | Tuesday | TUE |
| 3 | Wednesday | WED |
| 4 | Thursday | THU |
| 5 | Friday | FRI |
| 6 | Saturday | SAT |

---

## Command Line Examples

### Complete Workflow

```bash
# 1. Create a schedule
bug-finder schedule add "My Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily \
  --tags "production"

# 2. List all schedules
bug-finder schedule list

# 3. Start the daemon
bug-finder daemon start

# 4. Check daemon status
bug-finder daemon status

# 5. Test schedule immediately
bug-finder schedule run schedule_20251211_a1b2c3d4

# 6. View logs
bug-finder daemon logs

# 7. Disable if needed
bug-finder schedule disable schedule_20251211_a1b2c3d4

# 8. Re-enable when ready
bug-finder schedule enable schedule_20251211_a1b2c3d4

# 9. Remove when done
bug-finder schedule remove schedule_20251211_a1b2c3d4 --yes
```

### Multi-Site Setup

```bash
# Create schedules for multiple sites
bug-finder schedule add "WPR Daily" \
  --site "https://www.wpr.org" \
  --example "https://www.wpr.org/food/article" \
  --frequency daily \
  --tags "wpr"

bug-finder schedule add "Example Daily" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily \
  --tags "example"

# List all
bug-finder schedule list

# Start daemon once for all
bug-finder daemon start
```

### Advanced Scheduling

```bash
# Business hours only
bug-finder schedule add "Business Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 9-17 * * MON-FRI" \
  --max-pages 100

# Every 4 hours
bug-finder schedule add "Every 4 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */4 * * *" \
  --max-pages 200

# Last day of month
bug-finder schedule add "Monthly Review" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 3 L * *" \
  --max-pages 0
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (schedule not found, invalid params, etc.) |
| 2 | Command line usage error |

---

## Environment Variables

No environment variables required for basic operation.

Optional:
- `LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `HOME` - Used to locate `~/.website-analyzer/`

---

## See Also

- [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) - Comprehensive guide
- [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md) - Quick start guide
- [example_schedules.json](example_schedules.json) - Example configuration
