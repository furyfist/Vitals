"""Console package — HTML rendering and stdlib HTTP server (spec §9)."""

from vitals.console.render import render_console_html
from vitals.console.server import ConsoleRequestHandler, create_console_server

__all__ = ["render_console_html", "create_console_server", "ConsoleRequestHandler"]
