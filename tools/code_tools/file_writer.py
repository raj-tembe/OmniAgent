import logging
from pathlib import Path
from typing import Dict

from config import GENERATED_PROJECT_DIR, PROJECT_ROOT


# file writer tool

logger = logging.getLogger(__name__)


def _resolve_allowed_path(filepath: str) -> Path:
    target = Path(filepath).expanduser().resolve()
    allowed_roots = [
        Path(PROJECT_ROOT).resolve(),
        Path(GENERATED_PROJECT_DIR).resolve(),
    ]

    if not any(target == root or target.is_relative_to(root) for root in allowed_roots):
        raise ValueError(f"Refusing to write outside allowed roots: {filepath}")

    return target


class FileWriterTool:
    """
    File writing utility.

    Responsibilities:
    - create files
    - update files
    - create directories
    - support generated projects
    """


    # write file

    @staticmethod
    def write_file(
        filepath: str,
        content: str
    ) -> Dict:
        """
        Write content to file.
        """

        try:
            safe_path = _resolve_allowed_path(filepath)

            safe_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                safe_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(content)

            logger.info(f"File written: {filepath} ({len(content)} bytes)")

            return {

                "success": True,

                "filepath": str(safe_path)
            }

        except Exception as e:
            logger.error(f"Failed to write file {filepath}: {e}", exc_info=True)

            return {

                "success": False,

                "filepath": filepath,

                "error": str(e)
            }


    # write multiple files

    @staticmethod
    def write_files(
        files: Dict[str, str]
    ) -> Dict:
        """
        Write multiple files.
        """

        results = {}

        for filepath, content in files.items():

            results[filepath] = (
                FileWriterTool.write_file(
                    filepath=filepath,
                    content=content
                )
            )

        return results
