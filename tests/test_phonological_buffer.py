from codec.phonological_buffer import PhonologicalBuffer, create_phonological_buffer


def test_phonological_buffer_learns_and_generates():
    pb = create_phonological_buffer(n_assemblies=10)
    # Learn words for assembly 0
    pb.observe_pairing("hello", 0, strength=0.2)
    pb.observe_pairing("world", 0, strength=0.2)

    state = {"active_concept_neuron": 0, "attractor_chainer": None}
    out = pb.generate(state)
    assert "hello" in out or "world" in out, "Expected generated output to contain learned words"
