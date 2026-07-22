"""Clock-injected replay driver (spec §D6, §18)."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable

from vitals.model import GenAISpan
from vitals.replay.fixtures import read_fixture

logger = logging.getLogger("vitals.replay")


def run_replay(
    fixture_path: str | os.PathLike,
    speed: float = 1.0,
    on_span_cb: Callable[[GenAISpan, float], None] | None = None,
) -> int:
    """Replay spans from a JSONL fixture file with clock injection.

    Args:
        fixture_path: Path to JSONL fixture file.
        speed: Speed multiplier (e.g. 1.0 = real-time, 10.0 = 10x fast-forward, 0.0 = instant).
        on_span_cb: Callback invoked for each (span, virtual_now_ts).

    Returns:
        Number of spans replayed.
    """
    records = read_fixture(fixture_path)
    if not records:
        logger.warning("Fixture %s contains 0 spans", fixture_path)
        return 0

    logger.info("Replaying %d spans from %s (speed %.1fx)", len(records), fixture_path, speed)

    start_real_ts = time.time()
    last_rel_ts = 0.0

    for idx, (span, rel_ts) in enumerate(records):
        if speed > 0.0 and idx > 0:
            delta = rel_ts - last_rel_ts
            if delta > 0:
                sleep_time = delta / speed
                time.sleep(sleep_time)
        last_rel_ts = rel_ts

        virtual_now = start_real_ts + rel_ts
        if on_span_cb is not None:
            on_span_cb(span, virtual_now)

    logger.info("Finished replaying %d spans from %s", len(records), fixture_path)
    return len(records)
