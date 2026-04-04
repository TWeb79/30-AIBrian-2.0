import numpy as np
from brain.neurons import LIFPopulation, LIFParams


def test_lif_fires_with_constant_current():
    params = LIFParams(tau_m=10.0, tau_ref=1.0, v_thresh=-55.0, dt=0.1)
    pop = LIFPopulation(100, params)
    # Inject sustained current to half the population
    idx = np.arange(50)
    pop.inject_current(idx, 20.0)

    fired_any = False
    for _ in range(200):
        spikes = pop.step(np.zeros(pop.n, dtype=np.float32))
        if spikes.size > 0:
            fired_any = True
            break

    assert fired_any, "Expected at least one neuron to fire under sustained current"
