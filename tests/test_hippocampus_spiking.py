from memory.hippocampus_spiking import create_hippocampus_spiking


def test_hippocampus_spiking_encode_recall():
    h = create_hippocampus_spiking(max_episodes=10, dg_size=128)
    h.encode([1, 2, 3, 4], topic="test", valence=0.2)
    results = h.recall([1, 2, 3])
    # Should return a list (possibly empty) and not crash
    assert isinstance(results, list)
    # export/import roundtrip
    data = h.export()
    h2 = create_hippocampus_spiking(max_episodes=10, dg_size=128)
    h2.import_(data)
    assert isinstance(h2.export(), list)
