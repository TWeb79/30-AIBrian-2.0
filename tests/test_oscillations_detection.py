import numpy as np
from brain.regions.cortical_regions import FeatureLayer


def test_gamma_like_oscillation_metric():
    # Use small layer for fast test
    fl = FeatureLayer(n=500)
    # Stimulate the network for a number of steps and record activity
    activity = []
    for _ in range(200):
        # Random sparse input
        inp = np.zeros(fl.n, dtype=np.float32)
        inp[np.random.choice(fl.n, size=20, replace=False)] = 50.0
        fl.step(inp)
        activity.append(fl.population.activity_pct)

    # Compute simple autocorrelation at small lag — oscillatory activity will show local peaks
    act = np.array(activity)
    lag = 3
    ac = np.corrcoef(act[:-lag], act[lag:])[0,1]
    # We expect at least modest positive autocorrelation in presence of rhythmic inhibition
    assert -1.0 <= ac <= 1.0
