"""
config.py — BRAIN 2.0 Configuration
===================================
Global configuration for the brain system.
Supports multiple LLM backends including local Ollama.
"""

import os


# ─── Brain Scale Configuration ───────────────────────────────────────────────

# Scale factor 0.0–1.0 controls neuron counts
# scale=0.01 → fast CPU demo (~50k total neurons)
# scale=0.10 → full demo (~500k neurons)
# scale=1.00 → OSCEN target (~1M neurons, needs Loihi/GPU)
SCALE = float(os.getenv("BRAIN_SCALE", "0.01"))

# Simulation timestep (ms)
DT = 0.1


# ─── LLM Configuration ──────────────────────────────────────────────────────

class LLMConfig:
    """
    LLM Configuration with support for multiple backends.
    
    Supported backends:
    - local_ollama: Local Ollama instance (default for v0.1)
    - openai: OpenAI API (GPT-4o, GPT-4o-mini, etc.)
    - anthropic: Anthropic API (Claude)
    - none: No LLM (SNN-only mode)
    """
    
    def __init__(self):
        # Backend type: "local_ollama", "openai", "anthropic", "none"
        self.backend = os.getenv("LLM_BACKEND", "local_ollama")
        
        # ─── Local Ollama Configuration ──────────────────────────────────
        # Your Ollama instance
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.6.149:9997")
        
        # Available models - you can register multiple models
        # The first one in the list is the default
        self.ollama_models = self._parse_models(
            os.getenv("OLLAMA_MODELS", "qwen2.5:7b,llama3.2:latest,phi3:mini, mistral:latest")
        )
        
        # Model selection (index or name)
        self.default_model_index = int(os.getenv("LLM_MODEL_INDEX", "0"))
        
        # ─── OpenAI Configuration ────────────────────────────────────────
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_models = self._parse_models(
            os.getenv("OPENAI_MODELS", "gpt-4o-mini,gpt-4o,gpt-3.5-turbo")
        )
        
        # ─── Anthropic Configuration ─────────────────────────────────────
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_models = self._parse_models(
            os.getenv("ANTHROPIC_MODELS", "claude-sonnet-4-20250514,claude-3-opus-20240229")
        )
        
        # ─── General Settings ────────────────────────────────────────────
        # Temperature for generation
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        # Max tokens to generate
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "200"))
        
        # Timeout in seconds
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        
        # Whether to use local model by default
        self.prefer_local = os.getenv("LLM_PREFER_LOCAL", "true").lower() == "true"
    
    def _parse_models(self, models_str: str) -> list:
        """Parse comma-separated model list."""
        return [m.strip() for m in models_str.split(",") if m.strip()]
    
    def get_default_model(self) -> str:
        """Get the default model name based on backend."""
        if self.backend == "local_ollama":
            if self.default_model_index < len(self.ollama_models):
                return self.ollama_models[self.default_model_index]
            return self.ollama_models[0] if self.ollama_models else "llama3.2:latest"
        elif self.backend == "openai":
            if self.default_model_index < len(self.openai_models):
                return self.openai_models[self.default_model_index]
            return self.openai_models[0] if self.openai_models else "gpt-4o-mini"
        elif self.backend == "anthropic":
            if self.default_model_index < len(self.anthropic_models):
                return self.anthropic_models[self.default_model_index]
            return self.anthropic_models[0] if self.anthropic_models else "claude-sonnet-4-20250514"
        return "none"
    
    def get_all_models(self) -> dict:
        """Get all available models for each backend."""
        return {
            "local_ollama": self.ollama_models,
            "openai": self.openai_models,
            "anthropic": self.anthropic_models,
        }
    
    def set_model(self, backend: str, model_name: str):
        """Set the model to use."""
        self.backend = backend
        
        if backend == "local_ollama":
            if model_name in self.ollama_models:
                self.default_model_index = self.ollama_models.index(model_name)
        elif backend == "openai":
            if model_name in self.openai_models:
                self.default_model_index = self.openai_models.index(model_name)
        elif backend == "anthropic":
            if model_name in self.anthropic_models:
                self.default_model_index = self.anthropic_models.index(model_name)
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama is available at the configured URL."""
        import requests
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_ollama_models(self) -> list:
        """List available models from Ollama."""
        import requests
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except:
            pass
        return self.ollama_models  # Return configured models as fallback
    
    def get_best_available_model(self) -> str:
        """
        Auto-detect and select the best available Ollama model.
        
        Priority:
        1. Query Ollama for actual available models
        2. Select first available model from known-good list:
           - llama3.2:latest (latest Llama)
           - mistral:latest (reliable general)
           - phi3:mini (fast, efficient)
           - codellama:latest (if code-related)
        3. Fall back to configured default
        
        Returns the best available model name.
        """
        # Known good models in priority order
        known_good_models = [
            "llama3.2:latest",
            "llama3.1:latest", 
            "mistral:latest",
            "phi3:mini",
            "phi3:medium",
            "codellama:latest",
            "llama2:latest",
            "llama2:7b",
            "mixtral:latest",
        ]
        
        # Try to get actual available models from Ollama
        available = self.list_ollama_models()
        
        if available:
            # Find first known-good model that's actually available
            for model in known_good_models:
                # Check for exact match or model base
                for avail in available:
                    if model == avail or avail.startswith(model.split(':')[0]):
                        return avail
            # If no known model found, return first available
            return available[0]
        
        # Fallback to configured models
        if self.ollama_models:
            return self.ollama_models[self.default_model_index] if self.default_model_index < len(self.ollama_models) else self.ollama_models[0]
        
        return "llama3.2:latest"  # Ultimate fallback
    
    def auto_detect_best_model(self) -> tuple[bool, str | None]:
        """
        Convenience method: Check if Ollama is available and get best model.
        Returns tuple of (is_available, best_model_name).
        """
        is_available = self.is_ollama_available()
        if is_available:
            return (True, self.get_best_available_model())
        return (False, None)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "backend": self.backend,
            "default_model": self.get_default_model(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "ollama_base_url": self.ollama_base_url,
            "ollama_models": self.ollama_models,
            "openai_models": self.openai_models,
            "anthropic_models": self.anthropic_models,
            "prefer_local": self.prefer_local,
        }


# Create global LLM config instance
LLM_CONFIG = LLMConfig()

# Legacy compatibility - these are now accessed via LLM_CONFIG
LLM_MODEL = LLM_CONFIG.get_default_model()
LLM_API_BASE = LLM_CONFIG.ollama_base_url
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
USE_LOCAL_LLM = LLM_CONFIG.prefer_local


# ─── Persistence Configuration ──────────────────────────────────────────────

# Directory for brain state
PERSIST_DIR = os.getenv("PERSIST_DIR", "brain_state")

# Save frequency (steps)
SAVE_FREQUENCY = 10000

# Auto-save on shutdown
AUTO_SAVE = os.getenv("AUTO_SAVE", "true").lower() == "true"


# ─── API Configuration ───────────────────────────────────────────────────────

# API host
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# API port
API_PORT = int(os.getenv("API_PORT", "8030"))

# Enable CORS
ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"


# ─── Cost Configuration ────────────────────────────────────────────────────

# Daily budget (USD)
DAILY_BUDGET = float(os.getenv("DAILY_BUDGET", "0.50"))

# Monthly budget (USD)
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET", "10.00"))


# ─── Brain Stage Thresholds ─────────────────────────────────────────────────

# Steps thresholds for brain stages
NEONATAL_THRESHOLD = 100_000
JUVENILE_THRESHOLD = 1_000_000
ADOLESCENT_THRESHOLD = 5_000_000


# ─── STDP Parameters ───────────────────────────────────────────────────────

STDP_A_PLUS = 0.01
STDP_A_MINUS = 0.0105
STDP_TAU_PLUS = 20.0
STDP_TAU_MINUS = 20.0
STDP_W_MIN = 0.0
STDP_W_MAX = 1.0


# ─── Debug Configuration ───────────────────────────────────────────────────

# Enable debug logging
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Enable telemetry
ENABLE_TELEMETRY = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"


def get_config() -> dict:
    """Get all configuration as dictionary."""
    return {
        "scale": SCALE,
        "dt": DT,
        "llm": LLM_CONFIG.to_dict(),
        "persist_dir": PERSIST_DIR,
        "save_frequency": SAVE_FREQUENCY,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "daily_budget": DAILY_BUDGET,
        "monthly_budget": MONTHLY_BUDGET,
        "debug": DEBUG,
    }


def print_config():
    """Print current configuration."""
    config = get_config()
    print("BRAIN 2.0 Configuration:")
    print("-" * 40)
    print(f"Scale: {config['scale']}")
    print(f"DT: {config['dt']} ms")
    print(f"Persist dir: {config['persist_dir']}")
    print(f"API: {config['api_host']}:{config['api_port']}")
    print()
    print("LLM Configuration:")
    print("-" * 40)
    llm = config['llm']
    print(f"  Backend: {llm['backend']}")
    print(f"  Default model: {llm['default_model']}")
    print(f"  Temperature: {llm['temperature']}")
    print(f"  Max tokens: {llm['max_tokens']}")
    print(f"  Prefer local: {llm['prefer_local']}")
    print()
    if llm['backend'] == 'local_ollama':
        print(f"  Ollama URL: {llm['ollama_base_url']}")
        print(f"  Available models: {', '.join(llm['ollama_models'])}")
    print()
    print("Budget Configuration:")
    print("-" * 40)
    print(f"  Daily: ${config['daily_budget']}")
    print(f"  Monthly: ${config['monthly_budget']}")


if __name__ == "__main__":
    print_config()
