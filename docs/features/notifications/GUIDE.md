# Bug Finder Notification System

The notification system provides flexible, pluggable backends for alerting you about scan events across multiple channels (email, Slack, webhooks, console).

## Quick Start

### 1. Generate Configuration

```bash
python -m src.analyzer.cli notify configure
```

This interactive wizard guides you through setting up email, Slack, and/or webhook notifications.

### 2. Test Your Setup

```bash
python -m src.analyzer.cli notify test
```

Sends test notifications to all configured backends to verify settings.

### 3. Use in Your Scans

The notification system integrates with your scan workflows and sends alerts based on configured events.

## Notification Backends

### Console Backend
Prints notifications to the terminal (useful for testing and CI/CD pipelines).

**Configuration:**
```json
{
  "type": "console",
  "enabled": true,
  "events": []
}
```

**Features:**
- No credentials needed
- Perfect for testing
- Formatted with rich colors

---

### Email Backend
Send notifications via SMTP with HTML formatting.

**Configuration:**
```json
{
  "type": "email",
  "enabled": true,
  "events": ["scan_completed", "scan_failed", "threshold_alert"],
  "smtp_host": "${SMTP_HOST}",
  "smtp_port": 587,
  "smtp_user": "${SMTP_USER}",
  "smtp_password": "${SMTP_PASSWORD}",
  "from_address": "bug-finder@example.com",
  "to_addresses": ["qa-team@example.com"],
  "use_tls": true
}
```

**Environment Variables:**
- `SMTP_HOST` - SMTP server (e.g., smtp.gmail.com)
- `SMTP_USER` - Email address or username
- `SMTP_PASSWORD` - Password or app-specific password
- `SMTP_PORT` - Port number (default: 587)

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate app-specific password at https://myaccount.google.com/apppasswords
3. Use app password as `SMTP_PASSWORD`

**Features:**
- HTML-formatted emails
- Multiple recipient support
- Rich formatting with scan statistics

---

### Slack Backend
Send rich notifications to Slack channels.

**Configuration:**
```json
{
  "type": "slack",
  "enabled": true,
  "events": ["scan_completed", "new_bugs_found", "threshold_alert"],
  "webhook_url": "${SLACK_WEBHOOK_URL}"
}
```

**Environment Variables:**
- `SLACK_WEBHOOK_URL` - Incoming Webhook URL

**Slack Setup:**
1. Go to https://api.slack.com/messaging/webhooks
2. Click "Create New App" or use existing
3. Enable "Incoming Webhooks"
4. Create a new webhook for your channel
5. Copy the webhook URL

**Features:**
- Formatted messages with event details
- Color-coded by event type
- Emojis for quick scanning
- Click-through to reports

---

### Webhook Backend
Send JSON payloads to custom HTTP endpoints.

**Configuration:**
```json
{
  "type": "webhook",
  "enabled": true,
  "events": ["scan_completed", "threshold_alert"],
  "webhook_url": "https://api.example.com/webhooks/bug-finder",
  "headers": {
    "Authorization": "Bearer ${WEBHOOK_TOKEN}",
    "Content-Type": "application/json"
  }
}
```

**Environment Variables:**
- Any variable referenced as `${VAR_NAME}` is substituted from environment

**Payload Structure:**
```json
{
  "event": "scan_completed",
  "timestamp": "2023-12-01T12:00:00.000000",
  "site_url": "https://example.com",
  "site_name": "example.com",
  "scan_id": "scan_20231201_120000",
  "message": "Scan Results for example.com:\n  Pages scanned: 150\n...",
  "data": {},
  "event_data": {
    "pages_scanned": 150,
    "bugs_found": 42,
    "duration_seconds": 125.5,
    "output_file": "/path/to/results.json",
    "report_url": "https://example.com/reports/scan_20231201"
  }
}
```

**Features:**
- Custom headers and authentication
- Environment variable substitution
- Full event metadata in payload

---

## Event Types

### scan_completed
Emitted when a scan finishes successfully.

**Data:**
- `pages_scanned` - Number of pages scanned
- `bugs_found` - Total bugs discovered
- `duration_seconds` - Scan execution time
- `output_file` - Path to results file
- `report_url` - URL to view report

**Example Template:**
```
Subject: Bug Scan Complete - {site_name}

Scan Results:
- Pages scanned: {pages_scanned}
- Bugs found: {bugs_found}
- Duration: {duration_seconds:.1f} seconds

Output saved to: {output_file}
Report URL: {report_url}
```

---

### scan_failed
Emitted when a scan encounters an error.

**Data:**
- `error_message` - Brief error description
- `error_details` - Technical details
- `duration_seconds` - Time before failure

**Example Template:**
```
Subject: Bug Scan Failed - {site_name}

Scan failed: {error_message}
Duration: {duration_seconds:.1f} seconds

Details:
{error_details}
```

