"""SQLite Verdict Store implementation (spec §12, §15)."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from typing import Any

from vitals.verdict.types import Verdict

logger = logging.getLogger("vitals.store")


class VerdictStore:
    """Single SQLite verdict store, WAL mode, locked single-connection."""

    def __init__(self, path: str | os.PathLike = "vitals.db", retain_verdicts: int = 1000) -> None:
        self.path = str(path)
        self.retain_verdicts = retain_verdicts
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        try:
            with self._lock:
                self._conn = sqlite3.connect(self.path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL;")
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS verdicts (
                      verdict_id      TEXT PRIMARY KEY,
                      ts_unix         REAL NOT NULL,
                      service_name    TEXT NOT NULL,
                      version         TEXT NOT NULL,
                      state           TEXT NOT NULL,
                      subject         TEXT NOT NULL,
                      cause           TEXT NOT NULL,
                      behavior_sigma  REAL,
                      cost_sigma      REAL,
                      samples         INTEGER NOT NULL,
                      sentence        TEXT NOT NULL,
                      payload_json    TEXT NOT NULL
                    );
                    """
                )
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_verdicts_ts ON verdicts(ts_unix DESC);"
                )
                self._conn.commit()
        except Exception as exc:
            logger.warning("Failed to initialize VerdictStore database at %s: %s", self.path, exc)

    def insert(self, verdict: Verdict, retain_count: int | None = None) -> None:
        """Insert a verdict and prune beyond retain_count. Swallows exceptions (§15)."""
        limit = retain_count if retain_count is not None else self.retain_verdicts
        try:
            payload = json.dumps(verdict.to_dict())
            with self._lock:
                if self._conn is None:
                    return
                self._conn.execute(
                    """
                    INSERT INTO verdicts (
                      verdict_id, ts_unix, service_name, version, state, subject,
                      cause, behavior_sigma, cost_sigma, samples, sentence, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        verdict.verdict_id,
                        verdict.ts_unix,
                        verdict.service_name,
                        verdict.version,
                        verdict.state.value,
                        verdict.subject.value,
                        verdict.cause.value,
                        verdict.behavior_sigma,
                        verdict.cost_sigma,
                        verdict.samples,
                        verdict.sentence,
                        payload,
                    ),
                )
                # Retention pruning
                self._conn.execute(
                    """
                    DELETE FROM verdicts
                    WHERE verdict_id NOT IN (
                      SELECT verdict_id FROM verdicts ORDER BY ts_unix DESC LIMIT ?
                    )
                    """,
                    (limit,),
                )
                self._conn.commit()
        except Exception as exc:
            logger.warning("Failed to insert verdict %s: %s", verdict.verdict_id, exc)

    def get(self, verdict_id: str) -> Verdict | None:
        """Fetch a single verdict by ID. Swallows exceptions (§15)."""
        try:
            with self._lock:
                if self._conn is None:
                    return None
                cursor = self._conn.execute(
                    "SELECT payload_json FROM verdicts WHERE verdict_id = ?", (verdict_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                payload_dict = json.loads(row["payload_json"])
                return Verdict.from_dict(payload_dict)
        except Exception as exc:
            logger.warning("Failed to get verdict %s: %s", verdict_id, exc)
            return None

    def list(self, limit: int = 50) -> list[Verdict]:
        """Fetch newest verdicts up to limit. Swallows exceptions (§15)."""
        try:
            with self._lock:
                if self._conn is None:
                    return []
                cursor = self._conn.execute(
                    "SELECT payload_json FROM verdicts ORDER BY ts_unix DESC LIMIT ?", (limit,)
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    payload_dict = json.loads(row["payload_json"])
                    results.append(Verdict.from_dict(payload_dict))
                return results
        except Exception as exc:
            logger.warning("Failed to list verdicts: %s", exc)
            return []

    def close(self) -> None:
        """Close database connection cleanly."""
        try:
            with self._lock:
                if self._conn is not None:
                    self._conn.close()
                    self._conn = None
        except Exception as exc:
            logger.warning("Failed to close VerdictStore connection: %s", exc)
