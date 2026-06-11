import logging
from typing import Dict, List

import arxiv


# arxiv search tool

class ArxivSearchTool:
    """
    arXiv research paper retrieval tool.

    Responsibilities:
    - retrieve AI/ML papers
    - gather academic references
    - support advanced technical research
    """

    def __init__(
        self,
        max_results: int = 5
    ):

        self.max_results = max_results


    # search papers

    def search(
        self,
        query: str
    ) -> Dict:
        """
        Search arXiv papers.
        """

        try:

            search = arxiv.Search(

                query=query,

                max_results=self.max_results,

                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []

            for paper in search.results():

                results.append({

                    "title": paper.title,

                    "authors": [
                        author.name
                        for author in paper.authors
                    ],

                    "summary": paper.summary,

                    "published": str(
                        paper.published
                    ),

                    "pdf_url": paper.pdf_url,

                    "entry_id": paper.entry_id
                })

            return {

                "success": True,

                "query": query,

                "papers": results
            }

        except Exception as e:
            logging.getLogger(__name__).error("ArxivSearchTool.search failed: %s", e, exc_info=True)

            return {

                "success": False,

                "query": query,

                "error": str(e),

                "papers": []
            }


#global helper for simplified search usage

def arxiv_search(
    query: str,
    max_results: int = 5
) -> Dict:
    """
    Simple arXiv helper.
    """

    tool = ArxivSearchTool(
        max_results=max_results
    )

    return tool.search(query)