from brain import OSCENBrain


def test_brain_process_input_returns_response():
    brain = OSCENBrain(scale=0.001, seed=1)
    res = brain.process_input_v01("hello")
    assert res.get("response") is not None
    assert res.get("path") in ("local", "llm", "cached")
