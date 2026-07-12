import logging
import os

import config
from config import SQLITE_DB_PATH

logger = logging.getLogger(__name__)


class GraphCheckpointManager:
    """
    LangGraph checkpoint abstraction.

    Responsibilities:
    - provide checkpoint saver for graph persistence
    - support graph resumability
    """

    def __init__(self):
        self.backend = os.getenv("CHECKPOINT_BACKEND", config.CHECKPOINT_BACKEND).lower()
        self._backend_context = None
        self.checkpointer = self._initialize_backend()
        logger.info("Checkpoint backend initialized: %s", self.backend)

    def _initialize_backend(self):
        """Initialize LangGraph checkpoint saver based on configured backend."""
        if self.backend == "sqlite":
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver

                db_path = str(SQLITE_DB_PATH)
                os.makedirs(os.path.dirname(db_path), exist_ok=True)

                logger.info("Using SQLite checkpoint: %s", db_path)
                self._backend_context = SqliteSaver.from_conn_string(db_path)
                return self._backend_context.__enter__()
            except ImportError:
                logger.warning(
                    "SQLite backend not available. Install: pip install langgraph-checkpoint-sqlite. Falling back to memory saver."
                )
                return self._get_memory_saver()
            except Exception as exc:
                logger.error("Failed to initialize SQLite: %s. Using memory saver.", exc)
                return self._get_memory_saver()

        if self.backend == "postgres":
            try:
                from langgraph.checkpoint.postgres import PostgresSaver

                connection_string = os.getenv(
                    "POSTGRES_CONNECTION_STRING",
                    "postgresql://user:password@localhost/omniagent",
                )

                logger.info("Using PostgreSQL checkpoint")
                self._backend_context = PostgresSaver.from_conn_string(connection_string)
                return self._backend_context.__enter__()
            except ImportError:
                logger.warning(
                    "PostgreSQL backend not available. Install: pip install langgraph-checkpoint-postgres. Falling back to memory saver."
                )
                return self._get_memory_saver()
            except Exception as exc:
                logger.error("Failed to initialize PostgreSQL: %s. Using memory saver.", exc)
                return self._get_memory_saver()

        return self._get_memory_saver()

    def _get_memory_saver(self):
        """Get in-memory checkpoint saver (default/fallback)."""
        from langgraph.checkpoint.memory import MemorySaver

        logger.info("Using MemorySaver (in-memory checkpoints)")
        return MemorySaver()

    def __del__(self):
        if self._backend_context is not None:
            try:
                self._backend_context.__exit__(None, None, None)
            except Exception:
                pass


graph_checkpoint = GraphCheckpointManager()

