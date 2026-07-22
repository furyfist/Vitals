"""Rolling healthy-baseline window + calibrated CUSUM onset, per baseline key.

Baseline semantics (D6, honesty framing): the FIRST `window` outputs seen for a
(service, system, model) are taken as the established-good reference and frozen. Every
later output — including a new service.version — is scored as *deviation from that
healthy baseline*. This is what makes a poisoned-v2 deploy detectable: v2 drifts from
v1's healthy reference (baseline key deliberately excludes service.version).

CUSUM is calibrated on the signal's own scale (spike S4): after warming, the next
`calib_n` healthy drift values estimate mu0/sigma; k and h are expressed in sigma units.
No onset is ever reported during calibration — a clean-run false positive is worse than
slow detection (never-over-report).
"""

from __future__ import annotations

from statistics import fmean, pstdev

from spaniq.attribution.changepoint.cusum import CusumState, cusum_update

_SIGMA_FLOOR = 1e-6


class Baseline:
    """Frozen healthy-reference outputs for one baseline key, plus CUSUM state."""

    def __init__(self, window: int, calib_n: int, k_sigma: float, h_sigma: float):
        self._window = window
        self._calib_n = calib_n
        self._k_sigma = k_sigma
        self._h_sigma = h_sigma

        self.outputs: list[str] = []
        self.ready = False  # False while warming

        self._calib_values: list[float] = []
        self._calibrated = False
        self._mu0 = 0.0
        self._k = 0.0
        self._h = 0.0
        self._cusum = CusumState()
        self.onset = False  # latched once CUSUM alarms

    def add_warming_output(self, output: str) -> None:
        """Collect an output into the healthy reference; freeze when full."""
        if self.ready:
            return
        self.outputs.append(output)
        if len(self.outputs) >= self._window:
            self.ready = True

    def observe_drift(self, drift: float) -> bool:
        """Feed one post-warming drift value into CUSUM. Returns True on the first
        onset only (the transition), False otherwise."""
        if not self.ready:
            return False

        if not self._calibrated:
            self._calib_values.append(drift)
            if len(self._calib_values) >= self._calib_n:
                self._mu0 = fmean(self._calib_values)
                sigma = max(pstdev(self._calib_values), _SIGMA_FLOOR)
                self._k = self._k_sigma * sigma
                self._h = self._h_sigma * sigma
                self._calibrated = True
            return False  # never alarm during calibration

        was_alarmed = self._cusum.alarm_index is not None
        self._cusum = cusum_update(self._cusum, drift, self._mu0, self._k, self._h)
        now_alarmed = self._cusum.alarm_index is not None
        if now_alarmed and not was_alarmed:
            self.onset = True
            return True
        return False
