"""Unit tests for CalibratedSignal primitive (spec §17)."""

import math
import pytest
from vitals.verdict.signal import CalibratedSignal


def test_signal_calibration_not_ready():
    sig = CalibratedSignal(calib_n=30)
    assert not sig.calibrated()
    for _ in range(29):
        sig.observe_calibration(1.0)
    assert not sig.calibrated()

    with pytest.raises(RuntimeError, match="Signal not calibrated"):
        sig.z(1.0)


def test_signal_calibration_ready():
    sig = CalibratedSignal(calib_n=30)
    for i in range(30):
        sig.observe_calibration(10.0 + (i % 2))  # alternating 10 and 11
    assert sig.calibrated()
    assert math.isclose(sig.mu, 10.5, abs_tol=1e-5)
    # Z-score check
    z_val = sig.z(10.5)
    assert math.isclose(z_val, 0.0, abs_tol=1e-5)


def test_signal_sigma_floor():
    sig = CalibratedSignal(calib_n=5, sigma_floor=1e-4)
    for _ in range(5):
        sig.observe_calibration(5.0)  # zero variance
    assert sig.calibrated()
    assert sig.sigma == 1e-4
    # z should use sigma_floor
    assert sig.z(5.0) == 0.0
    assert math.isclose(sig.z(5.001), 10.0, abs_tol=1e-5)


def test_signal_z_score_calculation():
    sig = CalibratedSignal(calib_n=10)
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    for v in values:
        sig.observe_calibration(v)
    assert sig.calibrated()
    assert math.isclose(sig.mu, 5.5, abs_tol=1e-5)
    # sample std dev of 1..10 is ~3.02765
    expected_sigma = math.sqrt(sum((x - 5.5) ** 2 for x in values) / 9)
    assert math.isclose(sig.sigma, expected_sigma, abs_tol=1e-5)
    assert math.isclose(sig.z(8.52765), 1.0, abs_tol=1e-2)
