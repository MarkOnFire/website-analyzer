# Scheduler System - Complete Index

## Quick Navigation

### For First-Time Users
1. **[SCHEDULER_README.md](SCHEDULER_README.md)** - Start here! Overview and quick start
2. **[SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md)** - 5-minute setup guide

### For Developers
3. **[SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)** - Comprehensive technical guide
4. **[SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md)** - All commands with examples
5. **[SCHEDULER_IMPLEMENTATION_SUMMARY.md](SCHEDULER_IMPLEMENTATION_SUMMARY.md)** - Technical architecture

### For Operations/DevOps
6. **[SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md)** - Production deployment guide
7. **[example_schedules.json](example_schedules.json)** - Example configurations

### Source Code
8. **[src/analyzer/scheduler.py](src/analyzer/scheduler.py)** - Core implementation (600+ lines)
9. **[src/analyzer/cli.py](src/analyzer/cli.py)** - CLI commands (450+ lines added)
10. **[tests/test_scheduler.py](tests/test_scheduler.py)** - Test suite (45+ tests)

### System Integration
11. **[src/analyzer/website-analyzer-scheduler.service](src/analyzer/website-analyzer-scheduler.service)** - Linux systemd
12. **[src/analyzer/com.website-analyzer.scheduler.plist](src/analyzer/com.website-analyzer.scheduler.plist)** - macOS launchd

---

## Documentation by Use Case

### "I want to create a daily scan"

1. Read: [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md) (2 min)
2. Run: `bug-finder schedule add "My Scan" --site <url> --example <url> --frequency daily`
3. Start: `bug-finder daemon start`
4. Done!

### "I want to understand all the commands"

Read: [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md)
- Complete syntax for each command
- Parameter explanations
- Real-world examples
- Expected output

### "I want to deploy to production"

Read: [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md)
- Linux systemd setup
- macOS launchd setup
- Docker deployment
- Kubernetes deployment
- Monitoring and alerting
- Performance tuning

### "I want to understand how it works"

Read: [SCHEDULER_IMPLEMENTATION_SUMMARY.md](SCHEDULER_IMPLEMENTATION_SUMMARY.md)
- Architecture overview
- Component description
- Class hierarchy
- Data flow
- Storage format

### "I need detailed technical reference"

Read: [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)
- Complete feature documentation
- Installation instructions
- All CLI commands
- API reference
- Cron expression guide
- Troubleshooting

### "I want to use custom schedules"

1. Read: [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md) - Cron section
2. Run: `bug-finder schedule add <name> --site <url> --example <url> --frequency custom --cron "<expr>"`

### "Something isn't working"

1. Check logs: `bug-finder daemon logs`
2. Read: [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) - Troubleshooting section
3. Verify: `bug-finder schedule list` and `bug-finder daemon status`

---

## Command Quick Reference

### Schedule Management

```bash
# Create
bug-finder schedule add <name> --site <url> --example <url> --frequency <freq>

# List
bug-finder schedule list [--enabled]

# Show details
bug-finder schedule show <id>

# Enable/Disable
bug-finder schedule enable <id>
bug-finder schedule disable <id>

# Test
bug-finder schedule run <id>

# Remove
bug-finder schedule remove <id> [--yes]
```

### Daemon Control

```bash
# Start
bug-finder daemon start

# Stop
bug-finder daemon stop

# Status
bug-finder daemon status

# Logs
bug-finder daemon logs [--lines <n>]
```

---

## Key Information

### Storage Locations

| Item | Location |
|------|----------|
| Schedules | `~/.website-analyzer/schedules.json` |
| Logs | `~/.website-analyzer/logs/scheduler.log` |
| PID file | `~/.website-analyzer/scheduler.pid` |

### Frequency Options

| Frequency | Cron | When |
|-----------|------|------|
| `hourly` | `0 * * * *` | Top of every hour |
| `daily` | `0 2 * * *` | 2 AM UTC daily |
| `weekly` | `0 3 ? * MON` | 3 AM UTC Mondays |
| `custom` | User-defined | Custom cron |

### CLI Commands

| Command Group | Commands |
|---------------|----------|
| Schedule | add, list, show, enable, disable, remove, run |
| Daemon | start, stop, status, logs |

### System Integration

| Platform | Method | File |
|----------|--------|------|
| Linux | systemd | `website-analyzer-scheduler.service` |
| macOS | launchd | `com.website-analyzer.scheduler.plist` |
| Docker | Container | Dockerfile provided |
| Kubernetes | Manifest | K8s YAML in deployment guide |

---

## Features Summary

### Schedule Management
- Create named schedules
- Multiple frequency options (hourly, daily, weekly, custom)
- Custom cron expressions
- Enable/disable without deletion
- Tag schedules for organization
- Custom output directories
- Test execution immediately

### Daemon Operations
- Background execution with PID tracking
- Start/stop/status control
- Log streaming
- Error handling and recovery
- Resource management
- Performance monitoring

### Persistence
- JSON-based storage
- Configuration templates
- Last run tracking
- Next run calculation
- Atomic updates

### System Integration
- Linux systemd service
- macOS launchd agent
- Docker containerization
- Kubernetes orchestration
- Log rotation support

---

## File Statistics

### Implementation
- `scheduler.py`: 600+ lines, 4 main classes
- CLI modifications: 450+ lines, 11 commands
- Test suite: 500+ lines, 45+ tests
- Service files: 2 files

### Documentation
- 7 markdown files
- 2,500+ lines
- 100+ code examples
- Complete API reference

