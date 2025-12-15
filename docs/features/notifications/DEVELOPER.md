# Notification System - Developer Guide

This guide covers extending the notification system with new backends, event types, or features.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    NotificationManager                       │
│  (Orchestrates sending to multiple backends)                 │
└────────┬──────────────────┬──────────────────┬───────────────┘
         │                  │                  │
    ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
    │ Email   │        │ Slack   │       │ Webhook │
    │Backend  │        │Backend  │       │Backend  │
    └────┬────┘        └────┬────┘       └────┬────┘
         │                  │                  │
         └──────────┬───────┴─────────────────┘
                    │
            ┌───────▼──────────┐
            │  Backends send   │
            │  notifications   │
            └──────────────────┘

         ↓ (for each event)

    ┌────────────────────────┐
    │ NotificationTemplate   │
    │ (Renders message text) │
    └────────────────────────┘
```

## Creating a Custom Backend

### Step 1: Extend NotificationBackend Class

```python
from src.analyzer.notifications import NotificationBackend, ScanEvent

class MyCustomBackend(NotificationBackend):
    """Send notifications via MyService API."""

    async def send(self, event: ScanEvent, template: str) -> bool:
        """Send notification.

        Args:
            event: The event being sent
            template: Rendered template text

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get configuration
            api_key = self._substitute_env_vars(
                self.config.get("api_key", "")
            )
            endpoint = self._substitute_env_vars(
                self.config.get("endpoint", "")
            )

            if not api_key or not endpoint:
                logger.error("Missing API configuration")
                return False

            # Send notification
            response = requests.post(
                endpoint,
                json={"message": template},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            response.raise_for_status()

            logger.info("Notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
```

### Step 2: Register Backend

In `NotificationManager._initialize_backends()`:

```python
BACKEND_TYPES = {
    "console": ConsoleBackend,
    "email": EmailBackend,
    "slack": SlackBackend,
    "webhook": WebhookBackend,
    "myservice": MyCustomBackend,  # Add this
}
```

### Step 3: Add to Configuration

```json
{
  "backends": {
    "myservice_prod": {
      "type": "myservice",
      "enabled": true,
      "events": ["scan_completed", "threshold_alert"],
      "endpoint": "https://api.myservice.com/notify",
      "api_key": "${MYSERVICE_API_KEY}"
    }
  }
}
```

### Step 4: Test

```python
from src.analyzer.notifications import NotificationManager, ScanCompletedEvent

manager = NotificationManager()
manager.add_backend("myservice_test", "myservice", {
    "enabled": True,
    "endpoint": "https://api.myservice.com/notify",
    "api_key": "${MYSERVICE_API_KEY}"
})

event = ScanCompletedEvent(site_name="test.com", pages_scanned=100, bugs_found=10)
results = await manager.notify(event)
```

---

## Creating Custom Event Types

### Step 1: Define Event Class

```python
from dataclasses import dataclass, field
from typing import Any, Dict
from src.analyzer.notifications import ScanEvent

@dataclass
class PerformanceAlertEvent(ScanEvent):
    """Emitted when page performance degrades."""
    event_type: str = "performance_alert"
    pages_slow: int = 0
    avg_load_time: float = 0.0
    threshold_seconds: float = 3.0
    affected_urls: list = field(default_factory=list)
```

### Step 2: Add Templates

```python
# In NotificationTemplate.TEMPLATES
"performance_alert": {
    "console": """Subject: Performance Alert - {site_name}

Performance has degraded on {site_name}:
  Pages with slow load: {pages_slow}
  Average load time: {avg_load_time:.2f}s
  Threshold: {threshold_seconds}s

Affected pages:
{affected_urls_list}
""",
    "slack": "Performance alert on {site_name}: {pages_slow} pages slow (>{threshold_seconds}s)",
    "email": """Subject: ALERT - Performance Degradation - {site_name}

Performance has degraded on {site_name}.

Details:
- Pages with slow load: {pages_slow}
- Average load time: {avg_load_time:.2f} seconds
- Threshold: {threshold_seconds} seconds

Affected Pages:
{affected_urls_list}

