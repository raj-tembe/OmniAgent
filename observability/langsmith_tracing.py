import os
from typing import Dict

from langsmith import Client


# langsmith config

LANGCHAIN_TRACING_V2 = os.getenv(
    "LANGCHAIN_TRACING_V2",
    "true"
)

LANGCHAIN_API_KEY = os.getenv(
    "LANGCHAIN_API_KEY"
)

LANGCHAIN_PROJECT = os.getenv(
    "LANGCHAIN_PROJECT",
    "OmniAgent"
)


# langsmith tracer 

class LangSmithTracer:
    """
    LangSmith observability integration.

    Responsibilities:
    - workflow tracing
    - agent execution tracking
    - debugging orchestration flows
    - monitoring LLM interactions
    """

    def __init__(self):

        self.client = Client(
            api_key=LANGCHAIN_API_KEY
        )

        self.project_name = (
            LANGCHAIN_PROJECT
        )


    # trace event

    def trace_event(
        self,
        event_name: str,
        metadata: Dict
    ) -> Dict:
        """
        Log workflow tracing event.
        """

        try:

            trace_data = {

                "event_name": event_name,

                "project": self.project_name,

                "metadata": metadata
            }

            return {

                "success": True,

                "trace": trace_data
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


# global tracer

langsmith_tracer = (
    LangSmithTracer()
)