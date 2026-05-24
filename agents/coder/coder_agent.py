from typing import Dict

from langchain_core.messages import AIMessage

from graph.state import AgentState
from agents.coder.coder_chain import create_coder_chain


def coder_agent(state: AgentState) -> Dict:
    """
    Coding Agent

    Responsibilities:
    - Generate source code
    - Create project files
    - Fix execution errors
    - Update generated codebase
    - Prepare output for execution
    """

    #extract state

    user_request = state.get("user_request", "")

    current_step = state.get("current_step", "")

    plan = state.get("plan", [])

    generated_files = state.get(
        "generated_files",
        {}
    )

    error_message = state.get(
        "error_message",
        ""
    )

    retry_count = state.get(
        "retry_count",
        0
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )

    research_data = state.get(
        "research_data",
        []
    )


    #create coder chain

    coder_chain = create_coder_chain()


    #invoke coder chain

    response = coder_chain.invoke({

        "user_request": user_request,

        "current_step": current_step,

        "plan": plan,

        "generated_files": generated_files,

        "error_message": error_message,

        "retry_count": retry_count,

        "critic_feedback": critic_feedback,

        "research_data": research_data,
    })


    #extract structured output

    updated_files = response.generated_files

    explanation = response.explanation

    coding_status = response.coding_status

    next_agent = response.next_agent


    #coder workflow logic

    # first genration
    if retry_count == 0 and not error_message:

        coder_message = (
            "💻 Coding Agent: "
            "Generating project files and implementation..."
        )

    # error fioxing mode
    elif error_message:

        coder_message = (
            "🛠️ Coding Agent: "
            "Execution failure detected.\n\n"
            f"Error:\n{error_message}\n\n"
            "Attempting autonomous repair..."
        )

    # critic revision mode
    elif critic_feedback:

        coder_message = (
            "🧪 Coding Agent: "
            "Critic feedback received.\n\n"
            "Improving implementation quality..."
        )

    # general update
    else:

        coder_message = (
            "⚡ Coding Agent: "
            "Updating implementation..."
        )


    #return update state

    return {

        # convarsation update
        "messages": [
            AIMessage(content=coder_message)
        ],

        # generate codebase 
        "generated_files": updated_files,

        # coding metadata
        "coding_status": coding_status,
        "coding_explanation": explanation,

        # workflow
        "next_agent": next_agent,

        # reset execution state before rerun
        "execution_success": False,
        "execution_output": "",

        # clear previous errors after regeneration
        "error_message": "",
    }