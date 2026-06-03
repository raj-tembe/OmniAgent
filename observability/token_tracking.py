from datetime import datetime
from typing import Dict, List


# token tracer 

class TokenTracker:
    """
    LLM token monitoring system.

    Responsibilities:
    - track token usage
    - estimate API costs
    - monitor agent consumption
    - optimize workflow efficiency
    """

    def __init__(self):

        self.token_usage = []


    # record token usage 

    def record_usage(
        self,
        agent_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str
    ) -> None:
        """
        Store token usage event.
        """

        total_tokens = (
            prompt_tokens
            + completion_tokens
        )

        self.token_usage.append({

            "agent_name": agent_name,

            "model_name": model_name,

            "prompt_tokens": prompt_tokens,

            "completion_tokens": (
                completion_tokens
            ),

            "total_tokens": total_tokens,

            "timestamp": (
                datetime.utcnow()
                .isoformat()
            )
        })


    # total token count 

    def total_tokens(self) -> int:
        """
        Calculate overall token usage.
        """

        return sum(

            usage["total_tokens"]

            for usage in self.token_usage
        )


    # agent token summary 

    def tokens_by_agent(self) -> Dict:
        """
        Aggregate tokens per agent.
        """

        agent_summary = {}

        for usage in self.token_usage:

            agent = usage["agent_name"]

            current_total = (
                agent_summary.get(agent, 0)
            )

            agent_summary[agent] = (

                current_total

                + usage["total_tokens"]
            )

        return agent_summary


    # token report

    def generate_report(self) -> Dict:
        """
        Generate token analytics report.
        """

        return {

            "total_requests": len(
                self.token_usage
            ),

            "total_tokens": (
                self.total_tokens()
            ),

            "tokens_by_agent": (
                self.tokens_by_agent()
            ),

            "records": self.token_usage
        }


# global token tracer 

token_tracker = TokenTracker()