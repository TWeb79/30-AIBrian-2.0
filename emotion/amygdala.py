"""
emotion/amygdala.py — Amygdala-like fast tagging population
============================================================
Provides a compact LIF population used to compute a fast "amygdala_score"
that biases hippocampal encoding and proactive thought selection.
"""

import numpy as np


class AmygdalaRegion:
    """Compact amygdala-like population implemented without importing brain.neurons to avoid circular imports.

    This implements a lightweight spiking-like trace and score computed from input_current.
    """

    def __init__(self, n: int = 2000):
        self.n = int(n)
        # simple per-neuron trace (exponentially decaying)
        self.trace = np.zeros(self.n, dtype=np.float32)
        # last spikes (indices)
        self.last_spikes = np.array([], dtype=np.int32)
        self.activity_pct = 0.0
        # Rolling amygdala score (0.0-1.0)
        self.score = 0.0

    def step(self, input_current: np.ndarray) -> np.ndarray:
        """Advance the simple amygdala population and update score.

        input_current: numpy array len n, or None -> treated as zeros
        Returns an array of spike indices (simulated)
        """
        if input_current is None:
            input_current = np.zeros(self.n, dtype=np.float32)
        # ensure correct shape
        if input_current.shape[0] != self.n:
            # safely broadcast or clip
            ic = np.zeros(self.n, dtype=np.float32)
            ic[:min(self.n, input_current.shape[0])] = input_current[:min(self.n, input_current.shape[0])]
            input_current = ic

        # Simple probabilistic spiking: probability proportional to input_current (scaled)
        prob = 1.0 - np.exp(-np.maximum(input_current, 0.0) * 0.1)
        rand = np.random.rand(self.n)
        spikes_mask = rand < prob
        spike_indices = np.nonzero(spikes_mask)[0].astype(np.int32)
        # update trace: decay + spikes
        self.trace *= 0.9
        self.trace[spike_indices] += 1.0
        # update last_spikes and activity
        self.last_spikes = spike_indices
        self.activity_pct = 100.0 * float(spike_indices.size) / max(1, self.n)
        recent_frac = float((self.trace > 0.5).sum()) / max(1, self.n)
        self.score = 0.9 * self.score + 0.1 * recent_frac
        return spike_indices

    def get_score(self) -> float:
        return float(np.clip(self.score, 0.0, 1.0))

    def snapshot(self) -> dict:
        return {"n": self.n, "score": round(self.get_score(), 3), "activity_pct": round(self.activity_pct, 3)}


def create_amygdala(n: int = 2000) -> AmygdalaRegion:
    return AmygdalaRegion(n)