### Total
- 12 files created
- 1 file modified
- 1,550+ lines of code
- 2,500+ lines of documentation

---

## Getting Started Paths

### Path 1: Quick Start (15 minutes)
1. [SCHEDULER_README.md](SCHEDULER_README.md) - Overview
2. [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md) - Setup
3. Create first schedule and run

### Path 2: Comprehensive (1-2 hours)
1. [SCHEDULER_README.md](SCHEDULER_README.md) - Overview
2. [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) - Full guide
3. [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md) - Commands
4. Create and test schedules

### Path 3: Production Deployment (2-3 hours)
1. [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md) - Deployment
2. Choose platform (systemd/launchd/Docker/K8s)
3. Follow setup instructions
4. Configure monitoring and alerting

### Path 4: Development (4+ hours)
1. [SCHEDULER_IMPLEMENTATION_SUMMARY.md](SCHEDULER_IMPLEMENTATION_SUMMARY.md) - Architecture
2. [src/analyzer/scheduler.py](src/analyzer/scheduler.py) - Read source
3. [tests/test_scheduler.py](tests/test_scheduler.py) - Understand tests
4. Extend or customize as needed

---

## Common Tasks

### Create a Daily Scan
```bash
bug-finder schedule add "Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily
bug-finder daemon start
```

### Create an Hourly Check
```bash
bug-finder schedule add "Hourly Check" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency hourly \
  --max-pages 5
```

### Create a Custom Schedule
```bash
bug-finder schedule add "Every 6 Hours" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency custom \
  --cron "0 */6 * * *"
```

### Check Daemon Status
```bash
bug-finder daemon status
```

### View Logs
```bash
bug-finder daemon logs --lines 50
```

### Test a Schedule
```bash
bug-finder schedule run <schedule_id>
```

### Disable During Maintenance
```bash
bug-finder schedule disable <schedule_id>
# ... do maintenance ...
bug-finder schedule enable <schedule_id>
```

### Deploy to Linux
```bash
sudo cp src/analyzer/website-analyzer-scheduler.service /etc/systemd/user/
systemctl --user enable website-analyzer-scheduler
systemctl --user start website-analyzer-scheduler
```

### Deploy to macOS
```bash
cp src/analyzer/com.website-analyzer.scheduler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist
```

---

## Troubleshooting Quick Links

| Issue | Document | Section |
|-------|----------|---------|
| Installation errors | SCHEDULER_GUIDE.md | Installation |
| Command syntax | SCHEDULER_COMMAND_REFERENCE.md | Any command |
| Daemon won't start | SCHEDULER_GUIDE.md | Troubleshooting |
| Schedule not running | SCHEDULER_GUIDE.md | Troubleshooting |
| Production setup | SCHEDULER_DEPLOYMENT.md | Any platform |
| Performance | SCHEDULER_DEPLOYMENT.md | Performance Tuning |
| Monitoring | SCHEDULER_DEPLOYMENT.md | Monitoring and Alerting |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Scheduling | APScheduler |
| CLI | Typer + Rich |
| Storage | JSON files |
| Logging | Python logging |
| Testing | pytest |
| System Integration | systemd / launchd |
| Container | Docker |
| Orchestration | Kubernetes |

---

## API Quick Reference

### ScheduleManager
```python
manager = ScheduleManager()
manager.add_schedule(schedule)
manager.list_schedules(enabled_only=False)
manager.get_schedule(schedule_id)
manager.update_schedule(schedule)
manager.enable_schedule(schedule_id)
manager.disable_schedule(schedule_id)
manager.remove_schedule(schedule_id)
```

### ScheduledScanRunner
```python
runner = ScheduledScanRunner()
result = runner.run_schedule_sync(schedule_id)  # Returns dict with status
```

### SchedulerDaemon
```python
daemon = SchedulerDaemon()
daemon.start()
daemon.stop()
daemon.get_status()  # Returns dict with running status
daemon.reload_schedules()
```

---

## Contributing

To extend or contribute:
1. Read [SCHEDULER_IMPLEMENTATION_SUMMARY.md](SCHEDULER_IMPLEMENTATION_SUMMARY.md)
2. Review [src/analyzer/scheduler.py](src/analyzer/scheduler.py) source
3. Check [tests/test_scheduler.py](tests/test_scheduler.py) for examples
4. Add tests for new features
5. Update documentation

---

## Support Resources

### Included in This Package
- 7 comprehensive documentation files
- 45+ test cases
- 2 system integration files
- Example configurations
- Complete source code with comments

### Get Help
1. Check the relevant documentation file
2. Search for your issue in troubleshooting sections
3. Review test cases for examples
4. Check daemon logs for errors

---

## Version Information

- **Implementation Date**: December 2025
- **Status**: Production Ready
- **Python Version**: 3.11+
- **Main Dependencies**: APScheduler, Typer, Rich
- **Test Coverage**: 45+ tests
- **Documentation**: 2,500+ lines

---

## Next Steps

1. **Start here**: [SCHEDULER_README.md](SCHEDULER_README.md)
2. **Quick setup**: [SCHEDULER_QUICK_START.md](SCHEDULER_QUICK_START.md)
3. **Full reference**: [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)
4. **All commands**: [SCHEDULER_COMMAND_REFERENCE.md](SCHEDULER_COMMAND_REFERENCE.md)
5. **Production**: [SCHEDULER_DEPLOYMENT.md](SCHEDULER_DEPLOYMENT.md)

---

**Ready to get started?** Begin with [SCHEDULER_README.md](SCHEDULER_README.md) now!
