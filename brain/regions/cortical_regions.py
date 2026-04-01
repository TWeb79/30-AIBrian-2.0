"""
regions.py — Modular Brain Regions
===================================
Each region wraps a LIFPopulation and exposes a clean step() interface.
Regions are wired together by SparseSTDPSynapses in brain.py.

Hierarchy:
  SensoryRegion  → FeatureLayer → AssociationRegion
  AssociationRegion ↔ PredictiveRegion
  AssociationRegion  → ConceptLayer  (WTA)
  ConceptLayer       → MetaControl
  MetaControl        → WorkingMemory
  Any region motor output → ReflexArc → actuator
  Cerebellum / Brainstem: homeostatic support
"""

import numpy as np
from typing import Optional
from brain.neurons import LIFPopulation, LIFParams, PoissonEncoder
from brain.synapses import InhibitorySynapse, STDPParams


# ─── Base Region ──────────────────────────────────────────────────────────────

class BrainRegion:
    """Abstract base for all neuronal regions."""

    COLOR  = "#ffffff"
    LABEL  = "Region"

    def __init__(self, name: str, n: int, params: Optional[LIFParams] = None):
        self.name       = name
        self.population = LIFPopulation(n, params, name=name)
        self.last_spikes: np.ndarray = np.array([], dtype=np.int32)
        self._gain      = 1.0        # attention gain from predictive loop

    @property
    def n(self) -> int:
        return self.population.n

    @property
    def activity_pct(self) -> float:
        return self.population.activity_pct

    def step(self, i_syn: np.ndarray) -> np.ndarray:
        """Advance one timestep; return spike indices."""
        spikes = self.population.step(i_syn)
        self.last_spikes = spikes
        return spikes

    def set_gain(self, gain: float):
        self._gain = float(np.clip(gain, 0.5, 10.0))

    def snapshot(self) -> dict:
        pop = self.population
        return {
            "name":         self.name,
            "n_neurons":    self.n,
            "activity_pct": round(self.activity_pct, 2),
            "firing_rate":  round(pop.firing_rate * 1000, 2),  # Hz
            "total_spikes": int(pop.spike_count.sum()),
            "gain":         round(self._gain, 3),
        }


# ─── Sensory Cortex ───────────────────────────────────────────────────────────

class SensoryCortex(BrainRegion):
    """
    Multimodal sensory gateway.
    Converts raw stimuli (vision, audio, touch) to Poisson spike trains.
    Each modality occupies a separate neuron subgroup.
    """
    COLOR = "#4dffb4"
    LABEL = "Sensory Cortex"

    MODALITIES = {"vision": 0.4, "audio": 0.3, "touch": 0.3}  # fraction of n

    def __init__(self, n: int = 40_000):
        super().__init__("sensory", n, LIFParams(tau_m=15.0))
        self.encoder  = PoissonEncoder(dt=0.1, max_rate_hz=80.0)
        # Subgroup ranges
        self._ranges = {}
        start = 0
        for mod, frac in self.MODALITIES.items():
            end = start + int(n * frac)
            self._ranges[mod] = (start, min(end, n))
            start = end

    def stimulate(self, modality: str, stimulus: np.ndarray):
        """
        Inject sensory stimulus into a modality subgroup.
        stimulus: normalised [0,1] array of length matching subgroup size.
        """
        if modality not in self._ranges:
            return
        lo, hi = self._ranges[modality]
        size   = hi - lo
        if stimulus.size != size:
            stimulus = np.interp(
                np.linspace(0, 1, size),
                np.linspace(0, 1, stimulus.size),
                stimulus
            )
        spikes_bool = self.encoder.encode(np.clip(stimulus, 0, 1))
        fired_local = np.where(spikes_bool)[0] + lo
        self.population.inject_current(fired_local, 20.0)


# ─── Feature Layer ────────────────────────────────────────────────────────────

class FeatureLayer(BrainRegion):
    """
    Low-level feature extraction (edges, phonemes, pressure gradients).
    First hidden layer above raw sensory input.
    """
    COLOR = "#00cfff"
    LABEL = "Feature Layer"

    def __init__(self, n: int = 80_000):
        super().__init__("feature", n, LIFParams(tau_m=18.0))


