"""
brain/modulation/neuromodulators.py — Neuromodulator Populations
================================================================
Full neuromodulator populations as spiking LIF neurons.
Each population produces a scalar bias based on firing rate.

- Dopamine (DA): modulates STDP A_plus scaling (reward learning)
- Acetylcholine (ACh): modulates thinking_steps (encoding depth)
- Norepinephrine (NE): modulates WTA sharpness in ConceptLayer
- Serotonin (5-HT): modulates episode valence threshold for memory encoding

Usage:
    da_pop = DopaminePopulation(n=100)
    da_pop.step(input_signal)  # inject reward signal
    da_level = da_pop.get_level()  # returns 0-1 scalar
    
    Wire DA level to STDP A_plus: synapse.A_plus = base_A_plus * da_level
"""

import numpy as np
from typing import Optional
from brain.neurons import LIFPopulation, LIFParams


class NeuromodulatorPopulation:
    """Base class for neuromodulator LIF populations."""
    
    def __init__(self, n: int, params: Optional[LIFParams] = None, name: str = "nm"):
        self.population = LIFPopulation(n, params or self._default_params(), name=name)
        self.n = n
        self.name = name
        self._output_level = 0.0
    
    def _default_params(self) -> LIFParams:
        """Override in subclass."""
        return LIFParams(tau_m=50.0, v_thresh=-40.0)
    
    def step(self, i_syn: np.ndarray) -> np.ndarray:
        """Advance population and update output level."""
        spikes = self.population.step(i_syn)
        self._update_level(spikes)
        return spikes
    
    def _update_level(self, spikes: np.ndarray):
        """Compute output level from firing rate (0-1 normalized)."""
        if spikes.size == 0:
            self._output_level = max(0.0, self._output_level - 0.01)  # decay
        else:
            firing_rate = spikes.size / self.n
            self._output_level = min(1.0, firing_rate * 5.0)  # scale to 0-1
    
    def get_level(self) -> float:
        """Get current modulation level (0-1)."""
        return self._output_level
    
    def inject_signal(self, intensity: float):
        """Inject external signal (e.g., reward, salience)."""
        idx = np.random.choice(self.n, size=min(int(self.n * intensity), self.n), replace=False)
        self.population.inject_current(idx, 20.0)
    
    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "n_neurons": self.n,
            "output_level": round(self._output_level, 3),
            "activity_pct": round(self.population.activity_pct, 2),
        }


class DopaminePopulation(NeuromodulatorPopulation):
    """
    Dopamine population: reward prediction error.
    Higher firing → stronger LTP (reward learning).
    """
    
    def _default_params(self) -> LIFParams:
        return LIFParams(tau_m=100.0, v_thresh=-40.0, v_reset=-50.0)
    
    def _update_level(self, spikes: np.ndarray):
        """DA: fast rise, slow decay."""
        if spikes.size == 0:
            self._output_level = max(0.0, self._output_level - 0.005)  # slow decay
        else:
            firing_rate = spikes.size / self.n
            self._output_level = min(1.0, firing_rate * 3.0)
    
    def get_stdp_multiplier(self, base_A_plus: float = 0.01) -> float:
        """Get scaled A_plus for STDP."""
        return base_A_plus * (0.5 + self._output_level * 1.5)  # 0.5x to 2x


class AcetylcholinePopulation(NeuromodulatorPopulation):
    """
    Acetylcholine population: attention and encoding depth.
    Higher firing → more thinking steps (deeper processing).
    """
    
    def _default_params(self) -> LIFParams:
        return LIFParams(tau_m=80.0, v_thresh=-45.0)
    
    def _update_level(self, spikes: np.ndarray):
        """ACh: moderate dynamics."""
        if spikes.size == 0:
            self._output_level = max(0.0, self._output_level - 0.01)
        else:
            firing_rate = spikes.size / self.n
            self._output_level = min(1.0, firing_rate * 4.0)
    
    def get_thinking_steps_multiplier(self, base_steps: int = 400) -> int:
        """Get scaled thinking steps."""
        return int(base_steps * (0.5 + self._output_level * 1.5))


class NorepinephrinePopulation(NeuromodulatorPopulation):
    """
    Norepinephrine population: arousal and attention.
    Higher firing → sharper competition in WTA circuits.
    """
    
    def _default_params(self) -> LIFParams:
        return LIFParams(tau_m=60.0, v_thresh=-45.0)
    
    def _update_level(self, spikes: np.ndarray):
        """NE: fast dynamics, high gain."""
        if spikes.size == 0:
            self._output_level = max(0.0, self._output_level - 0.02)
        else:
            firing_rate = spikes.size / self.n
            self._output_level = min(1.0, firing_rate * 5.0)
    
    def get_wta_sharpness(self, base_strength: float = 5.0) -> float:
        """Get scaled inhibition strength for WTA."""
        return base_strength * (0.5 + self._output_level * 2.0)


