import os
from typing import Optional

from memory.checkpoints.sqlite_checkpoint import (
    SQLiteCheckpointManager
)

from memory.checkpoints.postgres_checkpoint import (
    PostgresCheckpointManager
)


# checkpoint configuration

CHECKPOINT_BACKEND = os.getenv(
    "CHECKPOINT_BACKEND",
    "sqlite"
)


# graph checkpoint manager

class GraphCheckpointManager:
    """
    LangGraph checkpoint abstraction.

    Responsibilities:
    - select persistence backend
    - save workflow state
    - load workflow state
    - support graph resumability
    """

    def __init__(self):

        self.backend = (
            CHECKPOINT_BACKEND.lower()
        )

        self.checkpointer = (
            self._initialize_backend()
        )


    # initialize backend

    def _initialize_backend(self):

        if self.backend == "postgres":

            return (
                PostgresCheckpointManager()
            )

        return SQLiteCheckpointManager()


    # save checkpoint

    def save(
        self,
        checkpoint_id: str,
        session_id: str,
        workflow_status: str,
        active_agent: str,
        retry_count: int,
        state_data: dict
    ):
        """
        Save graph state.
        """

        return self.checkpointer.save_checkpoint(

            checkpoint_id=checkpoint_id,

            session_id=session_id,

            workflow_status=workflow_status,

            active_agent=active_agent,

            retry_count=retry_count,

            state_data=state_data
        )


    # load checkpoint

    def load(
        self,
        checkpoint_id: str
    ):
        """
        Restore graph state.
        """

        return (
            self.checkpointer
            .load_checkpoint(
                checkpoint_id
            )
        )


    # list checkpoints

    def list(
        self,
        session_id: Optional[str] = None
    ):
        """
        Retrieve checkpoints.
        """

        if hasattr(
            self.checkpointer,
            "list_checkpoints"
        ):

            return (
                self.checkpointer
                .list_checkpoints(
                    session_id
                )
            )

        return {

            "success": False,

            "error": (
                "Listing not supported."
            )
        }


# global checkpoint manager 
graph_checkpoint = (
    GraphCheckpointManager()
)