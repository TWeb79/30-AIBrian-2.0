"""
brain/oscillations/gamma_ping.py — Simple PING-style E/I gamma generator
=====================================================================

Lightweight PING (pyramidal-interneuron gamma) rhythm implemented using
two LIF populations (E and I) connected with fixed weights. This is not a
full spiking network simulator but provides a runnable E/I pair that produces
gamma-range oscillatory firing under appropriate drive.

Usage:
    ping = PINGGamma(n_exc=200, n_inh=50)
    ping.step(dt_ms=0.1, ext_drive=5.0)
    power = ping.get_power()
"""

import numpy as np
from typing import Dict
from brain.neurons import LIFPopulation, LIFParams


class PINGGamma:
    def __init__(self, n_exc: int = 200, n_inh: int = 50):
        # Excitatory (E) and inhibitory (I) populations
        self.e = LIFPopulation(n_exc, LIFParams(tau_m=20.0, tau_ref=2.0, v_thresh=-50.0), name="ping_e")
        self.i = LIFPopulation(n_inh, LIFParams(tau_m=10.0, tau_ref=1.0, v_thresh=-47.0), name="ping_i")

        # Simple connection strengths (per-spike current)
        self.w_ei = 8.0   # E -> I excitation
        self.w_ie = 12.0  # I -> E inhibition

        # Buffers for synaptic currents
        self.i_e = np.zeros(self.e.n, dtype=np.float32)
        self.i_i = np.zeros(self.i.n, dtype=np.float32)

        # Statistics
        self.total_ticks = 0

    def step(self, dt_ms: float = 0.1, ext_drive: float = 0.0):
        """Advance populations one timestep.

        ext_drive is applied as constant current to excitatory population
        to kick the network into oscillation.
        """
        # Inject external drive into E population
        if ext_drive > 0:
            # choose a fraction of E neurons to drive
            k = max(1, int(self.e.n * 0.1))
            idx = np.random.choice(self.e.n, size=k, replace=False)
            self.e.inject_current(idx, ext_drive)

        # Advance E
        e_spikes = self.e.step(self.i_e)

        # E excites I
        if e_spikes.size > 0:
            # Add excitatory current uniformly to I neurons
            self.i.inject_current(np.arange(self.i.n), self.w_ei * (e_spikes.size / max(1, self.e.n)))

        # Advance I
        i_spikes = self.i.step(self.i_i)

        # I inhibits E
        if i_spikes.size > 0:
            inh_current = self.w_ie * (i_spikes.size / max(1, self.i.n))
            self.e.inject_current(np.arange(self.e.n), -inh_current)

        # Decay buffers (no persistent buffers in this simplified model)
        self.i_e.fill(0.0)
        self.i_i.fill(0.0)

        self.total_ticks += 1
        return e_spikes, i_spikes

    def get_power(self) -> float:
        """Return a simple gamma power estimate as recent E firing fraction."""
        return float(self.e.activity_pct / 100.0)

    def snapshot(self) -> Dict:
        return {
            "e_n": self.e.n,
            "i_n": self.i.n,
            "e_activity_pct": round(float(self.e.activity_pct), 3),
            "i_activity_pct": round(float(self.i.activity_pct), 3),
        }


def create_ping_gamma(n_exc: int = 200, n_inh: int = 50) -> PINGGamma:
    return PINGGamma(n_exc=n_exc, n_inh=n_inh)


if __name__ == "__main__":
    p = create_ping_gamma(300, 80)
    for i in range(200):
        p.step(0.1, ext_drive=5.0)
        if i % 20 == 0:
            print(p.snapshot())
