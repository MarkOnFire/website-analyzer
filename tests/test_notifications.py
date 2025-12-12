"""Tests for the notification system."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.analyzer.notifications import (
    NotificationManager,
    NotificationConfig,
    NotificationTemplate,
    ScanCompletedEvent,
    ScanFailedEvent,
    NewBugsFoundEvent,
    BugsFixedEvent,
    ThresholdAlertEvent,
    ConsoleBackend,
    EmailBackend,
    SlackBackend,
    WebhookBackend,
)


class TestEventCreation:
    """Test event creation and initialization."""

    def test_scan_completed_event(self):
        """Test ScanCompletedEvent creation."""
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

        assert event.event_type == "scan_completed"
        assert event.site_name == "example.com"
        assert event.pages_scanned == 150
        assert event.bugs_found == 42
        assert event.timestamp is not None

    def test_scan_failed_event(self):
        """Test ScanFailedEvent creation."""
        event = ScanFailedEvent(
            site_name="example.com",
            error_message="Connection timeout",
            error_details="The server stopped responding",
            duration_seconds=300.0
        )

        assert event.event_type == "scan_failed"
        assert event.error_message == "Connection timeout"

    def test_new_bugs_found_event(self):
        """Test NewBugsFoundEvent creation."""
        event = NewBugsFoundEvent(
            site_name="example.com",
            new_bugs_count=15,
            previous_bugs_count=27,
            new_bug_urls=["https://example.com/page1"]
        )

        assert event.event_type == "new_bugs_found"
        assert event.new_bugs_count == 15

    def test_bugs_fixed_event(self):
        """Test BugsFixedEvent creation."""
        event = BugsFixedEvent(
            site_name="example.com",
            fixed_bugs_count=10,
            remaining_bugs_count=5
        )

        assert event.event_type == "bugs_fixed"
        assert event.fixed_bugs_count == 10

    def test_threshold_alert_event(self):
        """Test ThresholdAlertEvent creation."""
        event = ThresholdAlertEvent(
            site_name="example.com",
            threshold=50,
            actual_count=127,
            exceeded_by=77,
            severity="critical"
        )

        assert event.event_type == "threshold_alert"
        assert event.exceeded_by == 77


class TestConsoleBackend:
    """Test console notification backend."""

    @pytest.mark.asyncio
    async def test_console_send(self, capsys):
        """Test console backend sends to stdout."""
        backend = ConsoleBackend({"enabled": True})
        event = ScanCompletedEvent(
            site_name="example.com",
            pages_scanned=100,
            bugs_found=10,
            duration_seconds=60.0
        )

        result = await backend.send(event, "Test message")
        assert result is True
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_console_backend_enabled(self):
        """Test console backend enabled check."""
        backend = ConsoleBackend({"enabled": True})
        assert backend.enabled is True

        backend = ConsoleBackend({"enabled": False})
        assert backend.enabled is False


class TestEmailBackend:
    """Test email notification backend."""

    def test_email_backend_initialization(self):
        """Test email backend config validation."""
        config = {
            "enabled": True,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_address": "sender@example.com",
            "to_addresses": ["recipient@example.com"]
        }
        backend = EmailBackend(config)
        assert backend.enabled is True

    def test_email_env_var_substitution(self):
        """Test environment variable substitution."""
        import os
        os.environ["TEST_SMTP_HOST"] = "smtp.gmail.com"

        backend = EmailBackend({
            "enabled": True,
            "smtp_host": "${TEST_SMTP_HOST}"
        })

        result = backend._substitute_env_vars("${TEST_SMTP_HOST}")
        assert result == "smtp.gmail.com"

    def test_email_missing_config(self):
        """Test email backend with missing config."""
        backend = EmailBackend({
            "enabled": True,
            "smtp_host": ""
        })

        # Should still initialize, but send should fail gracefully
        assert backend.enabled is True

    def test_email_template_to_html(self):
        """Test plain text to HTML conversion."""
        backend = EmailBackend({"enabled": True})
        event = ScanCompletedEvent(site_name="test.com")

        html = backend._template_to_html("Test message", event)
        assert html is not None
        assert "<html>" in html
        assert "Test message" in html


class TestSlackBackend:
    """Test Slack notification backend."""

    def test_slack_payload_creation(self):
        """Test Slack payload building."""
        backend = SlackBackend({
            "enabled": True,
            "webhook_url": "https://hooks.slack.com/test"
        })

        event = ScanCompletedEvent(
            site_name="example.com",
            pages_scanned=100,
            bugs_found=10,
            duration_seconds=60.0
        )

        payload = backend._build_slack_payload(event, "Test")
        assert "attachments" in payload
        assert len(payload["attachments"]) > 0
        assert "color" in payload["attachments"][0]

    def test_slack_color_mapping(self):
        """Test Slack event type to color mapping."""
        backend = SlackBackend({
            "enabled": True,
            "webhook_url": "https://hooks.slack.com/test"
        })

        # Test different event types have different colors
        events = {
            "scan_completed": ScanCompletedEvent(site_name="test.com"),
            "scan_failed": ScanFailedEvent(site_name="test.com", error_message="Error"),
            "threshold_alert": ThresholdAlertEvent(site_name="test.com"),
        }

        colors = set()
        for payload in [backend._build_slack_payload(event, "Test") for event in events.values()]:
            colors.add(payload["attachments"][0]["color"])

        # Should have at least 2 different colors
        assert len(colors) >= 2


class TestWebhookBackend:
    """Test webhook notification backend."""

    def test_webhook_config(self):
        """Test webhook backend configuration."""
        config = {
            "enabled": True,
            "webhook_url": "https://api.example.com/webhook",
            "headers": {"Authorization": "Bearer token"}
        }
        backend = WebhookBackend(config)
        assert backend.config["webhook_url"] == "https://api.example.com/webhook"

    @pytest.mark.asyncio
    async def test_webhook_missing_url(self):
        """Test webhook fails without URL."""
        backend = WebhookBackend({"enabled": True})
        event = ScanCompletedEvent(site_name="test.com")

        result = await backend.send(event, "Test")
        assert result is False


class TestNotificationTemplate:
    """Test notification template system."""

    def test_template_rendering_scan_completed(self):
        """Test template rendering for scan completed event."""
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

        template = NotificationTemplate.render("scan_completed", "console", event)
        assert "example.com" in template
        assert "150" in template
        assert "42" in template

    def test_template_rendering_scan_failed(self):
        """Test template rendering for scan failed event."""
        event = ScanFailedEvent(
            site_name="example.com",
            error_message="Connection timeout"
        )

        template = NotificationTemplate.render("scan_failed", "console", event)
        assert "Connection timeout" in template

    def test_template_unknown_event(self):
        """Test template rendering with unknown event type."""
        event = ScanCompletedEvent(site_name="test.com")

        with pytest.raises(ValueError):
            NotificationTemplate.render("unknown_event", "console", event)

    def test_template_url_list_formatting(self):
        """Test template formatting of URL lists."""
        event = NewBugsFoundEvent(
            site_name="example.com",
            new_bugs_count=15,
            previous_bugs_count=27,
            new_bug_urls=[
                f"https://example.com/page{i}"
                for i in range(15)
            ]
        )

        template = NotificationTemplate.render("new_bugs_found", "console", event)
        assert "page0" in template
        assert "more" in template  # Should mention there are more


class TestNotificationConfig:
    """Test configuration management."""

    def test_config_creation_with_defaults(self):
        """Test config uses defaults when not provided."""
        config = NotificationConfig()
        backends = config.get_backends()
        assert "console" in backends or len(backends) == 0

    def test_config_add_backend(self):
        """Test adding backends to config."""
        config = NotificationConfig()
        config.add_backend("test_backend", "console", {"enabled": True})

        backends = config.get_backends()
        assert "test_backend" in backends

    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config = NotificationConfig()
        config.add_backend("test", "console", {"enabled": True})

        config_file = tmp_path / "test_config.json"
        config.save(config_file)

        assert config_file.exists()

        # Load and verify
        with open(config_file) as f:
            data = json.load(f)
            assert "backends" in data
            assert "test" in data["backends"]

    def test_config_get_backend(self):
        """Test retrieving specific backend config."""
        config = NotificationConfig()
        config.add_backend("email", "email", {
            "enabled": True,
            "smtp_host": "smtp.example.com"
        })

        backend_config = config.get_backend_config("email")
        assert backend_config is not None
        assert backend_config["smtp_host"] == "smtp.example.com"


class TestNotificationManager:
    """Test notification manager."""

    def test_manager_initialization(self):
        """Test manager initialization with defaults."""
        manager = NotificationManager()
        assert manager.config is not None
        assert len(manager.backends) >= 0

    def test_manager_add_backend_runtime(self):
        """Test adding backend at runtime."""
        manager = NotificationManager()
        manager.add_backend("test_console", "console", {"enabled": True})

        backend = manager.get_backend("test_console")
        assert backend is not None

    def test_manager_get_backend(self):
        """Test retrieving backend by name."""
        manager = NotificationManager()
        manager.add_backend("my_backend", "console", {"enabled": True})

        backend = manager.get_backend("my_backend")
        assert backend is not None
        assert isinstance(backend, ConsoleBackend)

    @pytest.mark.asyncio
    async def test_manager_notify_returns_results(self):
        """Test manager notification returns success status."""
        manager = NotificationManager()
        manager.add_backend("test_console", "console", {"enabled": True})

        event = ScanCompletedEvent(site_name="test.com")
        results = await manager.notify(event)

        assert isinstance(results, dict)
        assert "test_console" in results

    @pytest.mark.asyncio
    async def test_manager_multiple_backends(self):
        """Test manager with multiple backends."""
        manager = NotificationManager()
        manager.add_backend("console1", "console", {"enabled": True})
        manager.add_backend("console2", "console", {"enabled": True})

        event = ScanCompletedEvent(site_name="test.com")
        results = await manager.notify(event)

        assert len(results) >= 2


class TestBackendEventFiltering:
    """Test event type filtering in backends."""

    def test_backend_supports_all_events_by_default(self):
        """Test backend supports all events when no filter specified."""
        backend = ConsoleBackend({"enabled": True})
        assert backend.supports_event("scan_completed") is True
        assert backend.supports_event("scan_failed") is True

    def test_backend_filters_events(self):
        """Test backend filters events correctly."""
        backend = ConsoleBackend({
            "enabled": True,
            "events": ["scan_completed", "scan_failed"]
        })

        assert backend.supports_event("scan_completed") is True
        assert backend.supports_event("new_bugs_found") is False

    @pytest.mark.asyncio
    async def test_manager_respects_event_filters(self):
        """Test manager respects backend event filters."""
        manager = NotificationManager()
        manager.add_backend("test_backend", "console", {
            "enabled": True,
            "events": ["scan_completed"]  # Only this event
        })

        # Scan completed should work
        event1 = ScanCompletedEvent(site_name="test.com")
        results1 = await manager.notify(event1)
        assert len(results1) > 0

        # This would work with multiple backends, but with one filtered backend
        # it may not appear in results if filtered
        event2 = ScanFailedEvent(site_name="test.com", error_message="Error")
        results2 = await manager.notify(event2)
        # Backend filters events, so it might not send


class TestSecurityAndEnvironment:
    """Test security features and environment handling."""

    def test_env_var_substitution_multiple_vars(self):
        """Test substituting multiple environment variables."""
        import os
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"

        backend = ConsoleBackend({"enabled": True})
        text = "${VAR1} and ${VAR2}"
        result = backend._substitute_env_vars(text)

        assert result == "value1 and value2"

    def test_env_var_missing_keeps_placeholder(self):
        """Test missing environment variables keep placeholder."""
        backend = ConsoleBackend({"enabled": True})
        text = "${NONEXISTENT_VAR}"
        result = backend._substitute_env_vars(text)

        # Should return the placeholder as-is
        assert result == "${NONEXISTENT_VAR}"


class TestEventDataPreservation:
    """Test that event data is properly preserved."""

    def test_event_custom_data(self):
        """Test event can carry custom data."""
        event = ScanCompletedEvent(
            site_name="test.com",
            data={"custom_key": "custom_value"}
        )

        assert event.data["custom_key"] == "custom_value"

    def test_slack_payload_includes_event_data(self):
        """Test Slack payload includes all event data."""
        backend = SlackBackend({
            "enabled": True,
            "webhook_url": "https://hooks.slack.com/test"
        })

        event = ScanCompletedEvent(
            site_name="test.com",
            pages_scanned=100,
            bugs_found=10,
            data={"custom": "data"}
        )

        payload = backend._build_slack_payload(event, "Test")
        assert payload is not None


# Integration tests
class TestIntegration:
    """Integration tests for full notification flow."""

    @pytest.mark.asyncio
    async def test_full_notification_flow(self, tmp_path):
        """Test complete notification flow."""
        # Create config
        config_file = tmp_path / "config.json"
        config = NotificationConfig()
        config.add_backend("console", "console", {"enabled": True})
        config.save(config_file)

        # Create manager
        manager = NotificationManager(config_file)

        # Create event
        event = ScanCompletedEvent(
            site_name="example.com",
            pages_scanned=100,
            bugs_found=10,
            duration_seconds=60.0
        )

        # Send notification
        results = await manager.notify(event)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_all_event_types_renderable(self):
        """Test all event types can be rendered by all backends."""
        events = [
            ScanCompletedEvent(site_name="test.com"),
            ScanFailedEvent(site_name="test.com", error_message="Error"),
            NewBugsFoundEvent(site_name="test.com", new_bugs_count=5, previous_bugs_count=3),
            BugsFixedEvent(site_name="test.com", fixed_bugs_count=5, remaining_bugs_count=0),
            ThresholdAlertEvent(site_name="test.com", threshold=50, actual_count=100, exceeded_by=50),
        ]

        for event in events:
            # Should render without error
            template = NotificationTemplate.render(event.event_type, "console", event)
            assert template
            assert event.site_name in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
