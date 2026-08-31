"""
Declarative provider/model catalog.

Every provider OmniAgent supports gets one entry here describing what it can
actually do — context window, whether it supports tool-calling, whether it's
a reasoning model, whether it needs an API key — instead of that information
being scattered across if/elif branches and docstrings. This is what lets a
caller ask "does the currently selected provider support tool-calling?"
without needing to know which provider is selected.

Model names themselves stay driven by config/env.py's per-provider
constants (GEMINI_MODEL, OPENAI_MODEL, ...) so there's still exactly one
place that decides which concrete model a provider uses.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from config import GEMINI_MODEL, GROQ_MODEL, HF_MODEL, OLLAMA_MODEL, OPENAI_MODEL


class ModelInfo(BaseModel):
    """Capability metadata for one provider's configured model."""

    provider: str = Field(..., description="Provider key (matches config.env.LLM_PROVIDER values).")
    model: str = Field(..., description="Model identifier currently configured for this provider.")
    context_window: Optional[int] = Field(default=None, description="Approximate max context window in tokens, if known.")
    supports_tools: bool = Field(default=True, description="Whether this model supports LangChain tool/function calling.")
    supports_reasoning: bool = Field(default=False, description="Whether this is a dedicated reasoning-style model.")
    requires_api_key: bool = Field(default=True, description="Whether this provider needs an API key to run.")
    notes: Optional[str] = Field(default=None, description="Anything else worth knowing before picking this provider.")


CATALOG: Dict[str, ModelInfo] = {
    "gemini": ModelInfo(
        provider="gemini", model=GEMINI_MODEL,
        context_window=1_000_000, supports_tools=True, supports_reasoning=True,
        requires_api_key=True,
    ),
    "openai": ModelInfo(
        provider="openai", model=OPENAI_MODEL,
        context_window=128_000, supports_tools=True, supports_reasoning=True,
        requires_api_key=True,
    ),
    "groq": ModelInfo(
        provider="groq", model=GROQ_MODEL,
        context_window=128_000, supports_tools=True, supports_reasoning=False,
        requires_api_key=True, notes="Fast inference; check the specific model's tool-calling support on Groq's model page.",
    ),
    "ollama": ModelInfo(
        provider="ollama", model=OLLAMA_MODEL,
        context_window=8_192, supports_tools=False, supports_reasoning=False,
        requires_api_key=False, notes="Local inference via an Ollama server; tool-calling support varies by model.",
    ),
    "huggingface_cloud": ModelInfo(
        provider="huggingface_cloud", model=HF_MODEL,
        context_window=None, supports_tools=False, supports_reasoning=False,
        requires_api_key=True,
    ),
    "huggingface_local": ModelInfo(
        provider="huggingface_local", model=HF_MODEL,
        context_window=None, supports_tools=False, supports_reasoning=False,
        requires_api_key=False, notes="Runs locally via transformers; needs torch and adequate hardware.",
    ),
}


def get_model_info(provider: str) -> ModelInfo:
    """Look up capability metadata for `provider`. Raises KeyError if unknown."""
    key = provider.lower().strip()
    if key not in CATALOG:
        raise KeyError(f"Unknown provider '{provider}'. Known providers: {sorted(CATALOG)}")
    return CATALOG[key]


def list_providers() -> List[str]:
    """Every provider name the catalog knows about, sorted."""
    return sorted(CATALOG)
