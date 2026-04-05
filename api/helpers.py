# API Helpers - Response generation functions
from api.config import brain

def get_stats_response() -> str:
    """Generate comprehensive brain statistics response."""
    snap = brain.snapshot()
    regions = snap.get("regions", {})
    total_neurons = brain.total_neurons()
    total_synapses = brain.total_synapses()
    vocab_size = brain.phon_buffer.get_vocabulary_size()
    bypass_stats = brain.bypass_monitor.get_statistics()
    memory_stats = brain.hippocampus.get_statistics()
    
    lines = [
        "**BRAIN STATISTICS**",
        "",
        f"Simulation: step={snap.get('step', 0):,}, rate={snap.get('step_rate', 0):.1f} steps/s",
        f"Attention gain: ×{snap.get('attention_gain', 1.0):.2f}",
        f"Prediction error: {snap.get('prediction_error', 0):.4f}",
        "",
        f"Total neurons: {total_neurons:,}",
        f"Total synapses: {total_synapses:,}",
        f"Vocabulary: {vocab_size} words",
        "",
        "**CORTICAL ACTIVITY**",
    ]
    for name, r in regions.items():
        act = r.get("activity_pct", 0)
        lines.append(f"  • {name}: {act:.1f}%")
    
    lines.extend([
        "",
        f"Bypass rate: {bypass_stats.get('bypass_rate', 0):.1%}",
        f"Episodes stored: {memory_stats.get('episode_count', 0)}",
    ])
    return "\n".join(lines)


def get_vocabulary_response() -> str:
    """Generate vocabulary statistics response."""
    vocab_stats = brain.phon_buffer.get_statistics(recent_count=50)
    vocab_size = vocab_stats.get("vocabulary_size", 0)
    recent_words = vocab_stats.get("recent_words", [])
    assembly_stats = brain.assembly_detector.get_statistics()
    assembly_count = assembly_stats.get("total_assemblies", 0)
    
    lines = [
        "**VOCABULARY**",
        "",
        f"Total words learned: {vocab_size}",
        f"Active assemblies: {assembly_count}",
    ]
    if recent_words:
        lines.extend([
            "",
            "Recent words:",
            ", ".join(recent_words[:30]) + ("..." if len(recent_words) > 30 else ""),
        ])
    return "\n".join(lines)


def get_memory_response() -> str:
    """Generate episodic memory statistics response."""
    mem_stats = brain.hippocampus.get_statistics()
    recent = brain.hippocampus.get_recent(5)
    lines = [
        "**EPISODIC MEMORY**",
        "",
        f"Episodes stored: {mem_stats.get('episode_count', 0)}",
        f"Recall hits: {mem_stats.get('recall_hits', 0)}",
    ]
    if recent:
        lines.append("")
        lines.append("Recent episodes:")
        for ep in recent:
            lines.append(f"  • {ep.topic} (valence: {ep.valence:.2f})")
    return "\n".join(lines)


def get_bypass_response() -> str:
    """Generate LLM bypass statistics response."""
    stats = brain.bypass_monitor.get_statistics()
    lines = [
        "**LLM BYPASS MONITOR**",
        "",
        f"Bypass rate: {stats.get('bypass_rate', 0):.1%}",
        f"Total turns: {stats.get('total_turns', 0)}",
        "",
        "Path distribution:",
        f"  • LLM: {stats.get('paths', {}).get('llm', 0)}",
        f"  • Local: {stats.get('paths', {}).get('local', 0)}",
        f"  • Cached: {stats.get('paths', {}).get('cached', 0)}",
    ]
    return "\n".join(lines)


def get_assemblies_response() -> str:
    """Generate cell assembly statistics response."""
    stats = brain.assembly_detector.get_statistics()
    lines = [
        "**CELL ASSEMBLIES**",
        "",
        f"Total assemblies: {stats.get('total_assemblies', 0)}",
        f"Stable assemblies: {stats.get('stable_assemblies', 0)}",
        f"Average size: {stats.get('avg_size', 0):.1f}",
    ]
    if stats.get('coalitions'):
        lines.append("")
        lines.append("Top coalitions:")
        for c in stats.get('coalitions', [])[:5]:
            lines.append(f"  • {c.get('id', '?')}: {c.get('size', 0)} neurons")
    return "\n".join(lines)


def get_help_response() -> str:
    """Generate help text with all available commands."""
    return """**CHAT COMMANDS**

| Command | Description |
|--------|-------------|
| `/stats` | Displays brain statistics |
| `/vocabulary` | Shows learned vocabulary |
| `/memory` | Shows episodic memory stats |
| `/bypass` | Shows LLM bypass rate |
| `/assemblies` | Shows cell assembly stats |
| `/grep <n> <url>` | Crawl web pages |
| `/llm <prompt>` | Direct LLM query |
| `/llmtrain [n] [text]` | Self-learning tutoring loop |
| `/yt <n> <url>` | Transcribe YouTube videos |
| `/?` or `/help` | Show this help |

Any other text is processed by the neural network."""


def brain_respond_fallback(message: str, snap: dict) -> str:
    """Fallback response when LLM is not available."""
    regions = snap.get("regions", {})
    gain = snap.get("attention_gain", 1.0)
    err = snap.get("prediction_error", 0.0)
    concept = regions.get("concept", {}).get("active_concept_neuron", -1)
    status = snap.get("status", "NEONATAL")
    step = snap.get("step", 0)

    assoc_act = regions.get("association", {}).get("activity_pct", 0)
    pred_act = regions.get("predictive", {}).get("activity_pct", 0)
    concept_act = regions.get("concept", {}).get("activity_pct", 0)
    
    lines = [
        f"[BRAIN20·{status}·step={step:,}]",
        "",
        f"Processing: '{message}'",
        "",
        f"Neural activity report:",
        f"  • Association hub:   {assoc_act:.1f}% active  (cross-modal binding)",
        f"  • Predictive cortex: {pred_act:.1f}% active  (error={err:.4f})",
        f"  • Concept layer:     {concept_act:.2f}% active  (WTA winner #{concept})",
        f"  • Attention gain:    ×{gain:.2f}  ({'HIGH — learning accelerated' if gain > 2 else 'normal'})",
        "",
        f"The STDP synapses are {'strengthening rapidly' if gain > 2 else 'updating normally'} based on this input.",
    ]
    return "\n".join(lines)