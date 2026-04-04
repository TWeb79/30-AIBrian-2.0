"""
brain/oscillations/theta.py — Theta Oscillation Pacemaker
===========================================================
Minimal theta pacemaker for phase-gated STDP.
Implements a simplified septal theta oscillator (8 Hz / 125ms period).

No Brian2 required — pure NumPy implementation.

Usage:
    theta = SeptalThetaPacemaker()
    phase = theta.tick(dt_ms=0.1)  # Call each simulation step
    if theta.is_encoding_window():
        # STDP should be applied
        syn.update_stdp(...)
"""

import numpy as np
from typing import Dict


class SeptalThetaPacemaker:
    """
    Simplified theta oscillator modeling septal input to hippocampus.
    
    Generates a sinusoidal theta phase signal (8 Hz default).
    Provides phase-gated windows for encoding vs retrieval.
    
    Biological basis:
    - Medial septum fires at theta frequency (4-12 Hz)
    - Theta phase determines whether CA1 pyramidal cells
      undergo LTP or LTD (encoding vs retrieval)
    """
    
    THETA_PERIOD_MS = 125.0  # 8 Hz
    THETA_FREQ_HZ = 8.0
    
    def __init__(
        self,
        theta_period_ms: float = THETA_PERIOD_MS,
        phase_offset: float = 0.0,
    ):
        """
        Parameters
        ----------
        theta_period_ms : float
            Period of theta oscillation in milliseconds
        phase_offset : float
            Initial phase offset (0-1)
        """
        self.theta_period_ms = theta_period_ms
        self.phase = phase_offset % 1.0
        self._time_accumulator_ms = 0.0
        
        # Statistics
        self.total_ticks = 0
        self.encoding_windows = 0
    
    def tick(self, dt_ms: float) -> float:
        """
        Advance theta phase by timestep.
        
        Parameters
        ----------
        dt_ms : float
            Time step in milliseconds
            
        Returns
        -------
        float
            Current theta phase (0-1)
        """
        self._time_accumulator_ms += dt_ms
        
        # Update phase based on elapsed time
        self.phase = (self._time_accumulator_ms / self.theta_period_ms) % 1.0
        self.total_ticks += 1
        
        if self.is_encoding_window():
            self.encoding_windows += 1
            
        return self.phase
    
    def get_phase(self) -> float:
        """Get current phase (0-1)."""
        return self.phase
    
    def get_phase_rad(self) -> float:
        """Get current phase in radians (0-2π)."""
        return 2 * np.pi * self.phase
    
    def get_theta_power(self) -> float:
        """Get current theta amplitude (sin wave)."""
        return np.sin(2 * np.pi * self.phase)
    
    def is_encoding_window(self) -> bool:
        """
        Returns True if current phase is in encoding window.
        
        First half of theta cycle (phase 0-0.5) is encoding.
        Second half (phase 0.5-1.0) is retrieval/consolidation.
        """
        return 0.0 <= self.phase < 0.5
    
    def is_retrieval_window(self) -> bool:
        """Returns True if current phase is in retrieval window."""
        return 0.5 <= self.phase < 1.0
    
    def get_theta_frequency_hz(self) -> float:
        """Get theta frequency in Hz."""
        return 1000.0 / self.theta_period_ms
    
    def get_statistics(self) -> Dict:
        """Get oscillator statistics."""
        return {
            "theta_freq_hz": self.get_theta_frequency_hz(),
            "current_phase": round(self.phase, 3),
            "theta_power": round(self.get_theta_power(), 3),
            "is_encoding": self.is_encoding_window(),
            "total_ticks": self.total_ticks,
            "encoding_windows": self.encoding_windows,
            "encoding_ratio": round(self.encoding_windows / max(1, self.total_ticks), 3),
        }
    
    def reset(self):
        """Reset oscillator state."""
        self.phase = 0.0
        self._time_accumulator_ms = 0.0
        self.total_ticks = 0
        self.encoding_windows = 0
    
    def export(self) -> Dict:
        """Export state for persistence."""
        return {
            "theta_period_ms": self.theta_period_ms,
            "phase": self.phase,
            "time_accumulator_ms": self._time_accumulator_ms,
        }
    
    def import_(self, data: Dict):
        """Import state from persistence."""
        if "theta_period_ms" in data:
            self.theta_period_ms = data["theta_period_ms"]
        if "phase" in data:
            self.phase = data["phase"] % 1.0
        if "time_accumulator_ms" in data:
            self._time_accumulator_ms = data["time_accumulator_ms"]


def create_theta_pacemaker() -> SeptalThetaPacemaker:
    """Create a default theta pacemaker."""
    return SeptalThetaPacemaker()


if __name__ == "__main__":
    # Test the theta pacemaker
    theta = create_theta_pacemaker()
    
    print("Theta Pacemaker Test")
    print("=" * 40)
    
    # Simulate 200ms of activity
    dt_ms = 0.1
    steps = int(200 / dt_ms)
    
    for i in range(steps):
        phase = theta.tick(dt_ms)
        
        if i % 100 == 0:  # Print every 10ms
            print(f"t={i*dt_ms:5.1f}ms: phase={theta.phase:.2f}, "
                  f"power={theta.get_theta_power():+.2f}, "
                  f"encoding={theta.is_encoding_window()}")
    
    print()
    print(f"Statistics: {theta.get_statistics()}")