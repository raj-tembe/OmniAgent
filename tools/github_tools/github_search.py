import os
from typing import Dict, List

from github import Github


# github client

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)

github_client = Github(GITHUB_TOKEN)


# github search tool

class GitHubSearchTool:
    """
    GitHub repository search tool.

    Responsibilities:
    - search repositories
    - retrieve implementation references
    - support technical research
    - discover open-source patterns
    """

    def __init__(
        self,
        max_results: int = 5
    ):

        self.max_results = max_results


    # search repo

    def search_repositories(
        self,
        query: str
    ) -> Dict:
        """
        Search GitHub repositories.
        """

        try:

            repositories = (
                github_client.search_repositories(
                    query=query
                )
            )

            results = []

            for repo in repositories[
                :self.max_results
            ]:

                results.append({

                    "name": repo.full_name,

                    "description": repo.description,

                    "stars": repo.stargazers_count,

                    "language": repo.language,

                    "url": repo.html_url,

                    "topics": repo.get_topics()
                })

            return {

                "success": True,

                "query": query,

                "repositories": results
            }

        except Exception as e:

            return {

                "success": False,

                "query": query,

                "error": str(e),

                "repositories": []
            }


# global helper 

def github_search(
    query: str,
    max_results: int = 5
) -> Dict:
    """
    Simple GitHub repository search helper.
    """

    tool = GitHubSearchTool(
        max_results=max_results
    )

    return tool.search_repositories(query)