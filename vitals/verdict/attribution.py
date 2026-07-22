"""Change attribution logic (spec §4.6)."""

from __future__ import annotations

from vitals.verdict.types import Cause


def attribute_change(
    version_timeline: list[tuple[str, float]],
    current_version: str,
    onset_ts: float,
    attribution_window_s: float = 300.0,
) -> tuple[Cause, str | None, float | None]:
    """Attribute a CHANGED verdict onset to a release or unattributed cause.

    Args:
        version_timeline: List of (version_name, first_seen_ts) sorted by time.
        current_version: Version string currently being evaluated.
        onset_ts: Timestamp when change condition onset occurred.
        attribution_window_s: Lookback window in seconds before onset_ts.

    Returns:
        (cause, baseline_version, seconds_after_deploy)
    """
    if not version_timeline:
        return (Cause.UNATTRIBUTED, None, None)

    matching_idx = None
    for idx, (ver, first_seen) in enumerate(version_timeline):
        if ver == current_version:
            matching_idx = idx

    if matching_idx is None:
        return (Cause.UNATTRIBUTED, None, None)

    _, first_seen_ts = version_timeline[matching_idx]
    delta = onset_ts - first_seen_ts

    if 0.0 <= delta <= attribution_window_s:
        baseline_ver = version_timeline[matching_idx - 1][0] if matching_idx > 0 else None
        return (Cause.RELEASE, baseline_ver, delta)

    return (Cause.UNATTRIBUTED, None, None)
