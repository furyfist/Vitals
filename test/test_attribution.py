"""Unit tests for change attribution (spec §17)."""

from vitals.verdict.attribution import attribute_change
from vitals.verdict.types import Cause


def test_attribution_release_within_window():
    timeline = [("v1", 1000.0), ("v2", 1200.0)]
    onset_ts = 1290.0  # 90 seconds after v2 deployed

    cause, baseline_ver, sec_after = attribute_change(
        version_timeline=timeline,
        current_version="v2",
        onset_ts=onset_ts,
        attribution_window_s=300.0,
    )

    assert cause == Cause.RELEASE
    assert baseline_ver == "v1"
    assert sec_after == 90.0


def test_attribution_unattributed_outside_window():
    timeline = [("v1", 1000.0), ("v2", 1200.0)]
    onset_ts = 1600.0  # 400 seconds after v2 deployed (> 300s window)

    cause, baseline_ver, sec_after = attribute_change(
        version_timeline=timeline,
        current_version="v2",
        onset_ts=onset_ts,
        attribution_window_s=300.0,
    )

    assert cause == Cause.UNATTRIBUTED
    assert baseline_ver is None
    assert sec_after is None


def test_attribution_no_timeline():
    cause, baseline_ver, sec_after = attribute_change(
        version_timeline=[],
        current_version="v1",
        onset_ts=1500.0,
    )

    assert cause == Cause.UNATTRIBUTED
    assert baseline_ver is None
    assert sec_after is None
