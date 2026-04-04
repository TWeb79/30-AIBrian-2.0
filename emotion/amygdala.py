"""
emotion/amygdala.py — Amygdala-like fast tagging population
============================================================
Provides a compact LIF population used to compute a fast "amygdala_score"
that biases hippocampal encoding and proactive thought selection.
"""

import numpy as np
from brain.neurons import LIFPopulation, LIFParams


class AmygdalaRegion:
    """Small fast-spiking LIF population for emotional tagging."""

    def __init__(self, n: int = 2000):
        # scale down LIF params for fast response
        self.n = n
        self.population = LIFPopulation(n, LIFParams(tau_m=10.0, tau_ref=1.0, v_thresh=-47.0), name="amygdala")
        # Rolling amygdala score (0.0-1.0)
        self.score = 0.0

    def step(self, input_current: np.ndarray) -> np.ndarray:
        """Advance amygdala population and update score.

        input_current should be size n; high-salience inputs produce a higher score.
        """
        if input_current is None:
            input_current = np.zeros(self.n, dtype=np.float32)
        spikes = self.population.step(input_current)
        # Score is fraction of neurons that fired in this step (smoothed)
        recent_frac = float((self.population.trace > 0.5).sum()) / max(1, self.n)
        # Exponential smoothing
        self.score = 0.9 * self.score + 0.1 * recent_frac
        return spikes

    def get_score(self) -> float:
        return float(np.clip(self.score, 0.0, 1.0))

    def snapshot(self) -> dict:
        return {"n": self.n, "score": round(self.get_score(), 3), "activity_pct": round(self.population.activity_pct, 3)}


def create_amygdala(n: int = 2000) -> AmygdalaRegion:
    return AmygdalaRegion(n)
