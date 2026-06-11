from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


#research status

ResearchStatus = Literal[
    "searching",
    "analyzing",
    "completed",
    "failed"
]


#next agent types

NextAgent = Literal[
    "coder",
    "planner",
    "critic",
    "human"
]


#source types
SourceType = Literal[
    "documentation",
    "github",
    "research_paper",
    "tutorial",
    "article",
    "api_reference",
    "other"
]


#research source model

class ResearchSource(BaseModel):
    """
    Represents a research source/reference.
    """

    title: str = Field(
        ...,
        description="Title of the source."
    )

    source_type: SourceType = Field(
        ...,
        description="Type of research source."
    )

    url: Optional[str] = Field(
        default=None,
        description="Source URL if available."
    )

    summary: str = Field(
        ...,
        description="Short summary of the source."
    )

    relevance_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Relevance score for the workflow."
    )


#research finding model

class ResearchFinding(BaseModel):
    """
    Represents an important research insight.
    """

    topic: str = Field(
        ...,
        description="Research topic or category."
    )

    finding: str = Field(
        ...,
        description="Important technical finding."
    )

    implementation_impact: Optional[str] = Field(
        default=None,
        description=(
            "How this finding affects implementation."
        )
    )


#research output schema
class ResearchOutput(BaseModel):    
    
    model_config = ConfigDict(extra="forbid")    
    """
    Structured output schema for Research Agent.

    Responsibilities:
    - gather implementation knowledge
    - analyze technical references
    - summarize research findings
    - support downstream coding
    """

    #research status

    research_status: ResearchStatus = Field(
        ...,
        description="Current research workflow phase."
    )


    #research summary

    research_summary: str = Field(
        ...,
        description=(
            "Overall summary of research findings."
        )
    )


    #research findings

    findings: List[ResearchFinding] = Field(
        ...,
        description=(
            "Important implementation insights."
        )
    )


    #sources

    sources: List[ResearchSource] = Field(
        ...,
        description=(
            "Research references and sources."
        )
    )


    #implementation recommendations

    implementation_recommendations: List[str] = Field(
        ...,
        description=(
            "Recommended implementation strategies."
        )
    )


    #technology & tools suggestions

    recommended_technologies: Optional[List[str]] = Field(
        default=None,
        description=(
            "Recommended libraries/frameworks/tools."
        )
    )


    #security considerations

    security_considerations: Optional[List[str]] = Field(
        default=None,
        description=(
            "Security recommendations identified "
            "during research."
        )
    )


    #performance considerations

    performance_considerations: Optional[List[str]] = Field(
        default=None,
        description=(
            "Performance optimization insights."
        )
    )


    #architectural suggestions

    architecture_suggestions: Optional[List[str]] = Field(
        default=None,
        description=(
            "Recommended architectural patterns."
        )
    )


    #next agent

    next_agent: NextAgent = Field(
        ...,
        description=(
            "Next workflow agent."
        )
    )


    #human intervention 

    requires_human_approval: bool = Field(
        default=False,
        description=(
            "Whether research results require "
            "human review."
        )
    )
    