---

### new_bugs_found
Emitted when comparing scans shows new bugs.

**Data:**
- `new_bugs_count` - Number of newly discovered bugs
- `previous_bugs_count` - Bugs from previous scan
- `new_bug_urls` - List of affected page URLs

---

### bugs_fixed
Emitted when bugs are fixed between scans.

**Data:**
- `fixed_bugs_count` - Number of fixed bugs
- `remaining_bugs_count` - Still-open bug count
- `fixed_bug_urls` - List of fixed page URLs

---

### threshold_alert
Emitted when bug count exceeds configured threshold.

**Data:**
- `threshold` - Configured threshold
- `actual_count` - Actual bug count
- `exceeded_by` - How much threshold was exceeded
- `severity` - "warning" or "critical"

---

## Configuration Files

### Example Configuration (notifications.example.json)

```json
{
  "enabled": true,
  "backends": {
    "console": {
      "type": "console",
      "enabled": true,
      "events": []
    },
    "email_production": {
      "type": "email",
      "enabled": false,
      "events": ["scan_completed", "scan_failed", "threshold_alert"],
      "smtp_host": "${SMTP_HOST}",
      "smtp_port": 587,
      "smtp_user": "${SMTP_USER}",
      "smtp_password": "${SMTP_PASSWORD}",
      "from_address": "bug-finder@example.com",
      "to_addresses": ["qa-team@example.com"]
    },
    "slack_main": {
      "type": "slack",
      "enabled": false,
      "events": ["scan_completed", "new_bugs_found"],
      "webhook_url": "${SLACK_WEBHOOK_URL}"
    }
  }
}
```

### Environment File (.env)

```bash
# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Custom Webhook
WEBHOOK_TOKEN=your-secret-token
```

## CLI Commands

### Initialize Configuration Wizard

```bash
python -m src.analyzer.cli notify configure
```

Interactive setup for all backends. Creates `notifications.json`.

**Options:**
- `--output, -o` - Custom config file path

---

### Test Notification

```bash
python -m src.analyzer.cli notify test
```

Send test notification using sample event data.

**Options:**
- `--event, -e` - Event type to test (default: scan_completed)
  - `scan_completed`
  - `scan_failed`
  - `new_bugs_found`
  - `bugs_fixed`
  - `threshold_alert`
- `--config, -c` - Path to configuration file

**Examples:**
```bash
# Test scan completion notification
python -m src.analyzer.cli notify test

# Test threshold alert
python -m src.analyzer.cli notify test --event threshold_alert

# Test with specific config
python -m src.analyzer.cli notify test --config my-notifications.json
```

---

### List Configured Backends

```bash
python -m src.analyzer.cli notify list-backends
```

Display all configured notification backends and their status.

**Options:**
- `--config, -c` - Path to configuration file

---

### Generate Example Configuration

```bash
python -m src.analyzer.cli notify generate-example
```

Create template configuration with all backends and options.

**Options:**
- `--output, -o` - Output path (default: notifications.example.json)

---

## Usage Examples

### Email + Slack Setup

```bash
# 1. Generate configuration
python -m src.analyzer.cli notify configure

# 2. When prompted, choose email and Slack
# 3. Configure your SMTP and webhook details

# 4. Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your credentials

# 5. Test notifications
python -m src.analyzer.cli notify test
python -m src.analyzer.cli notify test --event threshold_alert
```

### Multiple Email Recipients

Edit `notifications.json`:

```json
{
  "email_production": {
    "type": "email",
    "to_addresses": [
      "qa-lead@example.com",
      "dev-team@example.com",
      "incidents@example.com"
    ]
  }
}
```

### Alert-Only Configuration

```json
{
  "backends": {
    "slack_alerts": {
      "type": "slack",
      "enabled": true,
      "events": ["scan_failed", "threshold_alert"],
      "webhook_url": "${SLACK_ALERTS_WEBHOOK_URL}"
    }
  }
}
```

Only notifications on critical events (failures and threshold breaches).

### Custom Webhook Integration

```json
{
  "webhook_custom": {
    "type": "webhook",
    "enabled": true,
    "events": ["scan_completed"],
    "webhook_url": "https://my-api.example.com/webhooks/scans",
    "headers": {
      "Authorization": "Bearer sk_live_12345",
      "X-API-Version": "v2"
    }
  }
}
```

## Security Best Practices

1. **Never commit credentials** to version control
   - Use `.env` file (add to `.gitignore`)
   - Reference credentials with `${VAR_NAME}` syntax

2. **Use app-specific passwords**
   - Gmail: Generate at myaccount.google.com/apppasswords
   - Don't use main account password

3. **Restrict webhook access**
   - Use authentication tokens
   - Use HTTPS only
   - Validate source IPs if possible

