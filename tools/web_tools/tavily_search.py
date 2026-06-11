import os
import logging
from typing import Dict, List, Optional

from tavily import TavilyClient


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
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise EnvironmentError("TAVILY_API_KEY is not set.")
        self.client = TavilyClient(api_key=api_key)


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

            response = self.client.search(

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
            logging.getLogger(__name__).error("TavilySearchTool.search failed: %s", e, exc_info=True)

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