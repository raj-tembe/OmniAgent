from datetime import datetime
from typing import Dict, List


# metrics tracer 

class MetricsTracker:
    """
    Workflow metrics monitoring system.

    Responsibilities:
    - track workflow performance
    - monitor execution success
    - analyze agent efficiency
    - provide runtime analytics
    """

    def __init__(self):

        self.metrics = {

            "workflow_runs": 0,

            "successful_runs": 0,

            "failed_runs": 0,

            "agent_executions": {},

            "execution_times": [],

            "errors": []
        }


    # record workflow run

    def record_workflow_run(
        self,
        success: bool,
        execution_time: float
    ) -> None:
        """
        Track workflow execution.
        """

        self.metrics["workflow_runs"] += 1

        if success:

            self.metrics[
                "successful_runs"
            ] += 1

        else:

            self.metrics[
                "failed_runs"
            ] += 1

        self.metrics[
            "execution_times"
        ].append(execution_time)


    # record agent execution

    def record_agent_execution(
        self,
        agent_name: str
    ) -> None:
        """
        Track agent usage frequency.
        """

        current_count = self.metrics[
            "agent_executions"
        ].get(agent_name, 0)

        self.metrics[
            "agent_executions"
        ][agent_name] = current_count + 1


    # record error

    def record_error(
        self,
        agent_name: str,
        error_message: str
    ) -> None:
        """
        Track workflow errors.
        """

        self.metrics["errors"].append({

            "agent": agent_name,

            "error": error_message,

            "timestamp": (
                datetime.utcnow()
                .isoformat()
            )
        })


    # get metrics summary

    def get_summary(self) -> Dict:
        """
        Generate metrics summary.
        """

        total_runs = self.metrics[
            "workflow_runs"
        ]

        success_rate = 0

        if total_runs > 0:

            success_rate = (

                self.metrics[
                    "successful_runs"
                ]

                / total_runs

            ) * 100

        avg_execution_time = 0

        execution_times = self.metrics[
            "execution_times"
        ]

        if execution_times:

            avg_execution_time = (

                sum(execution_times)

                / len(execution_times)
            )

        return {

            "total_workflows": total_runs,

            "successful_runs": (
                self.metrics[
                    "successful_runs"
                ]
            ),

            "failed_runs": (
                self.metrics[
                    "failed_runs"
                ]
            ),

            "success_rate": round(
                success_rate,
                2
            ),

            "average_execution_time": round(
                avg_execution_time,
                2
            ),

            "agent_executions": (
                self.metrics[
                    "agent_executions"
                ]
            ),

            "total_errors": len(
                self.metrics["errors"]
            )
        }


# global metrics tracker

metrics_tracker = MetricsTracker()