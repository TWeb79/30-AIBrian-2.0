"""
neurons.py — Leaky Integrate-and-Fire (LIF) Neuron Model
=========================================================
Pure NumPy event-driven implementation.
No dense matrix ops; only sparse spike indices propagated.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LIFParams:
    """Biological LIF parameters (SI units)."""
    tau_m:      float = 20.0    # ms  membrane time constant
    tau_ref:    float =  2.0    # ms  refractory period
    v_rest:     float = -70.0   # mV  resting potential
    v_reset:    float = -70.0   # mV  reset after spike
    v_thresh:   float = -55.0   # mV  spike threshold
    v_peak:     float =  30.0   # mV  spike peak (cosmetic)
    r_m:        float =  10.0   # MΩ  membrane resistance
    dt:         float =   0.1   # ms  simulation timestep


class LIFPopulation:
    """
    Vectorised LIF neuron population.

    All computation is NumPy; spike events are returned as integer
    index arrays so downstream synapses only process firing neurons.
    """

    def __init__(self, n: int, params: Optional[LIFParams] = None, name: str = ""):
        self.n      = n
        self.name   = name
        self.p      = params or LIFParams()

        # State vectors
        self.v          = np.full(n, self.p.v_rest, dtype=np.float32)
        self.refractory = np.zeros(n, dtype=np.float32)   # remaining ref. time
        self.i_ext      = np.zeros(n, dtype=np.float32)   # external current (pA)

        # Monitoring
        self.spike_count    = np.zeros(n, dtype=np.int64)
        self.last_spike_t   = np.full(n, -np.inf, dtype=np.float64)
        self.t              = 0.0   # current sim time (ms)

        # Activity trace (exponential decay) for STDP
        self.trace = np.zeros(n, dtype=np.float32)

    # ------------------------------------------------------------------
    def step(self, i_syn: np.ndarray) -> np.ndarray:
        """
        Advance one timestep.

        Parameters
        ----------
        i_syn : (n,) array of total synaptic current (pA)

        Returns
        -------
        spike_idx : indices of neurons that fired this step
        """
        dt = self.p.dt
        self.t += dt

        # Neurons in refractory are clamped
        in_ref = self.refractory > 0.0
        self.refractory = np.maximum(0.0, self.refractory - dt)

        # LIF voltage update (Euler)
        dv = (-(self.v - self.p.v_rest) + self.p.r_m * (i_syn + self.i_ext)) / self.p.tau_m
        self.v += dv * dt
        self.v[in_ref] = self.p.v_reset   # clamp refractory neurons

        # Spike detection
        fired = np.where(self.v >= self.p.v_thresh)[0]

        if fired.size > 0:
            self.v[fired]           = self.p.v_reset
            self.refractory[fired]  = self.p.tau_ref
            self.spike_count[fired] += 1
            self.last_spike_t[fired] = self.t

        # Update STDP eligibility trace
        self.trace += (-self.trace / 20.0) * dt    # 20 ms decay
        self.trace[fired] += 1.0

        return fired

    # ------------------------------------------------------------------
    def inject_current(self, idx: np.ndarray, magnitude: float):
        """External current injection (e.g. sensory drive)."""
        self.i_ext[idx] += magnitude

    def reset_external(self):
        self.i_ext[:] = 0.0

    @property
    def firing_rate(self) -> float:
        """Mean population firing rate (spikes / neuron / ms)."""
        if self.t == 0:
            return 0.0
        return float(self.spike_count.sum()) / (self.n * self.t)

    @property
    def activity_pct(self) -> float:
        """% neurons that fired in the last step (approx from trace)."""
        return float((self.trace > 0.5).sum()) / self.n * 100.0


class PoissonEncoder:
    """
    Converts a real-valued stimulus vector [0,1] into Poisson spike trains.
    Used at the sensory boundary.
    """

    def __init__(self, dt: float = 0.1, max_rate_hz: float = 100.0):
        self.dt          = dt            # ms
        self.max_rate    = max_rate_hz   # Hz

    def encode(self, stimulus: np.ndarray) -> np.ndarray:
        """
        Parameters
        ----------
        stimulus : (n,) float array, values in [0, 1]

        Returns
        -------
        spikes : (n,) bool array
        """
        rates   = stimulus * self.max_rate                   # Hz
        p_spike = rates * (self.dt / 1000.0)                 # per timestep
        return np.random.rand(stimulus.size) < p_spike


class RateEncoder:
    """
    Converts discrete token IDs into graded current injections.
    Used for text/concept input.
    """

    def __init__(self, vocab_size: int, n_neurons: int):
        # Random projection: token → neuron subset
        rng   = np.random.default_rng(42)
        # Each token maps to a sparse subset of neurons
        k     = max(1, n_neurons // vocab_size)
        self.mapping = {}
        all_idx      = np.arange(n_neurons)
        for tok in range(vocab_size):
            self.mapping[tok] = rng.choice(all_idx, size=k, replace=False)

    def encode(self, token_ids: list[int], n_neurons: int) -> np.ndarray:
        current = np.zeros(n_neurons, dtype=np.float32)
        for tid in token_ids:
            if tid in self.mapping:
                current[self.mapping[tid]] += 5.0
        return current
