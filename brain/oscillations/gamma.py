"""
brain/oscillations/gamma.py — Gamma oscillator and theta-gamma coupling
=====================================================

Lightweight gamma oscillator (PING-like) implemented as a phase generator
and a simple coupling helper to coordinate theta→gamma amplitude modulation.

This is intentionally simple: it provides a phase and a power scalar which
other systems (e.g., STDP gating or inhibitory populations) can use to
modulate their behaviour.

Usage:
    g = GammaOscillator(freq_hz=40.0)
    phase = g.tick(dt_ms=0.1)
    power = g.get_power()

"""

import numpy as np
from typing import Dict


class GammaOscillator:
    """Simple gamma phase generator (sinusoidal power envelope).

    Not a biologically-detailed PING implementation, but sufficient for
    coordinating phase-amplitude coupling with theta in this codebase.
    """

    def __init__(self, freq_hz: float = 40.0):
        self.freq_hz = float(freq_hz)
        self.period_ms = 1000.0 / self.freq_hz
        self.phase = 0.0
        self._time_accum = 0.0
        self.total_ticks = 0

    def tick(self, dt_ms: float) -> float:
        """Advance oscillator and return current phase (0-1)."""
        self._time_accum += dt_ms
        self.phase = (self._time_accum / self.period_ms) % 1.0
        self.total_ticks += 1
        return self.phase

    def get_phase(self) -> float:
        return self.phase

    def get_phase_rad(self) -> float:
        return 2.0 * np.pi * self.phase

    def get_power(self) -> float:
        """Return a normalized gamma power scalar [0,1].

        We use a rectified sinusoid so power is non-negative. This value
        can be used to modulate local inhibition strength or plasticity.
        """
        return max(0.0, np.sin(self.get_phase_rad()))

    def get_statistics(self) -> Dict:
        return {
            "gamma_freq_hz": round(self.freq_hz, 2),
            "phase": round(self.phase, 3),
            "power": round(self.get_power(), 3),
            "total_ticks": int(self.total_ticks),
        }


class ThetaGammaCoupler:
    """Helper to compute gamma amplitude as a function of theta phase.

    Typical theta-gamma coupling: gamma amplitude is higher at specific
    theta phases (e.g., trough or peak). This class provides a simple
    mapping so other code can query a modulation scalar in [0,1].
    """

    def __init__(self, preferred_phase: float = 0.25, width: float = 0.4):
        """preferred_phase: theta phase (0-1) where gamma is strongest
        width: fraction of cycle around preferred_phase where gamma is boosted"""
        self.preferred_phase = float(preferred_phase) % 1.0
        self.width = float(np.clip(width, 0.01, 1.0))

    def coupling_gain(self, theta_phase: float) -> float:
        """Compute a gain scalar (0-1) for a given theta phase."""
        # Compute circular distance
        d = abs(((theta_phase - self.preferred_phase + 0.5) % 1.0) - 0.5)
        # d in [0,0.5]. Map to [1..0] across width/2 window
        half_width = max(1e-3, self.width / 2.0)
        if d <= half_width:
            return 1.0
        # Outside preferred window, fall off linearly to 0 at full cycle
        fall = min(1.0, (d - half_width) / (0.5 - half_width))
        return max(0.0, 1.0 - fall)


def create_gamma_oscillator(freq_hz: float = 40.0) -> GammaOscillator:
    return GammaOscillator(freq_hz=freq_hz)


if __name__ == "__main__":
    g = create_gamma_oscillator(40.0)
    print("Gamma oscillator test")
    for i in range(50):
        g.tick(0.1)
        if i % 10 == 0:
            print(g.get_statistics())
