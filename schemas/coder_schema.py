from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


#coding status options

CodingStatus = Literal[
    "generating",
    "updating",
    "fixing",
    "improving",
    "completed",
    "failed"
]


#coding agent options

NextAgent = Literal[
    "executor",
    "critic",
    "human"
]


#generated file model

class GeneratedFile(BaseModel):
    """
    Represents a single generated project file.
    """

    filename: str = Field(
        ...,
        description="Name/path of the generated file.",
        examples=[
            "app.py",
            "requirements.txt",
            "src/auth/jwt_handler.py"
        ]
    )

    content: str = Field(
        ...,
        description="Complete content of the generated file."
    )

    purpose: Optional[str] = Field(
        default=None,
        description=(
            "Optional explanation describing "
            "the purpose of this file."
        ),
        examples=[
            "Main FastAPI application entry point."
        ]
    )

#coder output schema
class CoderOutput(BaseModel):    
    model_config = ConfigDict(extra="forbid")    
    """
    Structured output schema for the Coding Agent.

    This schema ensures:
    - deterministic code generation
    - reliable workflow routing
    - autonomous repair support
    - production-grade orchestration
    """

#generated files

    generated_files: Dict[str, str] = Field(
        ...,
        description=(
            "Dictionary mapping filename to "
            "complete file content."
        ),
        examples=[
            {
                "app.py": (
                    "from fastapi import FastAPI\n"
                    "app = FastAPI()"
                ),
                "requirements.txt": (
                    "fastapi\nuvicorn"
                )
            }
        ]
    )


    # ============================================
    # FILE METADATA
    # ============================================

    project_name: str = Field(
        default="current_project",
        description="Name of the project being generated.",
        examples=["my_api", "calculator_app", "todo_list"]
    )

    entry_point: str = Field(
        default="app.py",
        description="The file to run to start or execute the project.",
        examples=["app.py", "main.py", "src/main.py"]
    )

    file_manifest: Optional[List[GeneratedFile]] = Field(
        default=None,
        description=(
            "Optional structured metadata for "
            "generated project files."
        )
    )


    # ============================================
    # CODE EXPLANATION
    # ============================================

    explanation: str = Field(
        ...,
        description=(
            "Short explanation of generated code, "
            "modifications, or fixes."
        ),
        examples=[
            (
                "Implemented JWT authentication "
                "using FastAPI and python-jose."
            )
        ]
    )


    # ============================================
    # CODING WORKFLOW STATUS
    # ============================================

    coding_status: CodingStatus = Field(
        ...,
        description=(
            "Current coding workflow phase."
        ),
        examples=[
            "generating"
        ]
    )


    # ============================================
    # NEXT WORKFLOW AGENT
    # ============================================

    next_agent: NextAgent = Field(
        ...,
        description=(
            "The next agent that should execute "
            "after coding completes."
        ),
        examples=[
            "executor"
        ]
    )


    # ============================================
    # ERROR FIX SUMMARY
    # ============================================

    fixes_applied: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of fixes applied during "
            "runtime error correction."
        ),
        examples=[
            [
                "Fixed missing Flask import",
                "Added dependency to requirements.txt"
            ]
        ]
    )


    # ============================================
    # DEPENDENCIES
    # ============================================

    dependencies: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of required dependencies/packages."
        ),
        examples=[
            [
                "fastapi",
                "uvicorn",
                "python-jose"
            ]
        ]
    )


    # ============================================
    # SECURITY NOTES
    # ============================================

    security_notes: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional security considerations "
            "or warnings."
        ),
        examples=[
            [
                "JWT secret should be stored in environment variables."
            ]
        ]
    )


    # ============================================
    # TESTING NOTES
    # ============================================

    testing_notes: Optional[str] = Field(
        default=None,
        description=(
            "Optional notes about testing strategy "
            "or validation."
        ),
        examples=[
            (
                "Basic endpoint tests added using pytest."
            )
        ]
    )


    # ============================================
    # HUMAN INTERVENTION FLAG
    # ============================================

    requires_human_approval: bool = Field(
        default=False,
        description=(
            "Whether coding changes require "
            "human approval before execution."
        ),
        examples=[
            False
        ]
    )