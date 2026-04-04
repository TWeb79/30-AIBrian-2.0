import numpy as np
from brain.synapses.stdp_synapses import SparseSTDPSynapse, STDPParams


def test_stdp_weight_change_magnitude():
    pre_n, post_n = 50, 50
    params = STDPParams(A_plus=0.05, A_minus=0.05, lr=1.0)
    syn = SparseSTDPSynapse(pre_n, post_n, p=0.1, params=params, rng_seed=2)

    # Prepare traces such that pre traces are high for certain synapses
    pre_trace = np.zeros(pre_n, dtype=np.float32)
    post_trace = np.zeros(post_n, dtype=np.float32)
    pre_trace[syn.pre_idx[:10]] = 1.0
    post_spikes = np.unique(syn.post_idx[:10])[:3]
    # Record mean weight before
    mean_before = syn.mean_weight()

    # Trigger LTP via post_spikes
    syn.update_stdp(np.array([], dtype=np.int32), post_spikes, pre_trace, post_trace, gain=1.0)
    mean_after_ltp = syn.mean_weight()
    assert mean_after_ltp >= mean_before, "Expected mean weight to increase after LTP"

    # Now set post traces and trigger LTD via pre spikes
    post_trace[syn.post_idx[:10]] = 1.0
    pre_spikes = np.unique(syn.pre_idx[:10])[:3]
    syn.update_stdp(pre_spikes, np.array([], dtype=np.int32), pre_trace, post_trace, gain=1.0)
    mean_after_ltd = syn.mean_weight()
    assert mean_after_ltd <= mean_after_ltp, "Expected mean weight to decrease after LTD"
