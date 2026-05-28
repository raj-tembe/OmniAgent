from typing import Dict, List


# commit generator tool

class CommitMessageGenerator:
    """
    Git commit message generator.

    Responsibilities:
    - generate meaningful commit messages
    - summarize code changes
    - support workflow automation
    """


    # generate commit msg

    @staticmethod
    def generate_commit_message(
        changed_files: List[str],
        change_summary: str,
        commit_type: str = "feat"
    ) -> Dict:
        """
        Generate standardized commit message.
        """

        try:

            short_summary = (
                change_summary.strip()
                .replace("\n", " ")
            )

            if len(short_summary) > 72:

                short_summary = (
                    short_summary[:72] + "..."
                )

            commit_message = (
                f"{commit_type}: "
                f"{short_summary}"
            )

            detailed_description = {

                "commit_message": commit_message,

                "changed_files": changed_files,

                "summary": change_summary
            }

            return {

                "success": True,

                "commit": detailed_description
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


# global helper 

def generate_commit_message(
    changed_files: List[str],
    change_summary: str,
    commit_type: str = "feat"
) -> Dict:
    """
    Simple commit generator helper.
    """

    return (
        CommitMessageGenerator
        .generate_commit_message(
            changed_files=changed_files,
            change_summary=change_summary,
            commit_type=commit_type
        )
    )