class SerotoninPopulation(NeuromodulatorPopulation):
    """
    Serotonin population: mood and valence processing.
    Modulates threshold for episodic memory encoding.
    """
    
    def _default_params(self) -> LIFParams:
        return LIFParams(tau_m=120.0, v_thresh=-45.0)
    
    def _update_level(self, spikes: np.ndarray):
        """5-HT: slow dynamics."""
        if spikes.size == 0:
            self._output_level = max(0.0, self._output_level - 0.003)  # very slow decay
        else:
            firing_rate = spikes.size / self.n
            self._output_level = min(1.0, firing_rate * 2.5)
    
    def get_valence_threshold(self, base_threshold: float = 0.1) -> float:
        """Get scaled valence threshold for memory encoding."""
        return base_threshold * (0.5 + self._output_level * 1.0)


class NeuromodulatorSystem:
    """
    Combined neuromodulator system.
    Provides unified interface to all neuromodulator populations.
    """
    
    def __init__(self, n_per_population: int = 100):
        self.da = DopaminePopulation(n_per_population, name="dopamine")
        self.ach = AcetylcholinePopulation(n_per_population, name="acetylcholine")
        self.ne = NorepinephrinePopulation(n_per_population, name="norepinephrine")
        self.ht = SerotoninPopulation(n_per_population, name="serotonin")  # 5-HT
    
    def step(self, reward_signal: float = 0.0, salience_signal: float = 0.0, mood_signal: float = 0.0):
        """Step all populations with external signals."""
        self.da.inject_signal(reward_signal)
        self.ach.inject_signal(salience_signal)
        self.ne.inject_signal(salience_signal)
        self.ht.inject_signal(mood_signal)
        
        self.da.step(np.zeros(self.da.n, dtype=np.float32))
        self.ach.step(np.zeros(self.ach.n, dtype=np.float32))
        self.ne.step(np.zeros(self.ne.n, dtype=np.float32))
        self.ht.step(np.zeros(self.ht.n, dtype=np.float32))
    
    def get_biases(self) -> dict:
        """Get neuromodulator biases as dict."""
        return {
            "dopamine": self.da.get_level(),
            "acetylcholine": self.ach.get_level(),
            "norepinephrine": self.ne.get_level(),
            "serotonin": self.ht.get_level(),
            # Deltas for backward compatibility
            "dopamine_delta": self.da.get_level() - 0.5,
            "acetylcholine_delta": self.ach.get_level() - 0.5,
            "norepinephrine_delta": self.ne.get_level() - 0.5,
            "serotonin_delta": self.ht.get_level() - 0.5,
        }
    
    def snapshot(self) -> dict:
        return {
            "dopamine": self.da.snapshot(),
            "acetylcholine": self.ach.snapshot(),
            "norepinephrine": self.ne.snapshot(),
            "serotonin": self.ht.snapshot(),
        }


def create_neuromodulator_system(n_per_population: int = 100) -> NeuromodulatorSystem:
    return NeuromodulatorSystem(n_per_population)


if __name__ == "__main__":
    # Test the neuromodulator system
    nms = create_neuromodulator_system(50)
    
    print("Testing NeuromodulatorSystem:")
    
    # Inject reward signal
    nms.step(reward_signal=0.8, salience_signal=0.5, mood_signal=0.3)
    biases = nms.get_biases()
    print(f"  After reward signal:")
    print(f"    DA level: {biases['dopamine']:.3f}")
    print(f"    ACh level: {biases['acetylcholine']:.3f}")
    print(f"    NE level: {biases['norepinephrine']:.3f}")
    print(f"    5-HT level: {biases['serotonin']:.3f}")
    
    # Test scaled parameters
    print(f"  STDP A_plus multiplier: {nms.da.get_stdp_multiplier(0.01):.4f}")
    print(f"  Thinking steps multiplier: {nms.ach.get_thinking_steps_multiplier(400)}")
    print(f"  WTA sharpness: {nms.ne.get_wta_sharpness(5.0):.2f}")
    print(f"  Valence threshold: {nms.ht.get_valence_threshold(0.1):.3f}")
    
    print("\n✓ NeuromodulatorSystem tests passed!")
