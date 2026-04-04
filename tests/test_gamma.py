import numpy as np

from brain.oscillations.gamma import GammaOscillator, ThetaGammaCoupler


def test_gamma_oscillator_basic():
    g = GammaOscillator(freq_hz=40.0)
    phases = []
    for _ in range(10):
        phases.append(g.tick(0.1))
    assert all(0.0 <= p < 1.0 for p in phases)
    assert isinstance(g.get_power(), float)


def test_theta_gamma_coupler():
    coupler = ThetaGammaCoupler(preferred_phase=0.25, width=0.4)
    # coupling highest near preferred phase
    g0 = coupler.coupling_gain(0.25)
    g1 = coupler.coupling_gain(0.75)
    assert g0 >= g1