Action required to investigate and optimize page load times.
""",
}
```

### Step 3: Use Event

```python
from src.analyzer.notifications import NotificationManager
from my_module import PerformanceAlertEvent

async def check_performance():
    event = PerformanceAlertEvent(
        site_name="example.com",
        pages_slow=25,
        avg_load_time=4.5,
        threshold_seconds=3.0,
        affected_urls=["https://example.com/slow-page"]
    )

    manager = NotificationManager()
    await manager.notify(event)
```

---

## Advanced: Custom Template Rendering

### Override Template Rendering

```python
class CustomSlackBackend(SlackBackend):
    """Slack backend with custom formatting."""

    def _build_slack_payload(self, event, template):
        """Override to customize Slack message format."""
        # Get base payload
        payload = super()._build_slack_payload(event, template)

        # Customize
        payload["attachments"][0]["footer"] = "Bug Finder v2.0"
        payload["attachments"][0]["image_url"] = "https://example.com/logo.png"

        return payload
```

### Custom Template Variables

```python
class MyBackend(NotificationBackend):
    """Backend with custom template variables."""

    async def send(self, event, template):
        # Add custom variables
        custom_vars = {
            "custom_field": "custom_value",
            "timestamp_formatted": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Render with custom variables
        # (template rendering would need to be enhanced)
        message = template.format(**custom_vars)

        # Send...
```

---

## Testing Custom Backends

### Unit Test Example

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestMyCustomBackend:

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Test successful notification."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200

            backend = MyCustomBackend({
                "enabled": True,
                "api_key": "test_key",
                "endpoint": "https://api.test.com/notify"
            })

            event = ScanCompletedEvent(site_name="test.com")
            result = await backend.send(event, "Test message")

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure(self):
        """Test failed notification."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            backend = MyCustomBackend({
                "enabled": True,
                "api_key": "test_key",
                "endpoint": "https://api.test.com/notify"
            })

            event = ScanCompletedEvent(site_name="test.com")
            result = await backend.send(event, "Test message")

            assert result is False
