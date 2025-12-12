"""
Bug Finder Web UI Module

Provides web dashboard for viewing and managing bug-finder scan results.
"""

from src.analyzer.web_ui.server import create_app, DashboardServer

__all__ = ["create_app", "DashboardServer"]
