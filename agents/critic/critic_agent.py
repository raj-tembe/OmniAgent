from typing import Dict

from langchain_core.messages import AIMessage

from graph.state import AgentState

from agents.critic.critic_chain import (
    create_critic_chain
)


def critic_agent(state: AgentState) -> Dict:
    """
    Critic Agent

    Responsibilities:
    - Evaluate generated code
    - Review execution results
    - Detect vulnerabilities
    - Analyze architecture quality
    - Decide whether code is acceptable
    """

    #extract state

    user_request = state.get(
        "user_request",
        ""
    )

    current_step = state.get(
        "current_step",
        ""
    )

    generated_files = state.get(
        "generated_files",
        {}
    )

    interactive = state.get("interactive", False)

    execution_success = state.get(
        "execution_success",
        False
    )

    execution_logs = state.get(
        "execution_logs",
        ""
    )

    execution_output = state.get(
        "execution_output",
        ""
    )

    error_message = state.get(
        "error_message",
        ""
    )

    retry_count = state.get(
        "retry_count",
        0
    )


    #create chain

    critic_chain = create_critic_chain()


    #invoke critic agent chain

    response = critic_chain.invoke({

        "user_request": user_request,

        "current_step": current_step,

        "generated_files": generated_files,

        "execution_success": execution_success,

        "execution_logs": execution_logs,

        "execution_output": execution_output,

        "error_message": error_message,

        "retry_count": retry_count,
    })


    #extract structured response

    review_status = response.review_status

    quality_score = response.quality_score

    summary = response.summary

    feedback = response.feedback

    next_agent = response.next_agent

    if interactive and getattr(response, "requires_human_approval", False):
        next_agent = "human"

    issues = response.issues or []

    security_issues = (
        response.security_issues or []
    )

    improvement_suggestions = (
        response.improvement_suggestions or []
    )


    #review success

    if review_status == "approved":

        critic_message = (
            "Critic Agent: "
            "Implementation approved.\n\n"
            f"Quality Score: {quality_score}/10\n\n"
            f"Summary:\n{summary}"
        )

    #review failed

    elif review_status in [
        "needs_improvement",
        "failed"
    ]:

        critic_message = (
            "Critic Agent: "
            "Issues detected in implementation.\n\n"
            f"Quality Score: {quality_score}/10\n\n"
            f"Feedback:\n{feedback}"
        )

    #security failure

    elif review_status == "unsafe":

        critic_message = (
            "Critic Agent: "
            "Security risks detected.\n\n"
            f"Security Issues:\n"
            f"{security_issues}"
        )

    #feedback

    else:

        critic_message = (
            "Critic Agent: "
            "Unexpected review state encountered."
        )


    #return update state

    return {

        "messages": [
            AIMessage(content=critic_message)
        ],

        # Review Results
        "review_status": review_status,

        "quality_score": quality_score,

        "critic_feedback": feedback,

        "critic_summary": summary,

        "review_issues": issues,

        "security_issues": security_issues,

        "improvement_suggestions": (
            improvement_suggestions
        ),

        # Workflow
        "next_agent": next_agent,
        "current_agent": "critic",

        # Reset retry count on approval so future workflow phases start fresh
        "retry_count": 0 if review_status == "approved" else state.get("retry_count", 0),
    }