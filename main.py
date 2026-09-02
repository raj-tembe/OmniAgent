#!/usr/bin/env python3
"""
OmniAgent - Multi-agent autonomous system for research, planning, coding, and execution.

CLI entry point for autonomous workflows.
"""

import sys
import argparse
import json
import logging
import uuid
from typing import Optional

from graph.workflow import OmniAgentCallbacks, omniagent_graph
from bus import bus, SessionStarted, SessionCompleted, SessionError


# configure logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# CLI interface

def run_workflow(
    user_request: str,
    interactive: bool = False,
    verbose: bool = False,
    agent_mode: str = "build",
    auto_approve: bool = False,
    session_id: str = None,
) -> dict:
    """
    Execute OmniAgent workflow for given user request.

    Args:
        user_request: Task description for autonomous execution
        interactive: Enable human approval nodes if available
        verbose: Enable detailed execution logging
        agent_mode: "build" (full access) or "plan" (read-only, denies
            write/bash by default — see permission/modes.py)
        auto_approve: Auto-approve "ask"
            permission rules automatically. Explicit "deny" rules still apply.
        session_id: Correlate this run with a pre-generated id (e.g. one the
            server layer already handed back to a caller before the run
            started). Falls back to generating one when not given, same as
            before.

    Returns:
        Workflow execution result with status and generated artifacts
    """

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting OmniAgent workflow for: {user_request[:100]}...")

    # Generate unique thread ID for checkpointing / event correlation,
    # unless the caller already has one
    thread_id = session_id or str(uuid.uuid4())

    bus.publish(SessionStarted(user_request=user_request, session_id=thread_id))

    try:
        # Initialize workflow input state
        initial_state = {
            "user_request": user_request,
            "interactive": interactive,
            "session_id": thread_id,
            "agent_mode": agent_mode,
            "auto_approve": auto_approve,
            "messages": [],
            "plan": [],
            "code": "",
            "execution_success": False,
            "quality_score": 0.0,
            "memory_context": [],
            "security_issues": [],
            "entry_point": "app.py",
        }

        # Configuration for LangGraph checkpoint saver
        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "callbacks": [OmniAgentCallbacks(session_id=thread_id)],
        }

        # Execute workflow
        result = omniagent_graph.invoke(initial_state, config=config)

        # Log execution results
        logger.info(f"Workflow completed with status: {result.get('execution_success')}")
        logger.info(f"Quality score: {result.get('quality_score', 0.0)}")

        if result.get('security_issues'):
            logger.warning(f"Security issues detected: {result['security_issues']}")

        bus.publish(SessionCompleted(
            execution_success=bool(result.get('execution_success')),
            quality_score=result.get('quality_score'),
            session_id=thread_id,
        ))

        result["session_id"] = thread_id
        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        bus.publish(SessionError(error_message=str(e), session_id=thread_id))
        return {
            "success": False,
            "error": str(e),
            "execution_success": False,
            "session_id": thread_id,
        }


def display_results(result: dict) -> None:
    """
    Display workflow execution results.

    Args:
        result: Workflow execution output
    """

    print("\n" + "=" * 60)
    print("OMNIAGENT EXECUTION RESULTS")
    print("=" * 60 + "\n")

    # Display execution status
    status = "✓ SUCCESS" if result.get('execution_success') else "✗ FAILED"
    print(f"Status: {status}")

    # Display quality score
    quality = result.get('quality_score', 0.0)
    print(f"Quality Score: {quality:.2f}/10.0")

    # Display plan
    if result.get('plan'):
        print(f"\nPlan ({len(result['plan'])} steps):")
        for i, step in enumerate(result['plan'], 1):
            print(f"  {i}. {step}")

    # Display generated code
    if result.get('generated_files'):
        files = result['generated_files']
        print(f"\nGenerated Files ({len(files)} files):")
        print("-" * 40)
        for filename, content in files.items():
            print(f"  [{filename}] — {len(content)} chars")
        print("-" * 40)
        project_name = result.get('project_name', 'unknown')
        from config import GENERATED_PROJECT_DIR
        print(f"\nProject saved to: {GENERATED_PROJECT_DIR}/{project_name}/")

    # Display security issues
    if result.get('security_issues'):
        print(f"\nSecurity Issues ({len(result['security_issues'])}):")
        for issue in result['security_issues']:
            print(f"  - {issue}")

    # Display errors
    if result.get('error'):
        print(f"\nError: {result['error']}")

    print("\n" + "=" * 60 + "\n")


def main():
    """
    CLI entry point for OmniAgent.
    """

    parser = argparse.ArgumentParser(
        description='OmniAgent - Autonomous multi-agent system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Build a Python REST API with FastAPI"
  python main.py --task "Analyze ML model training approach"
  python main.py --interactive --verbose "Debug memory leak in Node.js app"
        """
    )

    # Positional argument for task
    parser.add_argument(
        'task',
        nargs='?',
        type=str,
        help='Task description for autonomous execution'
    )

    # Optional arguments
    parser.add_argument(
        '--task',
        dest='task_arg',
        type=str,
        help='Task description (alternative to positional)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable human approval checkpoints'
    )

    parser.add_argument(
        '--agent-mode',
        dest='agent_mode',
        choices=['build', 'plan'],
        default='build',
        help="Agent mode: 'build' (default, full access) or 'plan' (read-only, denies file writes and code execution)"
    )

    parser.add_argument(
        '--plan',
        dest='plan_shorthand',
        action='store_true',
        help="Shorthand for --agent-mode plan"
    )

    parser.add_argument(
        '--auto',
        dest='auto_approve',
        action='store_true',
        help="Auto-approve 'ask' permission rules (explicit 'deny' rules are still enforced)"
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug-level logging'
    )

    # Parse arguments
    args = parser.parse_args()

    # Determine user task
    user_request = args.task or args.task_arg

    if not user_request:
        print("OmniAgent - Multi-agent autonomous system")
        print("\nUsage: python main.py <task> [--interactive] [--verbose]")
        print("\nExample: python main.py \"Build a Python REST API\"")
        print("\nFor more help: python main.py --help")
        sys.exit(1)

    try:
        # Run workflow
        agent_mode = "plan" if args.plan_shorthand else args.agent_mode
        result = run_workflow(
            user_request=user_request,
            interactive=args.interactive,
            verbose=args.verbose,
            agent_mode=agent_mode,
            auto_approve=args.auto_approve,
        )

        # Display results
        display_results(result)

        # Exit with appropriate code
        sys.exit(0 if result.get('execution_success') else 1)

    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
