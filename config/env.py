"""
OmniAgent central configuration.
All hardcoded constants live here. Import from this module everywhere.
"""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

try:
    from platformdirs import user_data_dir
except ImportError:
    user_data_dir = None

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent

# User data directory — resolves to the right place per OS:
#   Linux:   ~/.local/share/omniagent
#   macOS:   ~/Library/Application Support/omniagent
#   Windows: C:\Users\<you>\AppData\Local\omniagent\omniagent
def _default_user_data_dir() -> str:
    if user_data_dir is not None:
        return user_data_dir("omniagent", "omniagent")
    return str(Path.home() / ".local" / "share" / "omniagent")


USER_DATA_DIR = Path(
    os.getenv("OMNIAGENT_DATA_DIR") or _default_user_data_dir()
).expanduser().resolve()

# Paths
GENERATED_PROJECT_DIR = USER_DATA_DIR / "projects" 
MEMORY_STORAGE_DIR    = USER_DATA_DIR / "memory" / "storage"
CHROMA_DB_PATH        = USER_DATA_DIR / "memory" / "chroma_db"
CHECKPOINT_DIR        = USER_DATA_DIR / "memory" / "checkpoints" / "data"
SQLITE_DB_PATH        = CHECKPOINT_DIR / "workflow_checkpoints.db"

# Ensure directories exist
for _dir in [GENERATED_PROJECT_DIR, MEMORY_STORAGE_DIR, CHROMA_DB_PATH, CHECKPOINT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# LLM Configuration
# Provider selection: "gemini", "openai", "groq", "ollama", "huggingface_local", "huggingface_cloud"
LLM_PROVIDER      = os.getenv("LLM_PROVIDER", "gemini")
LLM_TEMPERATURE   = float(os.getenv("LLM_TEMPERATURE", "0.6"))

# Google Gemini
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY    = os.getenv("GOOGLE_GEMINI_API_KEY", "")

# OpenAI
OPENAI_MODEL      = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")

# Groq
GROQ_MODEL        = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")

# Ollama (local inference)
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# HuggingFace
HF_MODEL          = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")
HF_API_KEY        = os.getenv("HF_API_KEY", "")
HF_DEVICE         = os.getenv("HF_DEVICE", "cpu")  # "cpu" or "cuda"
HF_LOCAL_REPO     = str(Path(os.getenv("HF_LOCAL_REPO", str(USER_DATA_DIR / "hf_models"))).expanduser())

# Workflow limits
MAX_RETRIES       = 5
EXECUTION_TIMEOUT = 60  # seconds

# Checkpointing
CHECKPOINT_BACKEND = os.getenv("CHECKPOINT_BACKEND", "sqlite")

# Memory
MEMORY_MAX_ENTRIES   = 500
SHORT_TERM_MEM_LIMIT = 20
MEMORY_LOG_TRUNCATE  = 2000  # chars

# Embedding
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
