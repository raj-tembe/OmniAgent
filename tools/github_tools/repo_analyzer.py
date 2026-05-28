import os
from typing import Dict, List

from github import Github


# github client

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)

github_client = Github(GITHUB_TOKEN)


# repo analyzer

class RepoAnalyzerTool:
    """
    GitHub repository analysis tool.

    Responsibilities:
    - inspect repository structure
    - analyze technologies
    - retrieve important files
    - support implementation research
    """


    # analyze repo

    def analyze_repository(
        self,
        repo_name: str
    ) -> Dict:
        """
        Analyze GitHub repository.
        """

        try:

            repo = github_client.get_repo(
                repo_name
            )

            contents = repo.get_contents("")

            file_structure = []

            important_files = []

            while contents:

                file_content = contents.pop(0)

                if file_content.type == "dir":

                    contents.extend(
                        repo.get_contents(
                            file_content.path
                        )
                    )

                else:

                    file_structure.append(
                        file_content.path
                    )

                    if any(

                        keyword in file_content.path.lower()

                        for keyword in [

                            "readme",
                            "requirements",
                            "dockerfile",
                            "package.json",
                            "main.py",
                            "app.py"
                        ]
                    ):

                        important_files.append({

                            "path": file_content.path,

                            "download_url": (
                                file_content.download_url
                            )
                        })

            return {

                "success": True,

                "repository": repo.full_name,

                "description": repo.description,

                "stars": repo.stargazers_count,

                "language": repo.language,

                "topics": repo.get_topics(),

                "file_count": len(file_structure),

                "important_files": important_files,

                "file_structure": file_structure[:100]
            }

        except Exception as e:

            return {

                "success": False,

                "repository": repo_name,

                "error": str(e)
            }


# global helper

def analyze_repository(
    repo_name: str
) -> Dict:
    """
    Simple repository analyzer helper.
    """

    tool = RepoAnalyzerTool()

    return tool.analyze_repository(repo_name)