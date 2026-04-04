import numpy as np
from brain.synapses.stdp_synapses import SparseSTDPSynapse, STDPParams
from brain.neurons import LIFPopulation


def test_stdp_ltp_and_ltd_direction():
    pre_n = 10
    post_n = 10
    params = STDPParams(A_plus=0.1, A_minus=0.1, lr=1.0)
    syn = SparseSTDPSynapse(pre_n, post_n, p=0.5, params=params, rng_seed=1)

    # Create mock traces: pre trace high on pre neuron 0, post trace high on post neuron 0
    pre_trace = np.zeros(pre_n, dtype=np.float32)
    post_trace = np.zeros(post_n, dtype=np.float32)
    pre_trace[0] = 1.0
    post_trace[0] = 1.0

    # Capture weight before
    w_before = syn.weights.copy()

    # Simulate a post spike (should produce LTP for synapses where pre trace exists)
    syn.update_stdp(np.array([], dtype=np.int32), np.array([0], dtype=np.int32), pre_trace, post_trace, gain=1.0)
    w_after_post = syn.weights.copy()
    assert w_after_post.max() >= w_before.max(), "Expected some weights to increase on post spike (LTP)"

    # Now simulate a pre spike (should produce LTD for synapses where post trace exists)
    syn.update_stdp(np.array([0], dtype=np.int32), np.array([], dtype=np.int32), pre_trace, post_trace, gain=1.0)
    w_after_pre = syn.weights.copy()
    assert w_after_pre.min() <= w_after_post.min(), "Expected some weights to decrease on pre spike (LTD)"