```

---

## Configuration Best Practices

### Secrets Management

**Good:**
```json
{
  "api_key": "${MY_SERVICE_API_KEY}",
  "endpoint": "https://api.myservice.com/notify"
}
```

**Bad:**
```json
{
  "api_key": "sk_live_secret123456",
  "endpoint": "https://api.myservice.com/notify"
}
```

### Documentation in Config

```json
{
  "myservice": {
    "type": "myservice",
    "description": "Send to MyService API",
    "enabled": false,
    "api_key": "${MY_SERVICE_API_KEY}",
    "endpoint": "https://api.myservice.com/notify",
    "notes": "Get API key from https://myservice.com/settings/api"
  }
}
```

---

## Error Handling Patterns

### Graceful Degradation

```python
async def send(self, event, template):
    try:
        response = requests.post(...)
        response.raise_for_status()
        return True
    except requests.Timeout:
        logger.warning("Timeout sending notification")
        # Don't block scan, log and continue
        return False
    except requests.RequestException as e:
        logger.error(f"Failed to send: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
```

### Validation

```python
async def send(self, event, template):
    # Validate required config
    required = ["api_key", "endpoint"]
    for field in required:
        if not self.config.get(field):
            logger.error(f"Missing required config: {field}")
            return False

    # Validate event type
    if not self.supports_event(event.event_type):
        logger.debug(f"Backend doesn't support {event.event_type}")
        return True  # Not an error, just filtered

    # Send...
```

---

## Performance Optimization

### Async Operations

```python
import asyncio

class BatchedWebhookBackend(WebhookBackend):
    """Batch multiple notifications."""

    def __init__(self, config):
        super().__init__(config)
        self.queue = asyncio.Queue()
        self.batch_size = config.get("batch_size", 10)
        self.batch_timeout = config.get("batch_timeout", 5.0)

    async def send(self, event, template):
        """Queue notification for batching."""
        await self.queue.put((event, template))

        # Check if we should flush
        if self.queue.qsize() >= self.batch_size:
            return await self._flush_batch()

        return True

    async def _flush_batch(self):
        """Send all queued notifications."""
        # Implementation...
        pass
```

### Caching

```python
class CachedEmailBackend(EmailBackend):
    """Cache SMTP connections."""

    def __init__(self, config):
        super().__init__(config)
        self._smtp_cache = None

    async def send(self, event, template):
        """Reuse SMTP connection."""
        if not self._smtp_cache:
            self._smtp_cache = self._create_smtp_connection()

        # Use cached connection...
```

---

## Logging and Debugging

### Enable Debug Logging

```python
import logging

# In your code
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("notifications")

# Then logs will show:
# DEBUG:notifications:Initializing backend: email_prod
# INFO:notifications:Email sent to user@example.com
# ERROR:notifications:Failed to send webhook: Connection timeout
```

### Structured Logging

```python
import json

logger.info(json.dumps({
    "event": event.event_type,
    "backend": "slack",
    "status": "sent",
    "duration_ms": elapsed_time,
    "recipients": "general-channel"
}))
```

---

## Integration Patterns

### With Scan Workflow

```python
from src.analyzer.notifications import NotificationManager, ScanCompletedEvent

async def run_scan_with_notifications():
    try:
        # Run scan
        results = await scan(site_url)

        # Notify success
        event = ScanCompletedEvent(
            site_name=site_url,
            pages_scanned=len(results),
            bugs_found=count_bugs(results),
            duration_seconds=scan_duration,
            output_file=output_path
        )

        manager = NotificationManager()
        await manager.notify(event)

    except Exception as e:
        # Notify failure
        event = ScanFailedEvent(
            site_name=site_url,
            error_message=str(e),
            error_details=traceback.format_exc()
        )

        manager = NotificationManager()
        await manager.notify(event)
```

### With Scheduling

```python
# In scheduler job handler
async def scheduled_scan_handler(site_url):
    result = await run_scan(site_url)

    # Notify based on results
    if result.bug_count > THRESHOLD:
        event = ThresholdAlertEvent(
            site_name=site_url,
            threshold=THRESHOLD,
            actual_count=result.bug_count,
            exceeded_by=result.bug_count - THRESHOLD
        )
    else:
        event = ScanCompletedEvent(
            site_name=site_url,
            pages_scanned=result.pages_count,
            bugs_found=result.bug_count,
            duration_seconds=result.duration
        )

    await manager.notify(event)
```

---

## Troubleshooting Development

### Backend Not Loading

```bash
# Check backend type is registered
python -c "from src.analyzer.notifications import NotificationManager; print(NotificationManager.BACKEND_TYPES.keys())"

# Should show your custom type
```

### Template Not Found

```bash
# Verify template is in NotificationTemplate.TEMPLATES
python -c "from src.analyzer.notifications import NotificationTemplate; print(NotificationTemplate.TEMPLATES.keys())"
```

### Config Not Loading

```bash
# Validate JSON
python -m json.tool notifications.json

# Check file permissions
ls -la notifications.json
chmod 644 notifications.json
```

---

## Performance Testing

### Load Test Custom Backend

```python
import asyncio
import time

async def load_test_backend():
    manager = NotificationManager()
    manager.add_backend("test", "myservice", {...})

    events = [
        ScanCompletedEvent(site_name=f"site{i}.com")
        for i in range(100)
    ]

    start = time.time()
    tasks = [manager.notify(event) for event in events]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start

    print(f"100 notifications in {elapsed:.2f}s ({100/elapsed:.0f} msg/sec)")
```

---

## Contribution Guidelines

When adding new backends or features:

1. **Follow existing patterns** in the codebase
2. **Add comprehensive tests** in `tests/test_notifications.py`
3. **Document configuration** with examples
4. **Handle errors gracefully** without blocking scans
5. **Use environment variables** for credentials
6. **Add logging** for debugging
7. **Update documentation** in `NOTIFICATIONS.md`
8. **Test with real credentials** before submitting

---

## References

- Main Documentation: `NOTIFICATIONS.md`
- Quick Start: `NOTIFICATIONS_QUICK_START.md`
- Implementation: `src/analyzer/notifications.py`
- Tests: `tests/test_notifications.py`
- Example Config: `notifications.example.json`

---

**Happy extending!** 🚀

For questions or issues, refer to the comprehensive test suite and existing backend implementations for patterns and best practices.
