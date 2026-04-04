from brain.oscillations.gamma_ping import PINGGamma, create_ping_gamma


def test_ping_basic():
    p = create_ping_gamma(n_exc=200, n_inh=50)
    e_spikes, i_spikes = p.step(dt_ms=0.1, ext_drive=5.0)
    # even if no spikes, method returns arrays
    assert hasattr(e_spikes, 'size')
    assert hasattr(i_spikes, 'size')
    power = p.get_power()
    assert isinstance(power, float)