# ─── Association Region ───────────────────────────────────────────────────────

class AssociationRegion(BrainRegion):
    """
    The brain's integration hub.
    Binds cross-modal features via STDP.
    500k neurons — largest region.
    """
    COLOR = "#00ffc8"
    LABEL = "Association"

    def __init__(self, n: int = 500_000):
        super().__init__("association", n, LIFParams(tau_m=22.0, tau_ref=3.0))


# ─── Predictive Region ────────────────────────────────────────────────────────

class PredictiveRegion(BrainRegion):
    """
    Continuous prediction engine.

    Maintains a running prediction of the next sensory state.
    Computes prediction error → broadcasts attention gain to other regions.
    High error  → curiosity signal → accelerated STDP everywhere.
    """
    COLOR = "#ffb300"
    LABEL = "Predictive"

    def __init__(self, n: int = 100_000):
        super().__init__("predictive", n, LIFParams(tau_m=25.0))
        self._prediction   = np.zeros(n, dtype=np.float32)
        self.error         = 0.0
        self.attention_gain = 1.0
        self._alpha         = 0.05   # prediction update rate

    def compute_error(self, actual_activity: float) -> float:
        """
        Simple scalar error between predicted and actual firing rate.
        In a full system this would compare spike pattern vectors.
        """
        predicted = float(self._prediction.mean())
        self.error = abs(actual_activity - predicted)

        # Update prediction via exponential moving average
        self._prediction *= (1 - self._alpha)
        self._prediction += self._alpha * actual_activity

        # Translate error into attention gain [1.0, 5.0]
        self.attention_gain = 1.0 + 4.0 * min(self.error * 50.0, 1.0)
        return self.attention_gain

    def snapshot(self) -> dict:
        s = super().snapshot()
        s["prediction_error"]  = round(self.error, 4)
        s["attention_gain"]    = round(self.attention_gain, 3)
        return s


# ─── Concept Layer ────────────────────────────────────────────────────────────

class ConceptLayer(BrainRegion):
    """
    Sparse, abstract concept representation.
    5,800 neurons with lateral inhibition → Winner-Take-All.
    Only 3-5 neurons fire per concept (sparse coding).
    """
    COLOR = "#fd79a8"
    LABEL = "Concept Layer"

    def __init__(self, n: int = 5_800):
        super().__init__("concept", n, LIFParams(tau_m=30.0, v_thresh=-52.0))
        self.inhibition  = InhibitorySynapse(n, strength=8.0)
        self._concept_id = -1

    def step(self, i_syn: np.ndarray) -> np.ndarray:
        # Lateral inhibition applied before membrane integration
        i_inh  = self.inhibition.lateral_inhibit(self.last_spikes)
        spikes = self.population.step(i_syn + i_inh)
        self.last_spikes = spikes
        if spikes.size > 0:
            self._concept_id = int(spikes[0])   # winning neuron ID
        return spikes

    @property
    def active_concept(self) -> int:
        return self._concept_id

    def snapshot(self) -> dict:
        s = super().snapshot()
        s["active_concept_neuron"] = self._concept_id
        return s


# ─── Meta Control ─────────────────────────────────────────────────────────────

class MetaControl(BrainRegion):
    """
    Top-down attention and task switching.
    Modulates gain across other regions based on current goals.
    """
    COLOR = "#b36bff"
    LABEL = "Meta Control"

    def __init__(self, n: int = 60_000):
        super().__init__("meta_control", n, LIFParams(tau_m=30.0, tau_ref=4.0))


# ─── Working Memory ───────────────────────────────────────────────────────────

class WorkingMemory(BrainRegion):
    """
    Short-term spike pattern buffer.
    Maintains persistent activity via recurrent connections.
    """
    COLOR = "#ff9f43"
    LABEL = "Working Memory"

    def __init__(self, n: int = 20_000):
        super().__init__("working_memory", n, LIFParams(tau_m=50.0, tau_ref=2.0))
        # Recurrent self-excitation buffer
        self._buffer: list[np.ndarray] = []
        self._buf_len = 10   # steps to hold pattern

    def hold(self, spikes: np.ndarray):
        self._buffer.append(spikes.copy())
        if len(self._buffer) > self._buf_len:
            self._buffer.pop(0)

    def recall(self) -> np.ndarray:
        if not self._buffer:
            return np.array([], dtype=np.int32)
        return np.concatenate(self._buffer)


