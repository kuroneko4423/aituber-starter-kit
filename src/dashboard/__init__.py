"""Web dashboard module for AITuber Starter Kit."""

from .server import DashboardServer
from .api import create_app

__all__ = ["DashboardServer", "create_app"]
