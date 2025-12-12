"""Flexible notification system for scan completion and alerts.

Supports multiple notification backends (email, Slack, webhook, console) with
customizable templates, configuration management, and event type filtering.
"""

import json
import logging
import os
import smtplib
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


# Event Type Definitions
@dataclass
class ScanEvent:
    """Base event class for notifications."""
    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    site_url: str = ""
    site_name: str = ""
    scan_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanCompletedEvent(ScanEvent):
    """Emitted when a scan completes successfully."""
    event_type: str = "scan_completed"
    pages_scanned: int = 0
    bugs_found: int = 0
    duration_seconds: float = 0.0
    report_url: Optional[str] = None
    output_file: Optional[str] = None


@dataclass
class ScanFailedEvent(ScanEvent):
    """Emitted when a scan fails."""
    event_type: str = "scan_failed"
    error_message: str = ""
    error_details: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class NewBugsFoundEvent(ScanEvent):
    """Emitted when bugs are found (compared to previous scan)."""
    event_type: str = "new_bugs_found"
    new_bugs_count: int = 0
    previous_bugs_count: int = 0
    new_bug_urls: List[str] = field(default_factory=list)


@dataclass
class BugsFixedEvent(ScanEvent):
    """Emitted when bugs are fixed (regression tracking)."""
    event_type: str = "bugs_fixed"
    fixed_bugs_count: int = 0
    remaining_bugs_count: int = 0
    fixed_bug_urls: List[str] = field(default_factory=list)


@dataclass
class ThresholdAlertEvent(ScanEvent):
    """Emitted when bugs exceed configured threshold."""
    event_type: str = "threshold_alert"
    threshold: int = 0
    actual_count: int = 0
    exceeded_by: int = 0
    severity: str = "warning"  # "warning" or "critical"


