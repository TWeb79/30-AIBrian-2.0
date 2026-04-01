"""
synapses.py — Spike-Timing-Dependent Plasticity (STDP) Synapses
================================================================
Implements local, unsupervised Hebbian learning via STDP.
All weight updates are purely event-driven (fire → update).

STDP Rule:
  Δw > 0  (LTP)  if  t_pre < t_post  (pre fires before post)
  Δw < 0  (LTD)  if  t_pre > t_post  (post fires before pre)

  A_plus  · exp(-Δt / tau_plus)   for LTP
  A_minus · exp(-Δt / tau_minus)  for LTD
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class STDPParams:
    A_plus:    float = 0.01     # LTP amplitude
    A_minus:   float = 0.0105   # LTD amplitude  (slightly > LTP → weight decay)
    tau_plus:  float = 20.0     # ms LTP time window
    tau_minus: float = 20.0     # ms LTD time window
    w_min:     float = 0.0      # minimum synaptic weight
    w_max:     float = 1.0      # maximum synaptic weight
    lr:        float = 1.0      # global learning rate multiplier


class SparseSTDPSynapse:
    """
    Sparse STDP synapse connecting two LIFPopulations.

    Uses COO-style (pre_idx, post_idx, weight) storage so only
    active synapses are touched — no dense N×M matrix.
    """

    def __init__(
        self,
        pre_n:   int,
        post_n:  int,
        p:       float = 0.05,
        params:  Optional[STDPParams] = None,
        name:    str = "",
        rng_seed: int = 0,
    ):
        self.pre_n  = pre_n
        self.post_n = post_n
        self.name   = name
        self.p      = params or STDPParams()

        rng = np.random.default_rng(rng_seed)

        # Build sparse connectivity
        total_possible = pre_n * post_n
        n_synapses = int(total_possible * p)
        n_synapses = min(n_synapses, 5_000_000)   # cap for memory

        self.pre_idx  = rng.integers(0, pre_n,  size=n_synapses).astype(np.int32)
        self.post_idx = rng.integers(0, post_n, size=n_synapses).astype(np.int32)
        self.weights  = rng.uniform(0.05, 0.5, size=n_synapses).astype(np.float32)

        # Per-synapse eligibility traces
        self.pre_trace  = np.zeros(n_synapses, dtype=np.float32)
        self.post_trace = np.zeros(n_synapses, dtype=np.float32)

        # Stats
        self.total_ltp = 0.0
        self.total_ltd = 0.0
        self.n_updates = 0

    # ------------------------------------------------------------------
    @property
    def n_synapses(self) -> int:
        return self.weights.size

    # ------------------------------------------------------------------
    def propagate(self, pre_spikes: np.ndarray, scale: float = 1.0) -> np.ndarray:
        """
        Compute post-synaptic current from pre-synaptic spikes.

        Parameters
        ----------
        pre_spikes : indices of pre-synaptic neurons that fired
        scale      : gain multiplier (from predictive attention)

        Returns
        -------
        i_post : (post_n,) current array
        """
        if pre_spikes.size == 0:
            return np.zeros(self.post_n, dtype=np.float32)

        # Mask synapses whose pre neuron fired
        fired_mask = np.isin(self.pre_idx, pre_spikes)
        active_post = self.post_idx[fired_mask]
        active_w    = self.weights[fired_mask] * scale

        i_post = np.zeros(self.post_n, dtype=np.float32)
        np.add.at(i_post, active_post, active_w * 100.0)   # 100 pA/weight unit
        return i_post

    # ------------------------------------------------------------------
    def update_stdp(
        self,
        pre_spikes:  np.ndarray,
        post_spikes: np.ndarray,
        pre_trace:   np.ndarray,   # from LIFPopulation.trace
        post_trace:  np.ndarray,
        dt:          float = 0.1,
        gain:        float = 1.0,  # attention gain from predictive loop
    ):
        """
        Apply STDP weight updates using population eligibility traces.
        Event-driven: only synapses touching fired neurons are updated.
        """
        if pre_spikes.size == 0 and post_spikes.size == 0:
            return

        p = self.p
        lr_eff = p.lr * gain

        # LTP: post neuron fired → reward synapses with active pre traces
        if post_spikes.size > 0:
            post_mask = np.isin(self.post_idx, post_spikes)
            if post_mask.any():
                pre_tr = pre_trace[self.pre_idx[post_mask]]
                dw     = p.A_plus * pre_tr * lr_eff
                self.weights[post_mask] = np.clip(
                    self.weights[post_mask] + dw, p.w_min, p.w_max
                )
                self.total_ltp += dw.sum()

        # LTD: pre neuron fired → penalise synapses with active post traces
        if pre_spikes.size > 0:
            pre_mask = np.isin(self.pre_idx, pre_spikes)
            if pre_mask.any():
                post_tr = post_trace[self.post_idx[pre_mask]]
                dw      = p.A_minus * post_tr * lr_eff
                self.weights[pre_mask] = np.clip(
                    self.weights[pre_mask] - dw, p.w_min, p.w_max
                )
                self.total_ltd += dw.sum()

        self.n_updates += 1

    # ------------------------------------------------------------------
    def decay_traces(self, dt: float, tau: float = 20.0):
        self.pre_trace  -= (self.pre_trace  / tau) * dt
        self.post_trace -= (self.post_trace / tau) * dt

    def mean_weight(self) -> float:
        return float(self.weights.mean())

    def weight_histogram(self, bins: int = 10) -> dict:
        hist, edges = np.histogram(self.weights, bins=bins, range=(0, 1))
        return {"counts": hist.tolist(), "edges": edges.tolist()}


class InhibitorySynapse:
    """
    Fast lateral inhibition — no STDP, fixed negative weights.
    Used in Winner-Take-All (Concept Layer).
    """

    def __init__(self, n: int, strength: float = 5.0):
        self.n        = n
        self.strength = strength

    def lateral_inhibit(self, spikes: np.ndarray) -> np.ndarray:
        """
        Any neuron that fires suppresses all others.
        Returns a current vector (negative = inhibitory).
        """
        if spikes.size == 0:
            return np.zeros(self.n, dtype=np.float32)
        i_inh = np.full(self.n, -self.strength * 100.0, dtype=np.float32)
        i_inh[spikes] = 0.0   # winners not inhibited
        return i_inh
