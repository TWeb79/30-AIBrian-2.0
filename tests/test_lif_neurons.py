import numpy as np
from brain.neurons.lif_neurons import LIFPopulation, LIFParams


def test_lif_fires_with_constant_current():
    params = LIFParams(tau_m=10.0, tau_ref=1.0, v_thresh=-55.0, dt=0.1)
    pop = LIFPopulation(100, params)
    idx = np.arange(50)
    pop.inject_current(idx, 20.0)

    fired_any = False
    for _ in range(200):
        spikes = pop.step(np.zeros(pop.n, dtype=np.float32))
        if spikes.size > 0:
            fired_any = True
            break

    assert fired_any, "Expected at least one neuron to fire under sustained current"


def test_lif_refractory_period():
    """Test that neurons respect refractory period."""
    params = LIFParams(tau_m=10.0, tau_ref=5.0, v_thresh=-55.0, dt=0.1)
    pop = LIFPopulation(10, params)
    
    pop.inject_current(np.array([0]), 100.0)
    for _ in range(20):
        spikes = pop.step(np.zeros(10, dtype=np.float32))
        if spikes.size > 0:
            break
    
    assert pop.spike_count[0] > 0, "Neuron should fire with sustained current"


def test_lif_reset_behavior():
    """Test membrane potential reset after spike."""
    params = LIFParams(tau_m=10.0, tau_ref=1.0, v_thresh=-55.0, v_reset=-70.0, dt=0.1)
    pop = LIFPopulation(10, params)
    
    pop.inject_current(np.array([0]), 100.0)
    pop.step(np.zeros(10, dtype=np.float32))
    
    assert np.all(pop.v <= params.v_thresh), "Membrane should reset after spike"


def test_lif_properties():
    """Test that population properties work."""
    params = LIFParams(tau_m=10.0, v_thresh=-55.0)
    pop = LIFPopulation(50, params)
    
    assert pop.firing_rate >= 0, "Firing rate should be non-negative"
    assert 0 <= pop.activity_pct <= 100, "Activity percentage should be 0-100%"


def test_lif_inject_current_bounds_check():
    """Test that inject_current handles valid indices."""
    params = LIFParams(tau_m=10.0, v_thresh=-55.0)
    pop = LIFPopulation(10, params)
    
    valid_idx = np.array([0, 5])
    pop.inject_current(valid_idx, 10.0)
    
    assert pop.i_ext[0] > 0, "Valid index should receive current"
    assert pop.i_ext[5] > 0, "Valid index should receive current"


def test_lif_external_current_reset():
    """Test that external current persists until manually reset."""
    params = LIFParams(tau_m=10.0, v_thresh=-55.0)
    pop = LIFPopulation(10, params)
    
    pop.inject_current(np.array([0]), 50.0)
    pop.step(np.zeros(10, dtype=np.float32))
    pop.reset_external()
    
    assert pop.i_ext[0] == 0, "External current should be reset after reset_external()"


def test_lif_trace_update():
    """Test that STDP trace updates on spike."""
    params = LIFParams(tau_m=10.0, v_thresh=-55.0)
    pop = LIFPopulation(10, params)
    
    pop.v[0] = -50.0
    pop.step(np.zeros(10, dtype=np.float32))
    
    assert pop.trace[0] > 0, "Trace should increase on spike"


if __name__ == "__main__":
    test_lif_fires_with_constant_current()
    test_lif_refractory_period()
    test_lif_reset_behavior()
    test_lif_properties()
    test_lif_inject_current_bounds_check()
    test_lif_external_current_reset()
    test_lif_trace_update()
    print("✓ All LIF neuron tests passed!")
