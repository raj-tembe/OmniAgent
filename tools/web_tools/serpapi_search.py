import os
import logging
from typing import Dict

from serpapi import GoogleSearch


# serpapi configuration

SERPAPI_API_KEY = os.getenv(
    "SERPAPI_API_KEY"
)


# serpapi search tool

class SerpAPISearchTool:
    """
    Google Search tool using SerpAPI.

    Responsibilities:
    - retrieve Google search results
    - fetch technical articles
    - gather implementation references
    - support researcher agent
    """

    def __init__(
        self,
        num_results: int = 5
    ):

        self.num_results = num_results


    # search

    def search(
        self,
        query: str
    ) -> Dict:
        """
        Execute Google search.
        """

        try:

            params = {

                "engine": "google",

                "q": query,

                "api_key": SERPAPI_API_KEY,

                "num": self.num_results
            }

            search = GoogleSearch(params)

            results = search.get_dict()

            organic_results = results.get(
                "organic_results",
                []
            )

            return {

                "success": True,

                "query": query,

                "results": organic_results
            }

        except Exception as e:
            logging.getLogger(__name__).error("SerpAPISearch.search failed: %s", e, exc_info=True)

            return {

                "success": False,

                "query": query,

                "error": str(e),

                "results": []
            }


#global helper for simplified search usage

def serpapi_search(
    query: str,
    num_results: int = 5
) -> Dict:
    """
    Simple SerpAPI helper.
    """

    tool = SerpAPISearchTool(
        num_results=num_results
    )

    return tool.search(query)