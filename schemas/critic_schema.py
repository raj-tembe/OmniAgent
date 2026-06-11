from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


#review status

ReviewStatus = Literal[
    "approved",
    "needs_improvement",
    "failed",
    "unsafe"
]


#next agent 

NextAgent = Literal[
    "coder",
    "human",
    "end"
]


#issue severity 

IssueSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical"
]


#issue model

class ReviewIssue(BaseModel):
    """
    Represents a detected code issue.
    """

    issue: str = Field(
        ...,
        description="Description of the detected issue."
    )

    severity: IssueSeverity = Field(
        ...,
        description="Severity level of the issue."
    )

    recommendation: str = Field(
        ...,
        description="Suggested fix or improvement."
    )


# critic output schema

class CriticOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """
    Structured output schema for Critic Agent.

    Responsibilities:
    - evaluate generated code
    - analyze execution quality
    - detect vulnerabilities
    - validate architecture
    - determine workflow continuation
    """

    # review status

    review_status: ReviewStatus = Field(
        ...,
        description="Overall review result."
    )


    #quality score

    quality_score: float = Field(
        ...,
        ge=0,
        le=10,
        description=(
            "Overall quality score from 0-10."
        )
    )


    # review summary

    summary: str = Field(
        ...,
        description=(
            "Short summary of review findings."
        )
    )


    #detailed feedback

    feedback: str = Field(
        ...,
        description=(
            "Detailed technical review feedback."
        )
    )


    #detected issues

    issues: Optional[List[ReviewIssue]] = Field(
        default=None,
        description="List of detected issues."
    )


    #security analysis

    security_issues: Optional[List[str]] = Field(
        default=None,
        description="Detected security concerns."
    )


    #architecture review

    architecture_review: Optional[str] = Field(
        default=None,
        description=(
            "Evaluation of project structure "
            "and architecture."
        )
    )


    #testing review

    testing_review: Optional[str] = Field(
        default=None,
        description=(
            "Evaluation of testing coverage "
            "and reliability."
        )
    )


    #improvement suggestions

    improvement_suggestions: Optional[List[str]] = Field(
        default=None,
        description="Recommended improvements."
    )


    #next workflow agent

    next_agent: NextAgent = Field(
        ...,
        description=(
            "Next workflow agent."
        )
    )


    #human approval

    requires_human_approval: bool = Field(
        default=False,
        description=(
            "Whether workflow requires "
            "human review/intervention."
        )
    )