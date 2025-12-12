# Scheduler Deployment and System Integration

## Deployment Overview

The scheduler can be deployed in multiple ways:

1. **Manual CLI** - Run commands directly
2. **Daemon mode** - Long-running background process
3. **systemd** (Linux) - System-managed service
4. **launchd** (macOS) - User launch agent
5. **Docker** - Containerized deployment

## Manual CLI Deployment

Simplest setup - run commands as needed.

```bash
# Create a schedule
bug-finder schedule add "Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily

# Test it
bug-finder schedule run schedule_id

# For one-time runs, use cron to trigger the command
# Example crontab entry:
# 0 2 * * * bug-finder schedule run schedule_id
```

**Pros:**
- Simple, no additional setup
- Easy to debug
- Manual control

**Cons:**
- Requires external cron/scheduling
- Manual monitoring needed
- Less robust error handling

---

## Daemon Mode Deployment

Long-running background process managed by the CLI.

### Installation

```bash
# Install dependencies
pip install apscheduler

# Create a schedule
bug-finder schedule add "Daily Scan" \
  --site "https://example.com" \
  --example "https://example.com/page" \
  --frequency daily

# Start daemon in background
bug-finder daemon start

# Check status
bug-finder daemon status

# View logs
tail -f ~/.website-analyzer/logs/scheduler.log
```

### Management

```bash
# Check if running
bug-finder daemon status

# View logs
bug-finder daemon logs --lines 100

# Stop daemon
bug-finder daemon stop

# Restart
bug-finder daemon stop
bug-finder daemon start
```

**Pros:**
- Automatic scheduling (no cron needed)
- Integrated logging
- Easy enable/disable of schedules
- Built-in status monitoring

**Cons:**
- Needs manual restart after system reboot
- Requires APScheduler library
- Not integrated with OS services

---

## Linux (systemd) Deployment

System-managed service that starts on boot.

### Installation

```bash
# 1. Create a Python virtual environment for the app
python3.11 -m venv /opt/website-analyzer/.venv
source /opt/website-analyzer/.venv/bin/activate
pip install apscheduler

# 2. Copy service file
sudo cp src/analyzer/website-analyzer-scheduler.service \
  /etc/systemd/user/

# 3. Update the service file with your paths
sudo nano /etc/systemd/user/website-analyzer-scheduler.service
# Edit: ExecStart path, User, paths, etc.

# 4. Reload systemd
systemctl --user daemon-reload

# 5. Enable to start on login
systemctl --user enable website-analyzer-scheduler

# 6. Start the service
systemctl --user start website-analyzer-scheduler

# 7. Verify it's running
systemctl --user status website-analyzer-scheduler
```

### Service File Customization

Edit `/etc/systemd/user/website-analyzer-scheduler.service`:

```ini
[Unit]
Description=Website Analyzer Scheduler Daemon
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/website-analyzer
ExecStart=/home/your_username/website-analyzer/.venv/bin/python3 \
  -c "from src.analyzer.scheduler import SchedulerDaemon; SchedulerDaemon().start()"
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### Systemd Commands

```bash
# Start
systemctl --user start website-analyzer-scheduler

# Stop
systemctl --user stop website-analyzer-scheduler

# Restart
systemctl --user restart website-analyzer-scheduler

# Status
systemctl --user status website-analyzer-scheduler

# Enable on login
systemctl --user enable website-analyzer-scheduler

# Disable on login
systemctl --user disable website-analyzer-scheduler

# View logs
journalctl --user -u website-analyzer-scheduler -f

# View last 100 lines
journalctl --user -u website-analyzer-scheduler -n 100
```

### System-Wide Deployment (requires sudo)

```bash
# For system-wide installation
sudo cp src/analyzer/website-analyzer-scheduler.service \
  /etc/systemd/system/

# Edit for system user (www-data, nginx, etc.)
sudo nano /etc/systemd/system/website-analyzer-scheduler.service

sudo systemctl daemon-reload
sudo systemctl enable website-analyzer-scheduler
sudo systemctl start website-analyzer-scheduler

# Monitor
sudo journalctl -u website-analyzer-scheduler -f
```

---

## macOS (launchd) Deployment

User launch agent that starts on login.

### Installation

```bash
# 1. Copy plist file
cp src/analyzer/com.website-analyzer.scheduler.plist \
  ~/Library/LaunchAgents/

# 2. Edit plist if needed (paths, logging)
nano ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# 3. Load the agent
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# 4. Verify
launchctl list | grep website-analyzer

# 5. Check logs
log stream --predicate 'eventMessage contains[c] "website-analyzer"' --level debug
```

### Plist File Customization

Edit `~/Library/LaunchAgents/com.website-analyzer.scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.website-analyzer.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3.11</string>
        <string>-c</string>
        <string>from src.analyzer.scheduler import SchedulerDaemon; SchedulerDaemon().start()</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/your_username/.website-analyzer/logs/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/your_username/.website-analyzer/logs/scheduler.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>/Users/your_username</string>
    </dict>
</dict>
</plist>
```

### launchctl Commands

```bash
# Load agent (start on login)
launchctl load ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Unload agent (stop on login)
launchctl unload ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Start immediately (even if not at login)
launchctl start com.website-analyzer.scheduler

# Stop immediately
launchctl stop com.website-analyzer.scheduler

# Check status
launchctl list | grep website-analyzer

# View logs
log stream --predicate 'eventMessage contains[c] "website-analyzer"' --level debug

# View last 100 lines
log show --last 1h --predicate 'eventMessage contains[c] "website-analyzer"'
```

---

## Docker Deployment

Run scheduler in a Docker container.

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

# Copy app
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir apscheduler

# Create logs directory
RUN mkdir -p /root/.website-analyzer/logs

# Run scheduler daemon
CMD ["python", "-c", "from src.analyzer.scheduler import SchedulerDaemon; SchedulerDaemon().start()"]
```

### Build and Run

```bash
# Build image
docker build -t website-analyzer-scheduler .

# Run container
docker run -d \
  --name website-analyzer-scheduler \
  -v ~/.website-analyzer:/root/.website-analyzer \
  website-analyzer-scheduler

# Check status
docker ps

# View logs
docker logs -f website-analyzer-scheduler

# Stop
docker stop website-analyzer-scheduler

# Restart
docker restart website-analyzer-scheduler
```

### Docker Compose

```yaml
version: '3.8'

services:
  scheduler:
    build: .
    container_name: website-analyzer-scheduler
    volumes:
      - ~/.website-analyzer:/root/.website-analyzer
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Run with: `docker-compose up -d`

---

## Kubernetes Deployment

Run scheduler in Kubernetes cluster.

### Kubernetes Manifest

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
data:
  schedules.json: |
    {
      "schedules": [
        {
          "id": "daily-scan",
          "name": "Daily Scan",
          "site_url": "https://example.com",
          "example_url": "https://example.com/page",
          "frequency": "daily",
          "max_pages": 1000,
          "enabled": true
        }
      ]
    }

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-analyzer-scheduler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: scheduler
  template:
    metadata:
      labels:
        app: scheduler
    spec:
      containers:
      - name: scheduler
        image: website-analyzer-scheduler:latest
        imagePullPolicy: Always
        volumeMounts:
        - name: config
          mountPath: /root/.website-analyzer
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: scheduler-config

---
apiVersion: v1
kind: Service
metadata:
  name: scheduler-service
spec:
  selector:
    app: scheduler
  ports:
  - port: 8080
    targetPort: 8080
```

Deploy with: `kubectl apply -f scheduler-deployment.yaml`

---

## Performance Tuning

### Resource Limits

#### Daemon Mode

Set resource limits in systemd:

```ini
[Service]
MemoryMax=512M
CPUQuota=50%
```

#### Docker

```bash
docker run -d \
  --memory=512m \
  --cpus=0.5 \
  website-analyzer-scheduler
```

#### Kubernetes

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Optimization Tips

1. **Stagger schedules**: Don't run multiple full scans simultaneously
2. **Limit concurrent pages**: Use `--max-pages` for heavy schedules
3. **Off-peak scheduling**: Run large scans during low-traffic times
4. **Archive old logs**: Implement log rotation

### Log Rotation

Create `/etc/logrotate.d/website-analyzer`:

```
~/.website-analyzer/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 nobody adm
}
```

---

## Monitoring and Alerting

### Health Checks

```bash
#!/bin/bash
# Check if daemon is running

STATUS=$(python3 -c "
from src.analyzer.scheduler import SchedulerDaemon
daemon = SchedulerDaemon()
status = daemon.get_status()
print('running' if status['running'] else 'stopped')
")

if [ "$STATUS" = "stopped" ]; then
    # Send alert
    echo "Scheduler is stopped!" | mail -s "Alert" admin@example.com
fi
```

### Log Monitoring

```bash
# Watch logs for errors
tail -f ~/.website-analyzer/logs/scheduler.log | grep ERROR

# Count errors in logs
grep ERROR ~/.website-analyzer/logs/scheduler.log | wc -l
```

### Metrics

Key metrics to monitor:
- Daemon uptime
- Schedule success/failure rates
- Pages crawled per schedule
- Execution duration
- Error frequency

---

## Backup and Recovery

### Schedule Backup

```bash
# Backup schedules
cp ~/.website-analyzer/schedules.json ~/.website-analyzer/schedules.json.backup

# Restore from backup
cp ~/.website-analyzer/schedules.json.backup ~/.website-analyzer/schedules.json
```

### Log Cleanup

```bash
# Archive old logs
gzip ~/.website-analyzer/logs/scheduler.log
mv ~/.website-analyzer/logs/scheduler.log.gz \
   ~/.website-analyzer/logs/scheduler.log.$(date +%Y%m%d).gz

# Remove logs older than 30 days
find ~/.website-analyzer/logs -name "*.gz" -mtime +30 -delete
```

---

## Troubleshooting Deployment

### systemd Service Won't Start

```bash
# Check service status
systemctl --user status website-analyzer-scheduler

# View detailed logs
journalctl --user -u website-analyzer-scheduler -n 50

# Test the service manually
systemctl --user start website-analyzer-scheduler --verbose
```

### launchd Agent Won't Load

```bash
# Verify plist syntax
plutil -lint ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Load with error output
launchctl load -w ~/Library/LaunchAgents/com.website-analyzer.scheduler.plist

# Check for errors
log show --last 1h --predicate 'eventMessage contains[c] "website-analyzer"'
```

### Docker Container Crashes

```bash
# Check logs
docker logs website-analyzer-scheduler

# Inspect container
docker inspect website-analyzer-scheduler

# Run interactively for debugging
docker run -it website-analyzer-scheduler /bin/bash
```

---

## Best Practices

1. **Use version control** for schedule configs
2. **Regular backups** of schedules.json
3. **Monitor logs** for errors and failures
4. **Stagger schedules** to avoid resource spikes
5. **Test before production** deployment
6. **Document** custom cron expressions
7. **Review logs** periodically
8. **Plan for maintenance** windows
9. **Keep APScheduler updated**
10. **Archive old results** to save disk space
