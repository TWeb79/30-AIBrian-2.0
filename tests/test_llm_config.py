import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_llm_config_model_selection():
    """Test that LLM model can be selected and persisted."""
    from config import LLMConfig
    
    tmp = tempfile.mkdtemp(prefix="test_llm_")
    original_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    
    try:
        os.makedirs(os.path.join(tmp, "brain_state"), exist_ok=True)
        
        class TestConfig(LLMConfig):
            def _load_model_preference(self):
                pass
            
            def _save_model_preference(self, backend, model_name):
                config_file = os.path.join(tmp, "brain_state", "llm_preference.json")
                import json
                with open(config_file, "w") as f:
                    json.dump({"backend": backend, "model": model_name}, f)
        
        config = TestConfig()
        config.ollama_models = ["qwen2.5:7b", "llama3.2:latest", "phi3:mini"]
        
        assert config.get_default_model() == "qwen2.5:7b"
        
        config.set_model("local_ollama", "llama3.2:latest")
        
        assert config.get_default_model() == "llama3.2:latest"
        
        pref_file = os.path.join(tmp, "brain_state", "llm_preference.json")
        assert os.path.exists(pref_file)
        
        import json
        with open(pref_file, "r") as f:
            data = json.load(f)
        
        assert data["backend"] == "local_ollama"
        assert data["model"] == "llama3.2:latest"
        
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_llm_config_invalid_model():
    """Test that invalid model selection is handled gracefully."""
    from config import LLMConfig
    
    class TestConfig(LLMConfig):
        def _load_model_preference(self):
            pass
        def _save_model_preference(self, backend, model_name):
            pass
    
    config = TestConfig()
    config.ollama_models = ["qwen2.5:7b", "llama3.2:latest"]
    
    old_model = config.get_default_model()
    config.set_model("local_ollama", "nonexistent_model")
    
    assert config.get_default_model() == old_model


def test_llm_config_backend_switch():
    """Test switching between different backends."""
    from config import LLMConfig
    
    class TestConfig(LLMConfig):
        def _load_model_preference(self):
            pass
        def _save_model_preference(self, backend, model_name):
            pass
    
    config = TestConfig()
    config.ollama_models = ["qwen2.5:7b", "llama3.2:latest"]
    config.openai_models = ["gpt-4o-mini", "gpt-4o"]
    config.backend = "local_ollama"
    config.default_model_index = 0
    
    config.set_model("openai", "gpt-4o")
    
    assert config.backend == "openai"
    assert config.get_default_model() == "gpt-4o"


if __name__ == "__main__":
    test_llm_config_model_selection()
    test_llm_config_invalid_model()
    test_llm_config_backend_switch()
    print("✓ All LLM config tests passed!")
