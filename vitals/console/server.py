"""Console HTTP server using stdlib http.server (spec §8.3, §9, §15)."""

from __future__ import annotations

import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any

from vitals import __version__
from vitals.console.render import render_console_html

if TYPE_CHECKING:
    from vitals.health import Health
    from vitals.store import VerdictStore
    from vitals.verdict.scope import ScopeState

logger = logging.getLogger("vitals.console")


class ConsoleRequestHandler(BaseHTTPRequestHandler):
    """Handler for console HTML and REST API endpoints."""

    store: VerdictStore
    scopes: dict[tuple, ScopeState]
    health: Health
    start_time: float

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug(format, *args)

    def _send_json(self, data: Any, status: int = 200) -> None:
        try:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            logger.warning("Console JSON write error: %s", exc)

    def _send_html(self, html: str, status: int = 200) -> None:
        try:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            logger.warning("Console HTML write error: %s", exc)

    def do_GET(self) -> None:  # noqa: N802
        try:
            path = self.path.split("?")[0]

            # API endpoints
            if path == "/api/verdicts":
                verdicts = self.store.list(limit=50)
                self._send_json({"verdicts": [v.to_dict() for v in verdicts]})
                return

            if path.startswith("/api/verdicts/"):
                verdict_id = path.split("/api/verdicts/")[1]
                v = self.store.get(verdict_id)
                if v:
                    self._send_json(v.to_dict())
                else:
                    self._send_json({"error": "verdict not found"}, status=404)
                return

            if path == "/api/scopes":
                scopes_out = []
                for s in self.scopes.values():
                    (have, need), phase = s.warming_progress()
                    scopes_out.append(
                        {
                            "service_name": s.service_name,
                            "gen_ai_system": s.gen_ai_system,
                            "model": s.model,
                            "live": s.is_live(),
                            "phase": phase,
                            "warming_progress": [have, need],
                            "versions": list(s.windows.keys()),
                        }
                    )
                self._send_json({"scopes": scopes_out})
                return

            if path == "/api/health":
                snapshot = self.health.snapshot()
                snapshot["uptime_seconds"] = time.time() - self.start_time
                snapshot["version"] = __version__
                self._send_json(snapshot)
                return

            if path.startswith("/api/"):
                self._send_json({"error": "Not Found"}, status=404)
                return

            # Static asset & SPA serving (§0.2)
            import mimetypes
            from pathlib import Path

            static_dir = Path(__file__).parent / "static"
            requested_file = static_dir / path.lstrip("/")

            # Serve asset files from static/assets/ or other static assets (fonts, favicon)
            if requested_file.is_file() and not requested_file.name.endswith(".html"):
                mime_type, _ = mimetypes.guess_type(str(requested_file))
                if not mime_type:
                    mime_type = "application/octet-stream"
                body = requested_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(body)))
                if path.startswith("/assets/"):
                    self.send_header(
                        "Cache-Control", "public, max-age=31536000, immutable"
                    )
                else:
                    self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(body)
                return

            # SPA History Fallback: return index.html for all non-API paths
            index_html_file = static_dir / "index.html"
            if index_html_file.is_file():
                body = index_html_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)
                return

            # Fallback if static/index.html not built yet
            verdicts = self.store.list(limit=50)
            latest = verdicts[0] if verdicts else None
            scope_list = [s for s in self.scopes.values()]
            snapshot = self.health.snapshot()
            html = render_console_html(
                latest, verdicts, scope_list, snapshot, self.start_time
            )
            self._send_html(html)
        except Exception as exc:
            logger.exception("Console error servicing %s", self.path)
            self._send_json({"error": str(exc)}, status=500)



def create_console_server(
    host: str,
    port: int,
    store: VerdictStore,
    scopes: dict[tuple, ScopeState],
    health: Health,
) -> ThreadingHTTPServer | None:
    """Create ThreadingHTTPServer. Returns None if port already bound (spec §15)."""

    class BoundHandler(ConsoleRequestHandler):
        pass

    BoundHandler.store = store
    BoundHandler.scopes = scopes
    BoundHandler.health = health
    BoundHandler.start_time = time.time()

    try:
        server = ThreadingHTTPServer((host, port), BoundHandler)
        logger.info("Vitals console listening on http://%s:%d", host, port)
        return server
    except OSError as exc:
        logger.warning(
            "Failed to bind console server on %s:%d: %s. Console disabled.", host, port, exc
        )
        return None
