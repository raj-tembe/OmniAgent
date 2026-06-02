import os
import uuid
from pathlib import Path
from typing import Dict


# sandbox config 

SANDBOX_ROOT = "execution/generated_projects"

os.makedirs(SANDBOX_ROOT, exist_ok=True)


# sandbox manager 

class SandboxManager:
    """
    Sandbox environment manager.

    Responsibilities:
    - create isolated workspaces
    - manage execution directories
    - cleanup temporary projects
    - support autonomous execution
    """

    def __init__(self):

        self.sandbox_root = SANDBOX_ROOT


    # create sandbox

    def create_sandbox(
        self,
        prefix: str = "workflow"
    ) -> Dict:
        """
        Create isolated execution workspace.
        """

        try:

            sandbox_id = (
                f"{prefix}_{uuid.uuid4().hex[:8]}"
            )

            sandbox_path = os.path.join(
                self.sandbox_root,
                sandbox_id
            )

            Path(sandbox_path).mkdir(
                parents=True,
                exist_ok=True
            )

            return {

                "success": True,

                "sandbox_id": sandbox_id,

                "sandbox_path": sandbox_path
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


    # delete sandbox

    def delete_sandbox(
        self,
        sandbox_path: str
    ) -> Dict:
        """
        Remove sandbox workspace.
        """

        try:

            if os.path.exists(
                sandbox_path
            ):

                for root, dirs, files in os.walk(
                    sandbox_path,
                    topdown=False
                ):

                    for file in files:

                        os.remove(
                            os.path.join(
                                root,
                                file
                            )
                        )

                    for directory in dirs:

                        os.rmdir(
                            os.path.join(
                                root,
                                directory
                            )
                        )

                os.rmdir(sandbox_path)

            return {

                "success": True,

                "sandbox_path": sandbox_path
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


    # list sandboxes

    def list_sandboxes(self) -> Dict:
        """
        Retrieve active sandboxes.
        """

        try:

            sandboxes = []

            for item in os.listdir(
                self.sandbox_root
            ):

                full_path = os.path.join(
                    self.sandbox_root,
                    item
                )

                if os.path.isdir(full_path):

                    sandboxes.append(full_path)

            return {

                "success": True,

                "sandboxes": sandboxes
            }

        except Exception as e:

            return {

                "success": False,

                "error": str(e)
            }


# global sandbox manager 

sandbox_manager = SandboxManager()