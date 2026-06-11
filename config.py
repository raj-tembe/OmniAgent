"""
OmniAgent central configuration.
All hardcoded constants live here. Import from this module everywhere.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent

# Paths
GENERATED_PROJECT_DIR = PROJECT_ROOT / "execution" / "generated_project"
MEMORY_STORAGE_DIR    = PROJECT_ROOT / "memory" / "storage"
CHROMA_DB_PATH        = PROJECT_ROOT / "memory" / "chroma_db"
CHECKPOINT_DIR        = PROJECT_ROOT / "memory" / "checkpoints" / "data"
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