# ─── Cerebellum ───────────────────────────────────────────────────────────────

class Cerebellum(BrainRegion):
    """
    Fine motor timing, sequence learning, error-based correction.
    Uses eligibility traces (simplified).
    """
    COLOR = "#a8e6cf"
    LABEL = "Cerebellum"

    def __init__(self, n: int = 15_000):
        super().__init__("cerebellum", n, LIFParams(tau_m=12.0, tau_ref=1.5))


# ─── Brainstem ────────────────────────────────────────────────────────────────

class Brainstem(BrainRegion):
    """
    Homeostatic regulation, baseline arousal, autonomic functions.
    Provides constant low-level drive to keep the network alive.
    """
    COLOR = "#ffeaa7"
    LABEL = "Brainstem"

    BASELINE_CURRENT = 2.5   # pA always-on drive

    def __init__(self, n: int = 8_000):
        super().__init__("brainstem", n, LIFParams(tau_m=40.0))
        # Permanent baseline injection
        self.population.i_ext[:] = self.BASELINE_CURRENT


# ─── Reflex Arc (Safety Kernel) ───────────────────────────────────────────────

class ReflexArc(BrainRegion):
    """
    SAFETY KERNEL — hard-gated motor output supervisor.

    Every motor command MUST pass through check_command() before
    execution.  If safety constraints are violated, a withdrawal
    reflex fires and the command is blocked.  No ML model can
    bypass these hard limits.

    Constraints checked:
      • force     < FORCE_MAX   (N)
      • angle     < JOINT_LIMIT (degrees)
      • velocity  < VEL_MAX     (m/s)
    """
    COLOR = "#ff4d6d"
    LABEL = "Reflex Arc"

    FORCE_MAX   = 10.0    # N
    JOINT_LIMIT = 170.0   # degrees
    VEL_MAX     = 2.0     # m/s

    def __init__(self, n: int = 30_000):
        super().__init__("reflex_arc", n, LIFParams(tau_m=5.0, tau_ref=1.0))
        self.blocked_count  = 0
        self.passed_count   = 0
        self.last_decision  = "NONE"

    def check_command(self, cmd: dict) -> dict:
        """
        Intercept motor command before execution.

        Parameters
        ----------
        cmd : dict with optional keys: force, angle, velocity

        Returns
        -------
        result : dict  { approved: bool, command: dict, reason: str }
        """
        force    = abs(cmd.get("force",    0.0))
        angle    = abs(cmd.get("angle",    0.0))
        velocity = abs(cmd.get("velocity", 0.0))

        violations = []
        if force    > self.FORCE_MAX:   violations.append(f"force={force:.1f}N > {self.FORCE_MAX}N")
        if angle    > self.JOINT_LIMIT: violations.append(f"angle={angle:.1f}° > {self.JOINT_LIMIT}°")
        if velocity > self.VEL_MAX:     violations.append(f"vel={velocity:.2f} > {self.VEL_MAX} m/s")

        if violations:
            self.blocked_count += 1
            self.last_decision  = "BLOCKED"
            # Trigger withdrawal reflex (activate high-priority safety neurons)
            reflex_idx = np.random.choice(self.n, size=min(100, self.n), replace=False)
            self.population.inject_current(reflex_idx, 50.0)
            return {
                "approved": False,
                "command":  {"force": 0.0, "angle": 0.0, "velocity": 0.0},
                "reason":   "REFLEX_WITHDRAWAL: " + "; ".join(violations),
            }

        self.passed_count  += 1
        self.last_decision  = "APPROVED"
        return {"approved": True, "command": cmd, "reason": "SAFE"}

    def snapshot(self) -> dict:
        s = super().snapshot()
        s["blocked"]       = self.blocked_count
        s["passed"]        = self.passed_count
        s["last_decision"] = self.last_decision
        return s
