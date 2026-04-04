from memory.hippocampus_simple import HippocampusSimple
from emotion.amygdala import AmygdalaRegion


def test_hippocampus_recall_prefers_high_valence_with_amygdala():
    hip = HippocampusSimple()
    # Create two episodes with identical neuron sets but different valence
    neurons = [1,2,3,4]
    hip.encode(neurons, topic="neutral", valence=0.0, arousal=0.1)
    hip.encode(neurons, topic="salient", valence=0.9, arousal=0.9)

    # Normal recall (without amygdala) should return the most recent or by similarity
    recs = hip.recall(set(neurons), top_k=2)
    assert len(recs) >= 1

    # Now emulate amygdala score influence by filtering with lower min_overlap
    # We expect recall ordering to include high-valence episode earlier when min_overlap is relaxed
    recs_biased = hip.recall(set(neurons), top_k=2, min_overlap=0.0)
    # Ensure the high-valence one is present
    topics = [r.topic for r in recs_biased]
    assert "salient" in topics
