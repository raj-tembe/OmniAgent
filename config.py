"""
OmniAgent central configuration.
All hardcoded constants live here. Import from this module everywhere.
"""
import os
from pathlib import Path
from platformdirs import user_data_dir
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent

# User data directory — resolves to the right place per OS:
#   Linux:   ~/.local/share/omniagent
#   macOS:   ~/Library/Application Support/omniagent
#   Windows: C:\Users\<you>\AppData\Local\omniagent\omniagent
USER_DATA_DIR = Path(
    os.getenv("OMNIAGENT_DATA_DIR") or user_data_dir("omniagent", "omniagent")
)

# Paths
GENERATED_PROJECT_DIR = USER_DATA_DIR / "projects" 
MEMORY_STORAGE_DIR    = USER_DATA_DIR / "memory" / "storage"
CHROMA_DB_PATH        = USER_DATA_DIR / "memory" / "chroma_db"
CHECKPOINT_DIR        = USER_DATA_DIR / "memory" / "checkpoints" / "data"
SQLITE_DB_PATH        = CHECKPOINT_DIR / "workflow_checkpoints.db"

# Ensure directories exist
for _dir in [GENERATED_PROJECT_DIR, MEMORY_STORAGE_DIR, CHROMA_DB_PATH, CHECKPOINT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# LLM
GEMINI_MODEL      = "gemini-2.5-flash"
LLM_TEMPERATURE   = 0.6

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
