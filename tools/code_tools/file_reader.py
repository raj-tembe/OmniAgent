import os
from typing import Dict, List


# file reader tool

class FileReaderTool:
    """
    File reading utility.

    Responsibilities:
    - read project files
    - inspect generated code
    - support debugging/review workflows
    """


    # read file

    @staticmethod
    def read_file(
        filepath: str
    ) -> Dict:
        """
        Read file contents.
        """

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            return {

                "success": True,

                "filepath": filepath,

                "content": content
            }

        except Exception as e:

            return {

                "success": False,

                "filepath": filepath,

                "error": str(e)
            }


    # read multiple files

    @staticmethod
    def read_files(
        filepaths: List[str]
    ) -> Dict:
        """
        Read multiple files.
        """

        results = {}

        for filepath in filepaths:

            results[filepath] = (
                FileReaderTool.read_file(
                    filepath
                )
            )

        return results


    # list directory files

    @staticmethod
    def list_files(
        directory: str
    ) -> Dict:
        """
        List files recursively.
        """

        try:

            all_files = []

            for root, _, files in os.walk(
                directory
            ):

                for file in files:

                    full_path = os.path.join(
                        root,
                        file
                    )

                    all_files.append(full_path)

            return {

                "success": True,

                "files": all_files
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }