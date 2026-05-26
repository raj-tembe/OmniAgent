import os
from typing import Dict, List, Optional

from tavily import TavilyClient


#tavily client initialization

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

client = TavilyClient(
    api_key=TAVILY_API_KEY
)


#tavily search tool

class TavilySearchTool:
    """
    Tavily-powered web search tool.

    Responsibilities:
    - perform AI-optimized web search
    - retrieve technical documentation
    - gather implementation resources
    - support research workflows
    """

    def __init__(
        self,
        max_results: int = 5
    ):

        self.max_results = max_results


    #search

    def search(
        self,
        query: str,
        search_depth: str = "advanced"
    ) -> Dict:
        """
        Execute Tavily web search.
        """

        try:

            response = client.search(

                query=query,

                search_depth=search_depth,

                max_results=self.max_results
            )

            return {

                "success": True,

                "query": query,

                "results": response.get(
                    "results",
                    []
                )
            }

        except Exception as e:

            return {

                "success": False,

                "query": query,

                "error": str(e),

                "results": []
            }


# helper function for simplified search usage

def tavily_search(
    query: str,
    max_results: int = 5
) -> Dict:
    """
    Simple Tavily search helper.
    """

    tool = TavilySearchTool(
        max_results=max_results
    )

    return tool.search(query)