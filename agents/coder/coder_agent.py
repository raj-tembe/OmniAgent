from typing import Dict, Optional
import re

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage

from graph.state import AgentState
from agents.coder.coder_chain import create_coder_chain
from agents.diffing import compute_file_diffs
from schemas.coder_schema import CoderOutput
from tools.agent_tools.todo_tool import TodoTool
from bus import bus, FileDiff


def _build_fallback_response(project_name: str, entry_point: str, generated_files: Dict) -> CoderOutput:
    """Create a safe fallback coder response when structured output parsing fails."""
    return CoderOutput(
        generated_files=generated_files or {},
        explanation="Generated project files from the latest workflow state.",
        coding_status="completed",
        next_agent="executor",
        project_name=project_name or "current_project",
        entry_point=entry_point or "app.py",
    )


def _extract_project_name(user_request: str) -> str:
    """
    Extract project name from user request.
    
    Tries to extract from:
    1. Quoted names: "project 'name'" or "create 'name'"
    2. Filenames: "calculator.html" -> "calculator"
    3. First few words of request
    """
    
    # Try quoted names: 'project_name' or "project_name"
    quoted_match = re.search(r"['\"]([^'\"]+)['\"]", user_request)
    if quoted_match:
        name = quoted_match.group(1)
        # Remove file extension if present
        name = name.rsplit('.', 1)[0]
        # Sanitize name (remove spaces, special chars)
        name = re.sub(r'[^\w-]', '_', name)
        if name:
            return name
    
    # Fallback: use first few words (max 2)
    words = user_request.split()[:2]
    project_name = '_'.join(words).lower()
    project_name = re.sub(r'[^\w-]', '_', project_name)
    
    return project_name or "generated_project"


def _sync_todos(plan, current_step: str, existing_todos):
    """
    Keep the visible todo list roughly in sync with the plan: initialize it
    from `plan` the first time it's empty, then mark whichever item matches
    `current_step` as in-progress. Final "completed" status is set by
    executor_agent once execution actually succeeds — coder only knows it
    started working on a step, not whether that step held up.
    """
    todos = existing_todos if existing_todos else TodoTool.write(plan or [])

    if not current_step:
        return todos

    match = next((t for t in todos if t.get("content") == current_step), None)
    if match and match.get("status") == "pending":
        todos = TodoTool.update_status(todos, match["id"], "in_progress")

    return todos


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
    
    # Extract or preserve project name
    project_name = state.get("project_name", "")
    if not project_name:
        project_name = _extract_project_name(user_request)

    current_step = state.get("current_step", "")

    plan = state.get("plan", [])

    todos = _sync_todos(plan, current_step, state.get("todos", []))

    generated_files = state.get(
        "generated_files",
        {}
    )

    interactive = state.get("interactive", False)

    error_message = state.get(
        "error_message",
        ""
    )

    entry_point = state.get("entry_point", "app.py") or "app.py"

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

    used_fallback = False
    try:
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
        entry_point = getattr(response, "entry_point", entry_point) or entry_point
        next_agent = response.next_agent

    except (OutputParserException, AttributeError, TypeError, ValueError) as exc:
        response = _build_fallback_response(
            project_name=project_name,
            entry_point=entry_point,
            generated_files=generated_files,
        )
        updated_files = response.generated_files
        explanation = response.explanation
        coding_status = response.coding_status
        entry_point = response.entry_point
        next_agent = response.next_agent
        used_fallback = True
        if error_message:
            explanation = f"{explanation} Fallback due to parser error: {exc}"

    if interactive and getattr(response, "requires_human_approval", False):
        next_agent = "human"

    #compute and publish diffs for the desktop app's inline diff view —
    #before every branch below decides on messaging/routing, since diffing
    #only needs the before/after file snapshots, not the workflow status
    session_id = state.get("session_id")
    for file_diff in compute_file_diffs(generated_files, updated_files):
        bus.publish(FileDiff(
            filename=file_diff["filename"],
            change_type=file_diff["change_type"],
            diff=file_diff["diff"],
            agent="coder",
            session_id=session_id,
        ))


    #coder workflow logic

    # first genration
    if used_fallback:
        coder_message = (
            "⚠️ Coding Agent: "
            "The model returned an incomplete structured response. "
            "Using a safe fallback structure to continue the workflow."
        )
    elif retry_count == 0 and not error_message:

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
        "project_name": project_name,
        "entry_point": entry_point,

        # coding metadata
        "coding_status": coding_status,
        "coding_explanation": explanation,

        # visible task list
        "todos": todos,

        # workflow
        "next_agent": next_agent,
        "current_agent": "coder",

        # reset execution state before rerun
        "execution_success": False,
        "execution_output": "",

        # clear previous errors after regeneration
        "error_message": "",
    }