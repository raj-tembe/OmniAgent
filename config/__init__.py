"""
OmniAgent configuration package.

Two layers, kept deliberately separate:

- `config.env` — secrets and machine-local settings (API keys, paths,
  provider defaults) read from environment variables / .env. Unchanged
  from the original single-file `config.py`; re-exported here so every
  existing `from config import X` import keeps working.

- `config.schema` / `config.loader` — the declarative `omniagent.json` layer
  (permissions, agent modes, provider catalog, MCP servers, plugins). This is
  what later phases (permission engine, agent modes, MCP client) read from.
"""
from config.env import (
    CHECKPOINT_BACKEND,
    CHECKPOINT_DIR,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    EXECUTION_TIMEOUT,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GENERATED_PROJECT_DIR,
    GROQ_API_KEY,
    GROQ_MODEL,
    HF_API_KEY,
    HF_DEVICE,
    HF_LOCAL_REPO,
    HF_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    MAX_RETRIES,
    MEMORY_LOG_TRUNCATE,
    MEMORY_MAX_ENTRIES,
    MEMORY_STORAGE_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    PROJECT_ROOT,
    SHORT_TERM_MEM_LIMIT,
    SQLITE_DB_PATH,
    USER_DATA_DIR,
)
from config.loader import config_paths, load_config
from config.schema import (
    AgentModeConfig,
    McpServerConfig,
    OmniAgentConfig,
    PermissionAction,
    PermissionConfig,
    ProviderConfig,
)

__all__ = [
    # env.py re-exports
    "PROJECT_ROOT",
    "USER_DATA_DIR",
    "GENERATED_PROJECT_DIR",
    "MEMORY_STORAGE_DIR",
    "CHROMA_DB_PATH",
    "CHECKPOINT_DIR",
    "SQLITE_DB_PATH",
    "LLM_PROVIDER",
    "LLM_TEMPERATURE",
    "GEMINI_MODEL",
    "GEMINI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_API_KEY",
    "GROQ_MODEL",
    "GROQ_API_KEY",
    "OLLAMA_MODEL",
    "OLLAMA_BASE_URL",
    "HF_MODEL",
    "HF_API_KEY",
    "HF_DEVICE",
    "HF_LOCAL_REPO",
    "MAX_RETRIES",
    "EXECUTION_TIMEOUT",
    "CHECKPOINT_BACKEND",
    "MEMORY_MAX_ENTRIES",
    "SHORT_TERM_MEM_LIMIT",
    "MEMORY_LOG_TRUNCATE",
    "EMBEDDING_MODEL",
    # schema.py / loader.py
    "OmniAgentConfig",
    "PermissionConfig",
    "PermissionAction",
    "AgentModeConfig",
    "ProviderConfig",
    "McpServerConfig",
    "load_config",
    "config_paths",
]
