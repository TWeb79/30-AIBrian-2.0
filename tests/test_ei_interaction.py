import numpy as np
from brain.regions.cortical_regions import FeatureLayer


def test_inhibitory_population_suppresses_exc():
    # Small feature layer for test
    fl = FeatureLayer(n=200)
    # Create a strong excitatory input to cause excitatory firing
    i_syn = np.zeros(fl.n, dtype=np.float32)
    i_syn[:50] = 100.0
    spikes_no_inh = fl.population.step(i_syn)

    # Now run the E/I balanced step which will use inhibitory population internally
    fl._pending_inhibition.fill(0.0)
    spikes_with_ei = fl.step(i_syn)

    # If inhibition works, the number of spikes should be less or equal
    assert len(spikes_with_ei) <= len(spikes_no_inh)
