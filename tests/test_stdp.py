import numpy as np
from brain.synapses.stdp_synapses import SparseSTDPSynapse, STDPParams
from brain.neurons import LIFPopulation


def test_stdp_ltp_and_ltd_direction():
    pre_n = 10
    post_n = 10
    params = STDPParams(A_plus=0.1, A_minus=0.1, lr=1.0)
    syn = SparseSTDPSynapse(pre_n, post_n, p=0.5, params=params, rng_seed=1)

    pre_trace = np.zeros(pre_n, dtype=np.float32)
    post_trace = np.zeros(post_n, dtype=np.float32)
    pre_trace[0] = 1.0
    post_trace[0] = 1.0

    w_before = syn.weights.copy()
    syn.update_stdp(np.array([], dtype=np.int32), np.array([0], dtype=np.int32), pre_trace, post_trace, gain=1.0)
    w_after_post = syn.weights.copy()
    assert w_after_post.max() >= w_before.max(), "Expected some weights to increase on post spike (LTP)"

    syn.update_stdp(np.array([0], dtype=np.int32), np.array([], dtype=np.int32), pre_trace, post_trace, gain=1.0)
    w_after_pre = syn.weights.copy()
    assert w_after_pre.min() <= w_after_post.min(), "Expected some weights to decrease on pre spike (LTD)"


def test_stdp_weight_bounds():
    """Test that weights stay within min/max bounds."""
    params = STDPParams(A_plus=0.5, A_minus=0.5, w_min=0.1, w_max=0.9, lr=1.0)
    syn = SparseSTDPSynapse(10, 10, p=0.5, params=params, rng_seed=1)
    
    pre_trace = np.ones(10, dtype=np.float32)
    post_trace = np.ones(10, dtype=np.float32)
    
    for _ in range(50):
        syn.update_stdp(np.arange(10, dtype=np.int32), np.arange(10, dtype=np.int32), pre_trace, post_trace, gain=2.0)
    
    assert syn.weights.max() <= 0.9, f"Weight max {syn.weights.max()} exceeds w_max=0.9"
    assert syn.weights.min() >= 0.1, f"Weight min {syn.weights.min()} below w_min=0.1"


def test_stdp_no_spikes_no_update():
    """Test that STDP does nothing with empty spike arrays."""
    params = STDPParams(A_plus=0.1, A_minus=0.1)
    syn = SparseSTDPSynapse(10, 10, p=0.5, params=params, rng_seed=1)
    w_before = syn.weights.copy()
    
    syn.update_stdp(np.array([], dtype=np.int32), np.array([], dtype=np.int32), 
                    np.zeros(10), np.zeros(10))
    
    assert np.allclose(syn.weights, w_before), "Weights should not change with no spikes"


def test_stdp_event_counters():
    """Test LTP/LTD event counters."""
    params = STDPParams(A_plus=0.1, A_minus=0.1)
    syn = SparseSTDPSynapse(10, 10, p=0.5, params=params, rng_seed=1)
    
    assert hasattr(syn, 'total_ltp_events'), "Should have total_ltp_events attribute"
    assert hasattr(syn, 'total_ltd_events'), "Should have total_ltd_events attribute"
    
    pre_trace = np.ones(10, dtype=np.float32)
    post_trace = np.ones(10, dtype=np.float32)
    
    initial_ltp = syn.total_ltp_events
    syn.update_stdp(np.array([], dtype=np.int32), np.array([0], dtype=np.int32), pre_trace, post_trace)
    assert syn.total_ltp_events > initial_ltp, "LTP event counter should increment"


def test_stdp_theta_gating():
    """Test theta-gated STDP (apply_ltp/apply_ltd flags)."""
    params = STDPParams(A_plus=0.1, A_minus=0.1)
    syn = SparseSTDPSynapse(10, 10, p=0.5, params=params, rng_seed=1)
    
    pre_trace = np.ones(10, dtype=np.float32)
    post_trace = np.ones(10, dtype=np.float32)
    
    w_before = syn.weights.copy()
    syn.update_stdp(np.array([0], dtype=np.int32), np.array([0], dtype=np.int32), 
                    pre_trace, post_trace, apply_ltp=False, apply_ltd=False)
    
    assert np.allclose(syn.weights, w_before), "Weights should not change when both gates disabled"


def test_stdp_sparse_propagate():
    """Test sparse spike propagation."""
    params = STDPParams()
    syn = SparseSTDPSynapse(100, 50, p=0.1, params=params, rng_seed=1)
    
    spikes = np.array([0, 5, 10], dtype=np.int32)
    i_post = syn.propagate(spikes)
    
    assert i_post.shape == (50,), f"Expected shape (50,), got {i_post.shape}"
    assert i_post.sum() > 0, "Expected some post-synaptic current"


def test_stdp_mean_weight():
    """Test mean_weight calculation."""
    params = STDPParams()
    syn = SparseSTDPSynapse(10, 10, p=0.5, params=params, rng_seed=42)
    
    mean_w = syn.mean_weight()
    assert 0 <= mean_w <= 1, f"Mean weight {mean_w} out of range"


if __name__ == "__main__":
    test_stdp_ltp_and_ltd_direction()
    test_stdp_weight_bounds()
    test_stdp_no_spikes_no_update()
    test_stdp_event_counters()
    test_stdp_theta_gating()
    test_stdp_sparse_propagate()
    test_stdp_mean_weight()
    print("✓ All STDP tests passed!")
