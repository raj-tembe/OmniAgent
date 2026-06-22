import os
from pathlib import Path
from typing import Dict, List

from config import GENERATED_PROJECT_DIR, PROJECT_ROOT


# file reader tool

DENIED_FILENAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}


def _resolve_allowed_path(path: str) -> Path:
    target = Path(path).expanduser().resolve()
    allowed_roots = [
        Path(PROJECT_ROOT).resolve(),
        Path(GENERATED_PROJECT_DIR).resolve(),
    ]

    if not any(target == root or target.is_relative_to(root) for root in allowed_roots):
        raise ValueError(f"Refusing to read outside allowed roots: {path}")

    if target.name in DENIED_FILENAMES:
        raise ValueError(f"Refusing to read sensitive file: {path}")

    return target


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
            safe_path = _resolve_allowed_path(filepath)

            with open(
                safe_path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            return {

                "success": True,

                "filepath": str(safe_path),

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
            safe_directory = _resolve_allowed_path(directory)

            all_files = []

            for root, dirs, files in os.walk(
                safe_directory
            ):
                dirs[:] = [directory for directory in dirs if not directory.startswith(".")]

                for file in files:

                    full_path = os.path.join(
                        root,
                        file
                    )

                    if Path(full_path).name not in DENIED_FILENAMES:
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
