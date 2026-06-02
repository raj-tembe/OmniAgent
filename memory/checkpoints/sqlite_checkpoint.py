import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


# sqlite checkpoint manager 

CHECKPOINT_DIR = "memory/checkpoints/data"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

SQLITE_DB_PATH = os.path.join(
    CHECKPOINT_DIR,
    "workflow_checkpoints.db"
)


# sqlite checkpoint manager

class SQLiteCheckpointManager:
    """
    SQLite-based workflow checkpoint system.

    Responsibilities:
    - persist workflow state
    - enable workflow recovery
    - support resumable execution
    - track autonomous execution history
    """

    def __init__(
        self,
        db_path: str = SQLITE_DB_PATH
    ):

        self.db_path = db_path

        self._initialize_database()


    # initialize DB

    def _initialize_database(self) -> None:
        """
        Create checkpoint table if missing.
        """

        connection = sqlite3.connect(
            self.db_path
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                checkpoint_id TEXT UNIQUE,

                session_id TEXT,

                workflow_status TEXT,

                active_agent TEXT,

                retry_count INTEGER,

                state_data TEXT,

                created_at TEXT
            )
            """
        )

        connection.commit()

        connection.close()


    # save checkpoint

    def save_checkpoint(
        self,
        checkpoint_id: str,
        session_id: str,
        workflow_status: str,
        active_agent: str,
        retry_count: int,
        state_data: Dict[str, Any]
    ) -> Dict:
        """
        Persist workflow checkpoint.
        """

        try:

            connection = sqlite3.connect(
                self.db_path
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO checkpoints (

                    checkpoint_id,
                    session_id,
                    workflow_status,
                    active_agent,
                    retry_count,
                    state_data,
                    created_at

                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint_id,
                    session_id,
                    workflow_status,
                    active_agent,
                    retry_count,
                    json.dumps(state_data),
                    datetime.utcnow().isoformat()
                )
            )

            connection.commit()

            connection.close()

            return {

                "success": True,

                "checkpoint_id": checkpoint_id
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


    # load checkpoint

    def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> Dict:
        """
        Retrieve checkpoint by ID.
        """

        try:

            connection = sqlite3.connect(
                self.db_path
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM checkpoints
                WHERE checkpoint_id = ?
                """,
                (checkpoint_id,)
            )

            row = cursor.fetchone()

            connection.close()

            if not row:

                return {

                    "success": False,

                    "error": (
                        "Checkpoint not found."
                    )
                }

            return {

                "success": True,

                "checkpoint": {

                    "checkpoint_id": row[1],

                    "session_id": row[2],

                    "workflow_status": row[3],

                    "active_agent": row[4],

                    "retry_count": row[5],

                    "state_data": json.loads(
                        row[6]
                    ),

                    "created_at": row[7]
                }
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


    # list checkpoints

    def list_checkpoints(
        self,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Retrieve stored checkpoints.
        """

        try:

            connection = sqlite3.connect(
                self.db_path
            )

            cursor = connection.cursor()

            if session_id:

                cursor.execute(
                    """
                    SELECT checkpoint_id,
                           workflow_status,
                           active_agent,
                           created_at
                    FROM checkpoints
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                    """,
                    (session_id,)
                )

            else:

                cursor.execute(
                    """
                    SELECT checkpoint_id,
                           workflow_status,
                           active_agent,
                           created_at
                    FROM checkpoints
                    ORDER BY created_at DESC
                    """
                )

            rows = cursor.fetchall()

            connection.close()

            checkpoints = []

            for row in rows:

                checkpoints.append({

                    "checkpoint_id": row[0],

                    "workflow_status": row[1],

                    "active_agent": row[2],

                    "created_at": row[3]
                })

            return {

                "success": True,

                "checkpoints": checkpoints
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


# global checkpoint manager 

sqlite_checkpoint_manager = (
    SQLiteCheckpointManager()
)