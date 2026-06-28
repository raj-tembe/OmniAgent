from typing import Dict
from langchain_core.messages import AIMessage
from graph.state import AgentState
from agents.researcher.researcher_chain import (
    create_researcher_chain
)


def researcher_agent(state: AgentState) -> Dict:
    """
    Research Agent

    Responsibilities:
    - Analyze technical requirements
    - Gather implementation guidance
    - Recommend frameworks/tools
    - Provide architecture insights
    - Support downstream coding workflow
    """

    # extract state

    user_request = state.get(
        "user_request",
        ""
    )

    current_step = state.get(
        "current_step",
        ""
    )

    plan = state.get(
        "plan",
        []
    )

    previous_research = state.get(
        "research_data",
        []
    )

    error_message = state.get(
        "error_message",
        ""
    )

    critic_feedback = state.get(
        "critic_feedback",
        ""
    )


    # create researcher chain

    researcher_chain = create_researcher_chain()


    # invoke researcher chain

    response = researcher_chain.invoke({

        "user_request": user_request,

        "current_step": current_step,

        "plan": plan,

        "research_data": previous_research,

        "error_message": error_message,

        "critic_feedback": critic_feedback,
    })


    # extract structured output

    research_status = response.research_status

    research_summary = response.research_summary

    findings = response.findings

    sources = response.sources

    implementation_recommendations = (
        response.implementation_recommendations
    )

    recommended_technologies = (
        response.recommended_technologies or []
    )

    security_considerations = (
        response.security_considerations or []
    )

    performance_considerations = (
        response.performance_considerations or []
    )

    architecture_suggestions = (
        response.architecture_suggestions or []
    )

    next_agent = response.next_agent


    # research status message

    if research_status == "searching":

        researcher_message = (
            "Research Agent: "
            "Analyzing technical requirements "
            "and gathering implementation insights..."
        )

    elif research_status == "analyzing":

        researcher_message = (
            "Research Agent: "
            "Evaluating frameworks, architecture patterns, "
            "and implementation strategies..."
        )

    elif research_status == "completed":

        researcher_message = (
            "Research Agent: "
            "Research completed successfully.\n\n"
            f"Summary:\n{research_summary}"
        )

    elif research_status == "failed":

        researcher_message = (
            "Research Agent: "
            "Research workflow encountered issues."
        )

    else:

        researcher_message = (
            "Research Agent: "
            "Unexpected research state detected."
        )


    # format research data

    formatted_findings = []

    for finding in findings:

        formatted_findings.append({

            "topic": finding.topic,

            "finding": finding.finding,

            "implementation_impact": (
                finding.implementation_impact
            )
        })


    formatted_sources = []

    for source in sources:

        formatted_sources.append({

            "title": source.title,

            "source_type": source.source_type,

            "url": source.url,

            "summary": source.summary,

            "relevance_score": (
                source.relevance_score
            )
        })


    # return updated state

    return {

        "messages": [
            AIMessage(content=researcher_message)
        ],

        # Research Status
        "research_status": research_status,

        "research_summary": research_summary,

        # Structured Research Data
        "research_data": formatted_findings,

        "research_sources": formatted_sources,

        # Recommendations
        "implementation_recommendations": (
            implementation_recommendations
        ),

        "recommended_technologies": (
            recommended_technologies
        ),

        "security_considerations": (
            security_considerations
        ),

        "performance_considerations": (
            performance_considerations
        ),

        "architecture_suggestions": (
            architecture_suggestions
        ),

        # Workflow
        "next_agent": next_agent,
        "current_agent": "researcher",
    }