import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


# postgres config 

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost"
)

POSTGRES_PORT = os.getenv(
    "POSTGRES_PORT",
    "5432"
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "omniagent"
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "postgres"
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "postgres"
)


# postgres checkpoint manager

class PostgresCheckpointManager:
    """
    PostgreSQL workflow checkpoint system.

    Responsibilities:
    - scalable workflow persistence
    - distributed checkpoint storage
    - production-grade recovery
    """

    def __init__(self):
        self.connection = None


    # create connection

    def _create_connection(self):

        return psycopg2.connect(

            host=POSTGRES_HOST,

            port=POSTGRES_PORT,

            dbname=POSTGRES_DB,

            user=POSTGRES_USER,

            password=POSTGRES_PASSWORD
        )


    # initialize Db

    def _ensure_connection(self):
        if self.connection is None:
            self.connection = self._create_connection()
            self._initialize_database()

        return self.connection


    def _initialize_database(self) -> None:
        """
        Create checkpoint table.
        """

        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (

                id SERIAL PRIMARY KEY,

                checkpoint_id TEXT UNIQUE,

                session_id TEXT,

                workflow_status TEXT,

                active_agent TEXT,

                retry_count INTEGER,

                state_data JSONB,

                created_at TIMESTAMP
            )
            """
        )

        self.connection.commit()

        cursor.close()


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

            connection = self._ensure_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO checkpoints (

                    checkpoint_id,
                    session_id,
                    workflow_status,
                    active_agent,
                    retry_count,
                    state_data,
                    created_at

                ) VALUES (%s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (checkpoint_id)

                DO UPDATE SET

                    workflow_status = EXCLUDED.workflow_status,
                    active_agent = EXCLUDED.active_agent,
                    retry_count = EXCLUDED.retry_count,
                    state_data = EXCLUDED.state_data
                """,
                (
                    checkpoint_id,
                    session_id,
                    workflow_status,
                    active_agent,
                    retry_count,
                    json.dumps(state_data),
                    datetime.utcnow()
                )
            )

            self.connection.commit()

            cursor.close()

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
        Retrieve workflow checkpoint.
        """

        try:

            connection = self._ensure_connection()
            cursor = connection.cursor(
                cursor_factory=RealDictCursor
            )

            cursor.execute(
                """
                SELECT *
                FROM checkpoints
                WHERE checkpoint_id = %s
                """,
                (checkpoint_id,)
            )

            result = cursor.fetchone()

            cursor.close()

            if not result:

                return {

                    "success": False,

                    "error": (
                        "Checkpoint not found."
                    )
                }

            return {

                "success": True,

                "checkpoint": dict(result)
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }
