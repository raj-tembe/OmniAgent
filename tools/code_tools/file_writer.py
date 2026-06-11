import os
import logging
from pathlib import Path
from typing import Dict


# file writer tool

logger = logging.getLogger(__name__)


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

            Path(filepath).parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                filepath,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(content)

            logger.info(f"File written: {filepath} ({len(content)} bytes)")

            return {

                "success": True,

                "filepath": filepath
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