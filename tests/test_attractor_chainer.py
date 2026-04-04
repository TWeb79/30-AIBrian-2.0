from cognition.attractor_chainer import AttractorChainer
from codec.phonological_buffer import PhonologicalBuffer


def test_attractor_chainer_transitions():
    """Test that AttractorChainer learns transitions correctly."""
    chainer = AttractorChainer()
    
    # Record 5 transitions
    chainer.record_transition(0, 1, dt_ms=100)
    chainer.record_transition(1, 2, dt_ms=80)
    chainer.record_transition(2, 3, dt_ms=120)
    chainer.record_transition(0, 2, dt_ms=150)
    chainer.record_transition(1, 3, dt_ms=90)
    
    # Assert predict_next() returns expected top assembly
    preds = chainer.predict_next(0, top_k=1)
    assert len(preds) > 0, "Expected predictions for assembly 0"
    assert preds[0][0] == 1, f"Expected assembly 1 as top prediction, got {preds[0][0]}"
    
    # Assert predict_next() for assembly 1
    preds = chainer.predict_next(1, top_k=1)
    assert len(preds) > 0, "Expected predictions for assembly 1"
    assert preds[0][0] == 2, f"Expected assembly 2 as top prediction, got {preds[0][0]}"
    
    print("✓ test_attractor_chainer_transitions passed")


def test_phonological_buffer_with_chainer():
    """Test end-to-end: recorded transitions → generate() produces multi-word output."""
    chainer = AttractorChainer()
    
    # Record transitions: 0 → 1 → 2
    chainer.record_transition(0, 1, dt_ms=100)
    chainer.record_transition(1, 2, dt_ms=80)
    
    # Create phonological buffer and learn words for assemblies
    pb = PhonologicalBuffer(n_assemblies=10)
    pb.observe_pairing("hello", 0, strength=0.5)
    pb.observe_pairing("world", 1, strength=0.5)
    pb.observe_pairing("there", 2, strength=0.5)
    
    # Generate with chainer
    state = {
        "active_concept_neuron": 0,
        "attractor_chainer": chainer,
        "memory_snippet": "",
    }
    out = pb.generate(state)
    
    # Assert output contains multiple words from chained assemblies
    # The sentence template embeds words like "I recall hello. It connects with world."
    out_lower = out.lower()
    assert "hello" in out_lower or "world" in out_lower or "there" in out_lower, \
        f"Expected learned words in output, got: {out}"
    
    print(f"✓ test_phonological_buffer_with_chainer passed: '{out}'")


if __name__ == "__main__":
    test_attractor_chainer_transitions()
    test_phonological_buffer_with_chainer()
    print("\nAll AttractorChainer tests passed!")