# Notification Backend Interface
class NotificationBackend(ABC):
    """Base class for notification backends."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize backend with configuration.

        Args:
            config: Backend-specific configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.supported_events = config.get("events", [])  # Empty list = all events

    @abstractmethod
    async def send(self, event: ScanEvent, template: str) -> bool:
        """Send notification for an event.

        Args:
            event: The event to notify about
            template: Rendered template content to send

        Returns:
            True if successful, False otherwise
        """
        pass

    def supports_event(self, event_type: str) -> bool:
        """Check if backend supports this event type.

        Args:
            event_type: Type of event

        Returns:
            True if supported or no filtering configured
        """
        if not self.supported_events:
            return True
        return event_type in self.supported_events

    def _substitute_env_vars(self, value: str) -> str:
        """Substitute environment variables in config values.

        Format: ${VAR_NAME}

        Args:
            value: String that may contain env var references

        Returns:
            String with env vars substituted
        """
        import re
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)


class ConsoleBackend(NotificationBackend):
    """Print notifications to console (for testing)."""

    async def send(self, event: ScanEvent, template: str) -> bool:
        """Print notification to console.

        Args:
            event: The event to notify about
            template: Rendered template content

        Returns:
            Always True
        """
        print("\n" + "=" * 80)
        print(f"NOTIFICATION: {event.event_type.upper()}")
        print("=" * 80)
        print(template)
        print("=" * 80 + "\n")
        return True


class EmailBackend(NotificationBackend):
    """Send email notifications via SMTP."""

    async def send(self, event: ScanEvent, template: str) -> bool:
        """Send email notification.

        Args:
            event: The event to notify about
            template: Rendered template content (should contain subject line)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get SMTP configuration
            smtp_host = self._substitute_env_vars(self.config.get("smtp_host", ""))
            smtp_port = self.config.get("smtp_port", 587)
            smtp_user = self._substitute_env_vars(self.config.get("smtp_user", ""))
            smtp_password = self._substitute_env_vars(self.config.get("smtp_password", ""))
            from_address = self._substitute_env_vars(self.config.get("from_address", ""))
            to_addresses = self.config.get("to_addresses", [])
            use_tls = self.config.get("use_tls", True)

            if not all([smtp_host, smtp_user, smtp_password, from_address, to_addresses]):
                logger.error("Missing required email configuration")
                return False

            # Prepare message
            if isinstance(to_addresses, str):
                to_addresses = [to_addresses]

            # Parse template for subject line (first line)
            lines = template.split('\n', 1)
            subject = lines[0].replace('Subject: ', '').strip()
            body = lines[1] if len(lines) > 1 else template

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)

            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Add HTML part if available
            html_body = self._template_to_html(body, event)
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {', '.join(to_addresses)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _template_to_html(self, text: str, event: ScanEvent) -> Optional[str]:
        """Convert plain text template to HTML.

        Args:
            text: Plain text template
            event: Event object for context

        Returns:
            HTML string or None
        """
        try:
            # Simple conversion: newlines to <br>, bold text patterns
            html = text.replace('\n', '<br>\n')
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; }}
                    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
                    .stat {{ font-weight: bold; color: #0066cc; }}
                    a {{ color: #0066cc; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Scan Notification - {event.event_type}</h2>
                </div>
                <div class="content">
                    {html}
                </div>
                <div class="footer">
                    <p>Automated notification from Bug Finder</p>
                </div>
            </body>
            </html>
            """
            return html
        except Exception as e:
            logger.warning(f"Failed to convert to HTML: {e}")
            return None


class SlackBackend(NotificationBackend):
    """Send notifications to Slack via webhook."""

    async def send(self, event: ScanEvent, template: str) -> bool:
        """Send Slack notification.

        Args:
            event: The event to notify about
            template: Rendered template content

        Returns:
            True if successful, False otherwise
        """
        try:
            webhook_url = self._substitute_env_vars(self.config.get("webhook_url", ""))

            if not webhook_url:
                logger.error("Missing Slack webhook URL")
                return False

            # Build Slack message payload
            payload = self._build_slack_payload(event, template)

            # Send to Slack
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info("Slack notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _build_slack_payload(self, event: ScanEvent, template: str) -> Dict[str, Any]:
        """Build Slack message payload.

        Args:
            event: Event object
            template: Template content

        Returns:
            Slack payload dictionary
        """
        # Color coding by event type
        color_map = {
            "scan_completed": "#36a64f",  # Green
            "scan_failed": "#ff0000",      # Red
            "new_bugs_found": "#ffaa00",   # Orange
            "bugs_fixed": "#0099cc",       # Blue
            "threshold_alert": "#ff6600",  # Orange-red
        }

        emoji_map = {
            "scan_completed": "✅",
            "scan_failed": "❌",
            "new_bugs_found": "🐛",
            "bugs_fixed": "🔧",
            "threshold_alert": "⚠️",
        }

        color = color_map.get(event.event_type, "#808080")
        emoji = emoji_map.get(event.event_type, "📢")

        fields = []

        # Add relevant fields based on event type
        if isinstance(event, ScanCompletedEvent):
            fields = [
                {"title": "Site", "value": event.site_name or event.site_url, "short": True},
                {"title": "Pages Scanned", "value": str(event.pages_scanned), "short": True},
                {"title": "Bugs Found", "value": str(event.bugs_found), "short": True},
                {"title": "Duration", "value": f"{event.duration_seconds:.1f}s", "short": True},
            ]
            if event.report_url:
                fields.append({"title": "Report", "value": f"<{event.report_url}|View Report>", "short": False})

        elif isinstance(event, ScanFailedEvent):
            fields = [
                {"title": "Site", "value": event.site_name or event.site_url, "short": True},
                {"title": "Error", "value": event.error_message, "short": False},
                {"title": "Duration", "value": f"{event.duration_seconds:.1f}s", "short": True},
            ]

        elif isinstance(event, NewBugsFoundEvent):
            fields = [
                {"title": "Site", "value": event.site_name or event.site_url, "short": True},
                {"title": "New Bugs", "value": str(event.new_bugs_count), "short": True},
                {"title": "Previous", "value": str(event.previous_bugs_count), "short": True},
            ]

        elif isinstance(event, BugsFixedEvent):
            fields = [
                {"title": "Site", "value": event.site_name or event.site_url, "short": True},
                {"title": "Fixed Bugs", "value": str(event.fixed_bugs_count), "short": True},
                {"title": "Remaining", "value": str(event.remaining_bugs_count), "short": True},
            ]

        elif isinstance(event, ThresholdAlertEvent):
            fields = [
                {"title": "Site", "value": event.site_name or event.site_url, "short": True},
                {"title": "Threshold", "value": str(event.threshold), "short": True},
                {"title": "Actual Count", "value": str(event.actual_count), "short": True},
                {"title": "Exceeded By", "value": str(event.exceeded_by), "short": True},
            ]

        # Build attachment
        attachment = {
            "color": color,
            "title": f"{emoji} {event.event_type.replace('_', ' ').title()}",
            "text": template.split('\n', 1)[0],  # First line as summary
            "fields": fields,
            "footer": "Bug Finder",
            "ts": int(datetime.fromisoformat(event.timestamp).timestamp()),
        }

        return {
            "attachments": [attachment]
        }


class WebhookBackend(NotificationBackend):
    """Send notifications to custom webhook endpoint."""

    async def send(self, event: ScanEvent, template: str) -> bool:
        """Send webhook notification.

        Args:
            event: The event to notify about
            template: Rendered template content

        Returns:
            True if successful, False otherwise
        """
        try:
            webhook_url = self._substitute_env_vars(self.config.get("webhook_url", ""))

            if not webhook_url:
                logger.error("Missing webhook URL")
                return False

            # Build payload
            payload = {
                "event": event.event_type,
                "timestamp": event.timestamp,
                "site_url": event.site_url,
                "site_name": event.site_name,
                "scan_id": event.scan_id,
                "message": template,
                "data": event.data,
            }

            # Add event-specific data
            if hasattr(event, '__dict__'):
                event_dict = {k: v for k, v in event.__dict__.items()
                             if k not in ['event_type', 'timestamp', 'site_url', 'site_name', 'scan_id', 'data']}
                payload["event_data"] = event_dict

            # Send webhook
            headers = self.config.get("headers", {})
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Webhook sent to {webhook_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False


# Template System
class NotificationTemplate:
    """Manages notification templates for different event types."""

    TEMPLATES = {
        "scan_completed": {
            "console": """Subject: Bug Scan Complete - {site_name}

Scan Results for {site_name}:
  Pages scanned: {pages_scanned}
  Bugs found: {bugs_found}
  Duration: {duration_seconds:.1f} seconds
  Scan ID: {scan_id}

Output saved to: {output_file}
Report URL: {report_url}

Next steps:
  1. Review the results
  2. Compare with previous scans
  3. File issues for confirmed bugs
""",
            "slack": """Scan completed successfully on {site_name}
Pages: {pages_scanned} | Bugs: {bugs_found} | Time: {duration_seconds:.1f}s""",
            "email": """Subject: Bug Scan Complete - {site_name}

Dear Team,

Your scheduled bug scan has completed successfully.

Scan Summary:
- Site: {site_name}
- Pages Scanned: {pages_scanned}
- Bugs Found: {bugs_found}
- Duration: {duration_seconds:.1f} seconds
- Scan ID: {scan_id}

Output File: {output_file}
Report URL: {report_url}

Next Steps:
1. Review the results in the report
2. Compare with previous scans using: bug-finder compare
3. File issues for confirmed bugs
4. Plan fixes based on severity

Questions? Contact the QA team.

Best regards,
Bug Finder
""",
        },
        "scan_failed": {
            "console": """Subject: Bug Scan Failed - {site_name}

Scan failed for {site_name}:
  Error: {error_message}
  Duration: {duration_seconds:.1f} seconds
  Scan ID: {scan_id}

Details:
{error_details}

Please review the error and retry the scan.
""",
            "slack": """Scan failed on {site_name}: {error_message}""",
            "email": """Subject: Bug Scan Failed - {site_name}

Dear Team,

The scheduled bug scan has failed.

Failure Details:
- Site: {site_name}
- Error: {error_message}
- Duration: {duration_seconds:.1f} seconds
- Scan ID: {scan_id}

Technical Details:
{error_details}

Please investigate and retry the scan.

Best regards,
Bug Finder
""",
        },
        "new_bugs_found": {
            "console": """Subject: New Bugs Detected - {site_name}

New bugs detected on {site_name}:
  New bugs: {new_bugs_count}
  Previous bugs: {previous_bugs_count}
  Scan ID: {scan_id}

Affected Pages:
{new_bug_urls_list}

Action Required: Review and prioritize these bugs.
""",
            "slack": """New bugs found on {site_name}: {new_bugs_count} new issues (was {previous_bugs_count})""",
            "email": """Subject: New Bugs Detected - {site_name}

Dear Team,

New bugs have been detected during the latest scan.

Bug Summary:
- Site: {site_name}
- New Bugs Found: {new_bugs_count}
- Previous Count: {previous_bugs_count}
- Scan ID: {scan_id}

Affected Pages:
{new_bug_urls_list}

Action Required:
1. Review the affected pages
2. Assess severity and impact
3. Create issues if needed
4. Plan fixes accordingly

Best regards,
Bug Finder
""",
        },
        "bugs_fixed": {
            "console": """Subject: Bugs Fixed - {site_name}

Bugs have been fixed on {site_name}:
  Fixed bugs: {fixed_bugs_count}
  Remaining bugs: {remaining_bugs_count}
  Scan ID: {scan_id}

Fixed Pages:
{fixed_bug_urls_list}

Great progress! Keep up the good work.
""",
            "slack": """Bugs fixed on {site_name}: {fixed_bugs_count} issues resolved (Remaining: {remaining_bugs_count})""",
            "email": """Subject: Bugs Fixed - {site_name}

Dear Team,

Great news! Bugs have been fixed on {site_name}.

Fix Summary:
- Site: {site_name}
- Bugs Fixed: {fixed_bugs_count}
- Remaining: {remaining_bugs_count}
- Scan ID: {scan_id}

Fixed Pages:
{fixed_bug_urls_list}

Congratulations on the progress! Continue monitoring for any regressions.

Best regards,
Bug Finder
""",
        },
        "threshold_alert": {
            "console": """Subject: Bug Threshold Exceeded - {site_name}

ALERT: Bug count has exceeded threshold on {site_name}
  Threshold: {threshold}
  Actual Count: {actual_count}
  Exceeded By: {exceeded_by}
  Severity: {severity}
  Scan ID: {scan_id}

Immediate action required!
""",
            "slack": """⚠️ ALERT: Bug threshold exceeded on {site_name} ({actual_count} > {threshold})""",
            "email": """Subject: ALERT - Bug Threshold Exceeded - {site_name}

Dear Team,

ALERT: The bug count on {site_name} has exceeded the configured threshold.

Alert Details:
- Site: {site_name}
- Threshold: {threshold}
- Actual Count: {actual_count}
- Exceeded By: {exceeded_by}
- Severity: {severity}
- Scan ID: {scan_id}

IMMEDIATE ACTION REQUIRED

Please investigate and address the critical bugs immediately.
This may indicate a major quality issue or regression.

Contact QA lead for assistance.

Best regards,
Bug Finder
""",
        },
    }

    @staticmethod
    def render(event_type: str, backend_type: str, event: ScanEvent) -> str:
        """Render a template for the given event and backend.

        Args:
            event_type: Type of event (e.g., "scan_completed")
            backend_type: Backend type (console, email, slack, webhook)
            event: Event object with data to render

        Returns:
            Rendered template string

        Raises:
            ValueError: If template not found
        """
        if event_type not in NotificationTemplate.TEMPLATES:
            raise ValueError(f"Unknown event type: {event_type}")

        templates = NotificationTemplate.TEMPLATES[event_type]
        template = templates.get(backend_type, templates.get("console", ""))

        if not template:
            raise ValueError(f"No template for {event_type} in {backend_type}")

        # Build format dict from event
        format_dict = {
            "site_name": event.site_name or event.site_url,
            "site_url": event.site_url,
            "scan_id": event.scan_id,
            "timestamp": event.timestamp,
        }

        # Add event-specific fields
        if hasattr(event, '__dict__'):
            for key, value in event.__dict__.items():
                if key not in format_dict:
                    format_dict[key] = value

        # Special handling for URL lists
        if "new_bug_urls" in format_dict and format_dict.get("new_bug_urls"):
            urls = format_dict["new_bug_urls"]
            format_dict["new_bug_urls_list"] = "\n".join(
                f"  - {url}" for url in urls[:10]
            )
            if len(urls) > 10:
                format_dict["new_bug_urls_list"] += f"\n  ... and {len(urls) - 10} more"
        else:
            # Provide default empty list if not present
            format_dict["new_bug_urls_list"] = "(No new bugs)"

        if "fixed_bug_urls" in format_dict and format_dict.get("fixed_bug_urls"):
            urls = format_dict["fixed_bug_urls"]
            format_dict["fixed_bug_urls_list"] = "\n".join(
                f"  - {url}" for url in urls[:10]
            )
            if len(urls) > 10:
                format_dict["fixed_bug_urls_list"] += f"\n  ... and {len(urls) - 10} more"
        else:
            # Provide default empty list if not present
            format_dict["fixed_bug_urls_list"] = "(No bugs fixed)"

        # Handle None/missing values
        for key in format_dict:
            if format_dict[key] is None:
                format_dict[key] = "-"

        return template.format(**format_dict)


# Configuration Management
class NotificationConfig:
    """Manages notification configuration."""

    DEFAULT_CONFIG = {
        "enabled": True,
        "backends": {
            "console": {
                "enabled": True,
                "type": "console",
                "events": []  # Empty = all events
            }
        }
    }

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize notification configuration.

        Args:
            config_path: Path to config file (JSON) or None for defaults
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()

        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: Union[str, Path]):
        """Load configuration from file.

        Args:
            config_path: Path to JSON config file
        """
        try:
            config_path = Path(config_path)
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.config.update(loaded)

            logger.info(f"Loaded notification config from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save(self, output_path: Union[str, Path]):
        """Save configuration to file.

        Args:
            output_path: Path where config will be saved
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)

            logger.info(f"Saved notification config to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_backends(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured backends.

        Returns:
            Dictionary of backend configurations
        """
        return self.config.get("backends", {})

    def get_backend_config(self, backend_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific backend.

        Args:
            backend_name: Name of the backend (e.g., "email_production")

        Returns:
            Backend configuration or None if not found
        """
        backends = self.get_backends()
        return backends.get(backend_name)

    def add_backend(self, name: str, backend_type: str, config: Dict[str, Any]):
        """Add or update a backend configuration.

        Args:
            name: Backend name (for reference)
            backend_type: Type of backend (console, email, slack, webhook)
            config: Backend-specific configuration
        """
        if "backends" not in self.config:
            self.config["backends"] = {}

        self.config["backends"][name] = {
            "type": backend_type,
            "enabled": config.get("enabled", True),
            **config
        }


# Notification Manager
class NotificationManager:
    """Manages sending notifications across multiple backends."""

    BACKEND_TYPES = {
        "console": ConsoleBackend,
        "email": EmailBackend,
        "slack": SlackBackend,
        "webhook": WebhookBackend,
    }

    def __init__(self, config: Optional[Union[str, Path, NotificationConfig]] = None):
        """Initialize notification manager.

        Args:
            config: Path to config file, NotificationConfig object, or None for defaults
        """
        if isinstance(config, NotificationConfig):
            self.config = config
        elif isinstance(config, (str, Path)):
            self.config = NotificationConfig(config)
        else:
            self.config = NotificationConfig()

        self.backends = self._initialize_backends()

    def _initialize_backends(self) -> Dict[str, NotificationBackend]:
        """Initialize backend instances.

        Returns:
            Dictionary of initialized backends
        """
        backends = {}

        for name, config in self.config.get_backends().items():
            try:
                backend_type = config.get("type", "console")
                backend_class = self.BACKEND_TYPES.get(backend_type)

                if not backend_class:
                    logger.warning(f"Unknown backend type: {backend_type}")
                    continue

                backend = backend_class(config)
                if backend.enabled:
                    backends[name] = backend
                    logger.debug(f"Initialized backend: {name}")

            except Exception as e:
                logger.error(f"Failed to initialize backend {name}: {e}")

        return backends

    async def notify(self, event: ScanEvent) -> Dict[str, bool]:
        """Send notification for an event to all configured backends.

        Args:
            event: Event to notify about

        Returns:
            Dictionary mapping backend names to success status
        """
        results = {}

        if not self.backends:
            logger.warning("No notification backends configured")
            return results

        # Render templates for each backend type
        templates = {}
        for backend_name, backend in self.backends.items():
            backend_type = backend.config.get("type", "console")

            # Only render if backend supports this event
            if backend.supports_event(event.event_type):
                try:
                    if backend_type not in templates:
                        templates[backend_type] = NotificationTemplate.render(
                            event.event_type,
                            backend_type,
                            event
                        )
                    template = templates[backend_type]

                    # Send notification
                    success = await backend.send(event, template)
                    results[backend_name] = success

                except Exception as e:
                    logger.error(f"Failed to notify via {backend_name}: {e}")
                    results[backend_name] = False
            else:
                logger.debug(f"Backend {backend_name} doesn't support {event.event_type}")

        return results

    def add_backend(self, name: str, backend_type: str, config: Dict[str, Any]):
        """Add a new backend at runtime.

        Args:
            name: Backend name
            backend_type: Type of backend
            config: Backend configuration
        """
        self.config.add_backend(name, backend_type, config)
        self.backends = self._initialize_backends()

    def get_backend(self, name: str) -> Optional[NotificationBackend]:
        """Get a backend by name.

        Args:
            name: Backend name

        Returns:
            Backend instance or None
        """
        return self.backends.get(name)


# Example usage and testing
async def test_notifications():
    """Test notification system with sample events."""

    # Create sample event
    event = ScanCompletedEvent(
        site_name="example.com",
        site_url="https://example.com",
        scan_id="scan_20231201_120000",
        pages_scanned=150,
        bugs_found=42,
        duration_seconds=125.5,
        output_file="/path/to/results.json",
        report_url="https://example.com/reports/scan_20231201"
    )

    # Create manager with console backend
    manager = NotificationManager()
    manager.add_backend("console", "console", {"enabled": True})

    # Send notification
    results = await manager.notify(event)
    print(f"Notification results: {results}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_notifications())