4. **Protect configuration files**
   - `.env` should be readable only by user
   - `notifications.json` may contain template info but not credentials

5. **Rotate credentials regularly**
   - Update passwords every 90 days
   - Regenerate API tokens annually

## Troubleshooting

### Emails not sending

**Problem:** Email notifications fail silently

**Solutions:**
1. Check environment variables:
   ```bash
   echo $SMTP_HOST
   echo $SMTP_USER
   ```

2. Enable logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Verify SMTP settings:
   - Port 587 for TLS
   - Port 465 for SSL
   - Gmail requires app-specific password with 2FA

4. Check firewall:
   - SMTP port not blocked by ISP/firewall

### Slack notifications not arriving

**Problem:** Webhook calls fail or messages don't appear

**Solutions:**
1. Verify webhook URL:
   ```bash
   python -m src.analyzer.cli notify test --event scan_completed
   ```

2. Check webhook format:
   - Must be valid Slack incoming webhook URL
   - Should start with `https://hooks.slack.com/`

3. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test"}' \
     $SLACK_WEBHOOK_URL
   ```

### Configuration not loading

**Problem:** `notify test` shows "No backends configured"

**Solutions:**
1. Check file exists:
   ```bash
   ls -la notifications.json
   ```

2. Validate JSON:
   ```bash
   python -m json.tool notifications.json
   ```

3. Check file permissions:
   ```bash
   chmod 644 notifications.json
   ```

### Environment variables not substituting

**Problem:** Webhook headers contain literal `${VAR_NAME}`

**Solutions:**
1. Set environment variable:
   ```bash
   export WEBHOOK_TOKEN="your-token"
   ```

2. Verify it's set:
   ```bash
   echo $WEBHOOK_TOKEN
   ```

3. Use format `${VAR_NAME}` exactly (with braces)

## API Reference

### Python Integration

```python
from src.analyzer.notifications import (
    NotificationManager,
    ScanCompletedEvent,
    ScanFailedEvent,
)
import asyncio

# Initialize manager
manager = NotificationManager("notifications.json")

# Create event
event = ScanCompletedEvent(
    site_name="example.com",
    site_url="https://example.com",
    scan_id="scan_001",
    pages_scanned=150,
    bugs_found=42,
    duration_seconds=125.5,
    output_file="/path/to/results.json",
    report_url="https://example.com/reports"
)

# Send notification
async def send():
    results = await manager.notify(event)
    for backend_name, success in results.items():
        print(f"{backend_name}: {'OK' if success else 'FAILED'}")

asyncio.run(send())
```

### Event Classes

All event classes inherit from `ScanEvent` and can be created with:

```python
from src.analyzer.notifications import (
    ScanCompletedEvent,
    ScanFailedEvent,
    NewBugsFoundEvent,
    BugsFixedEvent,
    ThresholdAlertEvent,
)

# Common fields
event = ScanCompletedEvent(
    site_url="https://example.com",      # Required
    site_name="example.com",              # Optional
    scan_id="scan_123",                   # Optional
    timestamp="2023-12-01T12:00:00",      # Auto-generated if not provided
    # ... event-specific fields
)
```

### Template Customization

Override templates in configuration:

```python
from src.analyzer.notifications import NotificationTemplate

# Add custom template
NotificationTemplate.TEMPLATES["scan_completed"]["email"] = """
Subject: Custom: {site_name} scan done!

Your scan of {site_name} found {bugs_found} bugs.
Visit: {report_url}
"""
```

## Integration with Scan Workflow

The notification system is designed to integrate with scan completion:

```python
from src.analyzer.notifications import (
    NotificationManager,
    ScanCompletedEvent,
)

async def run_scan_with_notifications():
    # ... run scan ...

    # Create completion event
    event = ScanCompletedEvent(
        site_name=site_url,
        pages_scanned=len(results),
        bugs_found=bug_count,
        duration_seconds=scan_duration,
        output_file=output_path,
        report_url=report_url,
    )

    # Send notifications
    manager = NotificationManager()
    results = await manager.notify(event)
```

## Performance Considerations

- **Console backend**: Immediate, no overhead
- **Email backend**: 1-5 seconds per email (depends on SMTP)
- **Slack backend**: <1 second (async HTTP call)
- **Webhook backend**: <1 second (async HTTP call)

For long scan processes, notifications are sent asynchronously and don't block scan execution.

## Future Enhancements

Potential additions to notification system:

- SMS/text message alerts
- PagerDuty integration
- Microsoft Teams support
- Database logging
- Notification templating with Jinja2
- Delivery retry logic
- Rate limiting
- Notification history

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review example configuration files
3. Test with console backend first
4. Check logs for detailed error messages

---

**Last Updated:** 2023-12-01
**Version:** 1.0
