# Notification System - Quick Start Guide

## 5-Minute Setup

### Step 1: Configure Notifications (2 min)

```bash
python -m src.analyzer.cli notify configure
```

When prompted:
- **Console notifications?** Yes (for testing)
- **Email?** Yes (if you want email alerts)
- **Slack?** Yes (if you want Slack messages)
- **Webhook?** Yes (if you have custom integration)

### Step 2: Set Credentials (2 min)

Copy credentials template:
```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
```bash
# For Gmail
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# For Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 3: Test It (1 min)

```bash
python -m src.analyzer.cli notify test
```

You should see success confirmations for each backend.

---

## Common Tasks

### Test Specific Event Type

```bash
# Test scan failure notification
python -m src.analyzer.cli notify test --event scan_failed

# Test threshold alert
python -m src.analyzer.cli notify test --event threshold_alert

# Test new bugs found
python -m src.analyzer.cli notify test --event new_bugs_found
```

### View Configured Backends

```bash
python -m src.analyzer.cli notify list-backends
```

### Regenerate Example Config

```bash
python -m src.analyzer.cli notify generate-example
```

---

## Backend Setup - Choose Your Path

### Email (Gmail)

1. Enable 2-factor authentication on Gmail
2. Generate app password: https://myaccount.google.com/apppasswords
3. Set in `.env`:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

### Slack

1. Go to https://api.slack.com/messaging/webhooks
2. Create new incoming webhook
3. Choose channel to post to
4. Copy webhook URL
5. Set in `.env`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

### Custom Webhook

1. Set endpoint URL in `notifications.json`
2. Set authentication in `.env` (if needed)
3. Test with:
   ```bash
   python -m src.analyzer.cli notify test --event scan_completed
   ```

---

## What Gets Notified?

By default, notifications are sent for:

| Event | When | Backends |
|-------|------|----------|
| **scan_completed** | Scan finishes | All |
| **scan_failed** | Scan has error | Email, Slack, Custom |
| **new_bugs_found** | Regression detected | All |
| **bugs_fixed** | Bugs are resolved | All |
| **threshold_alert** | Too many bugs | Email, Slack, Custom |

You can customize which events go to which backend in `notifications.json`.

---

## Configuration File Location

Default: `notifications.json` in current directory

Specify different location:
```bash
python -m src.analyzer.cli notify test --config /path/to/config.json
```

---

## Troubleshooting Quick Fixes

### Email not working?
```bash
# Check your credentials
echo "SMTP_HOST: $SMTP_HOST"
echo "SMTP_USER: $SMTP_USER"

# Make sure .env is loaded
source .env

# Try again
python -m src.analyzer.cli notify test --event scan_completed
```

### Slack not working?
```bash
# Test webhook with curl
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL

# Should respond with "ok"
```

### Missing configuration?
```bash
# Check if config exists
cat notifications.json

# Not found? Generate it
python -m src.analyzer.cli notify generate-example
cp notifications.example.json notifications.json

# Then run configure
python -m src.analyzer.cli notify configure
```

---

## Using in Python Code

```python
from src.analyzer.notifications import (
    NotificationManager,
    ScanCompletedEvent,
)
import asyncio

async def notify_scan_done():
    # Initialize manager
    manager = NotificationManager("notifications.json")

    # Create event
    event = ScanCompletedEvent(
        site_name="example.com",
        pages_scanned=150,
        bugs_found=42,
        duration_seconds=125.5,
        output_file="/path/to/results.json",
        report_url="https://example.com/reports"
    )

    # Send
    results = await manager.notify(event)
    print(f"Sent to: {list(results.keys())}")

# Run it
asyncio.run(notify_scan_done())
```

---

## Event Types Reference

### ScanCompletedEvent
```python
ScanCompletedEvent(
    site_name="example.com",
    pages_scanned=150,
    bugs_found=42,
    duration_seconds=125.5,
    output_file="/path/to/results.json",
    report_url="https://example.com/reports"
)
```

### ScanFailedEvent
```python
ScanFailedEvent(
    site_name="example.com",
    error_message="Connection timeout",
    error_details="Server stopped responding",
    duration_seconds=300.0
)
```

### NewBugsFoundEvent
```python
NewBugsFoundEvent(
    site_name="example.com",
    new_bugs_count=15,
    previous_bugs_count=27,
    new_bug_urls=["https://example.com/page1"]
)
```

### BugsFixedEvent
```python
BugsFixedEvent(
    site_name="example.com",
    fixed_bugs_count=10,
    remaining_bugs_count=5,
    fixed_bug_urls=["https://example.com/fixed1"]
)
```

### ThresholdAlertEvent
```python
ThresholdAlertEvent(
    site_name="example.com",
    threshold=50,
    actual_count=127,
    exceeded_by=77,
    severity="critical"
)
```

---

## FAQ

**Q: Can I disable specific backends?**
A: Yes, set `"enabled": false` in `notifications.json` for that backend.

**Q: Can I send to multiple Slack channels?**
A: Create multiple Slack backends with different webhook URLs:
```json
{
  "slack_dev": {"webhook_url": "${SLACK_DEV_WEBHOOK}"},
  "slack_qa": {"webhook_url": "${SLACK_QA_WEBHOOK}"}
}
```

**Q: Can I use different events for different backends?**
A: Yes, set `"events"` in each backend to filter:
```json
{
  "email": {"events": ["scan_failed", "threshold_alert"]},
  "slack": {"events": ["scan_completed"]}
}
```

**Q: Are credentials safe?**
A: Yes - use `.env` file (add to `.gitignore`) and environment variable substitution.

**Q: Can I use this without email/Slack?**
A: Yes - console backend works without any credentials.

---

## Next Steps

1. ✓ Run `notify configure` to set up
2. ✓ Create `.env` with credentials
3. ✓ Run `notify test` to verify
4. ✓ Check `NOTIFICATIONS.md` for detailed docs
5. ✓ Integrate into your scan workflows

---

## Support Resources

- **Full Documentation:** See `NOTIFICATIONS.md`
- **Technical Details:** See `NOTIFICATION_SUMMARY.md`
- **Test Cases:** See `tests/test_notifications.py`
- **Examples:** See `notifications.example.json`

---

**Ready to get notified about your scans!** 🎉

```bash
python -m src.analyzer.cli notify test
```
