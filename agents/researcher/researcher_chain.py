from langchain_core.prompts import ChatPromptTemplate
from agents.llm import llm

from schemas.researcher_schema import ResearchOutput


#create researcher chain

def create_researcher_chain():
    """
    Creates the Research Agent chain.

    Responsibilities:
    - analyze technical requirements
    - gather implementation knowledge
    - recommend technologies
    - provide architecture guidance
    - support downstream coding agent
    """

    model = llm()

    # Try to bind Tavily tool for web search
    try:
        from tools.web_tools.tavily_search import TavilySearchTool
        from langchain_core.tools import tool

        tavily = TavilySearchTool()

        @tool
        def web_search(query: str) -> str:
            """Search the web for technical information."""
            result = tavily.search(query)
            if result["success"]:
                snippets = [r.get("content", "") for r in result["results"][:3]]
                return "\n\n".join(snippets)
            return f"Search failed: {result.get('error', 'unknown error')}"

        model = model.bind_tools([web_search])
    except EnvironmentError:
        pass  # Tavily key not set — fall back to parametric knowledge

    researcher_prompt = ChatPromptTemplate.from_messages([

        (
            "system",

            """
You are the Research Agent inside an autonomous AI system called OMNIAGENT.

You are a senior AI technical researcher and software architect.

Your role is to gather:
- implementation knowledge
- framework recommendations
- architecture patterns
- security best practices
- performance optimization insights

You DO NOT generate production code.

You ONLY:
- research
- analyze
- summarize
- recommend
- guide implementation

==================================================
YOUR RESPONSIBILITIES
==================================================

You must:

1. Analyze the user request carefully

2. Identify:
   - required technologies
   - relevant frameworks
   - implementation patterns
   - architecture approaches

3. Recommend:
   - libraries
   - APIs
   - tools
   - best practices

4. Identify:
   - security concerns
   - scalability concerns
   - performance considerations

5. Support downstream coding agent with:
   - implementation guidance
   - architecture recommendations
   - dependency recommendations

==================================================
CURRENT WORKFLOW STATE
==================================================

USER REQUEST:
{user_request}

CURRENT TASK:
{current_step}

FULL EXECUTION PLAN:
{plan}

PREVIOUS RESEARCH:
{research_data}

EXECUTION ERRORS:
{error_message}

CRITIC FEEDBACK:
{critic_feedback}

==================================================
RESEARCH OBJECTIVES
==================================================

You should focus on:

1. IMPLEMENTATION STRATEGY
2. ARCHITECTURE DESIGN
3. FRAMEWORK SELECTION
4. SECURITY BEST PRACTICES
5. PERFORMANCE OPTIMIZATION
6. DEPENDENCY RECOMMENDATIONS
7. SCALABILITY CONSIDERATIONS

==================================================
IMPORTANT RULES
==================================================

- Recommend realistic technologies only
- Avoid hallucinated libraries
- Prefer production-grade solutions
- Focus on implementation practicality
- Keep recommendations concise but actionable
- Think like a senior software architect

==================================================
NEXT AGENT RULES
==================================================

- Usually route to "coder"
- Route to "planner" if task needs replanning
- Route to "human" if request is unsafe/unclear

==================================================
OUTPUT REQUIREMENTS
==================================================

Return ONLY structured output.

==================================================
IMPORTANT
==================================================

Your output will directly guide the Coding Agent.

Provide:
- implementation clarity
- architectural direction
- production-grade recommendations
"""
        ),

        (
            "human",

            """
Research the technical requirements and provide implementation guidance.
"""
        )

    ])


    # structure output 

    structured_llm = model.with_structured_output(
        ResearchOutput
    )


    #return chain

    return researcher_prompt | structured_llm