import os
import logging
from typing import Optional

from config import SQLITE_DB_PATH

# checkpoint configuration

CHECKPOINT_BACKEND = os.getenv(
    "CHECKPOINT_BACKEND",
    "memory"
)

logger = logging.getLogger(__name__)


# graph checkpoint manager

class GraphCheckpointManager:
    """
    LangGraph checkpoint abstraction.

    Responsibilities:
    - provide checkpoint saver for graph persistence
    - support graph resumability

    Note: Uses MemorySaver by default (in-memory). For production
    with persistent storage, use environment variable CHECKPOINT_BACKEND=sqlite
    and install langgraph-checkpoint[sqlite] package.
    """

    def __init__(self):

        self.backend = (
            CHECKPOINT_BACKEND.lower()
        )

        self.checkpointer = (
            self._initialize_backend()
        )

        logger.info(
            f"Checkpoint backend initialized: {self.backend}"
        )


    # initialize backend

    def _initialize_backend(self):
        """
        Initialize LangGraph checkpoint saver based on configured backend.
        
        Returns:
            BaseCheckpointSaver: LangGraph-compatible checkpoint saver
        """

        if self.backend == "sqlite":
            try:
                # Try langgraph-checkpoint sqlite backend
                from langgraph_checkpoint.sqlite import SqliteSaver
                
                db_path = str(SQLITE_DB_PATH)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                logger.info(f"Using SQLite checkpoint: {db_path}")
                return SqliteSaver(db_path=db_path)
                
            except ImportError:
                logger.warning(
                    "SQLite backend not available. "
                    "Install: pip install langgraph-checkpoint[sqlite]. "
                    "Falling back to memory saver."
                )
                return self._get_memory_saver()
            except Exception as e:
                logger.error(f"Failed to initialize SQLite: {e}. Using memory saver.")
                return self._get_memory_saver()

        elif self.backend == "postgres":
            try:
                # Try langgraph-checkpoint postgres backend
                from langgraph_checkpoint.postgres import PostgresSaver
                
                connection_string = os.getenv(
                    "POSTGRES_CONNECTION_STRING",
                    "postgresql://user:password@localhost/omniagent"
                )
                
                logger.info(f"Using PostgreSQL checkpoint")
                return PostgresSaver(conn_string=connection_string)
                
            except ImportError:
                logger.warning(
                    "PostgreSQL backend not available. "
                    "Install: pip install langgraph-checkpoint[postgres]. "
                    "Falling back to memory saver."
                )
                return self._get_memory_saver()
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL: {e}. Using memory saver.")
                return self._get_memory_saver()

        else:
            # Default to memory saver
            return self._get_memory_saver()

    def _get_memory_saver(self):
        """
        Get in-memory checkpoint saver (default/fallback).
        
        Returns:
            MemorySaver: In-memory checkpoint saver for current session
        """
        from langgraph.checkpoint.memory import MemorySaver
        
        logger.info("Using MemorySaver (in-memory checkpoints)")
        return MemorySaver()


# global checkpoint manager instance
graph_checkpoint = GraphCheckpointManager()

