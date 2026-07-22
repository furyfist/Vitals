"""CalibratedSignal — statistical primitive wrapping every measured quantity (spec §4.2)."""

from __future__ import annotations

import math


class CalibratedSignal:

    def __init__(self, calib_n: int, sigma_floor: float = 1e-6) -> None:
        if calib_n < 2:
            raise ValueError("calib_n must be >= 2")
        self.calib_n: int = calib_n
        self.sigma_floor: float = sigma_floor
        self.n: int = 0
        self.mu: float = 0.0
        self._m2: float = 0.0
        self._sigma: float = 0.0

    def observe_calibration(self, x: float) -> None:
        """Observe a data point during the calibration phase."""
        if self.calibrated():
            return
        self.n += 1
        delta = x - self.mu
        self.mu += delta / self.n
        delta2 = x - self.mu
        self._m2 += delta * delta2

        if self.n >= 2:
            var = self._m2 / (self.n - 1)
            self._sigma = math.sqrt(max(0.0, var))

    def calibrated(self) -> bool:
        """Return True if calibration window has reached required sample count."""
        return self.n >= self.calib_n

    @property
    def sigma(self) -> float:
        """Standard deviation with sigma_floor enforced."""
        return max(self._sigma, self.sigma_floor)

    def z(self, x: float) -> float:
        """Compute (x - mu) / sigma. Raises RuntimeError if not calibrated."""
        if not self.calibrated():
            raise RuntimeError("Signal not calibrated")
        return (x - self.mu) / self.sigma
