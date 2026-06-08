from pathlib import Path
from typing import Optional

from graph.workflow import (
    omniagent_graph
)


# graph visualizer

class GraphVisualizer:
    """
    Workflow visualization utility.

    Responsibilities:
    - visualize LangGraph workflow
    - export Mermaid diagrams
    - save workflow images
    - support debugging/documentation
    """

    def __init__(self):

        self.graph = omniagent_graph


    # get mermaid

    def get_mermaid(self) -> str:
        """
        Returns Mermaid graph definition.
        """

        try:

            return (
                self.graph
                .get_graph()
                .draw_mermaid()
            )

        except Exception as e:

            return (
                f"Failed to generate Mermaid: {e}"
            )


    # save mermaid

    def save_mermaid(
        self,
        filepath: str
    ) -> str:
        """
        Save Mermaid graph to file.
        """

        mermaid = self.get_mermaid()

        Path(filepath).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(mermaid)

        return filepath


    # save png

    def save_png(
        self,
        filepath: str
    ) -> str:
        """
        Save workflow graph as PNG.

        Requires:
        grandalf
        pygraphviz
        OR LangGraph image support
        """

        try:

            png_data = (

                self.graph
                .get_graph()
                .draw_mermaid_png()

            )

            Path(filepath).parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                filepath,
                "wb"
            ) as file:

                file.write(
                    png_data
                )

            return filepath

        except Exception as e:

            raise RuntimeError(
                f"PNG export failed: {e}"
            )


    # display mermaid

    def print_graph(self):
        """
        Print Mermaid workflow.
        """

        print(
            self.get_mermaid()
        )


    # export documentation

    def export_documentation(
        self,
        filepath: str
    ) -> str:
        """
        Export graph documentation.
        """

        mermaid = self.get_mermaid()

        content = f"""
# OMNIAGENT Workflow

```mermaid
{mermaid}
```
"""

        Path(filepath).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(content)

        return filepath


# global visualizer 

graph_visualizer = (
    GraphVisualizer()
)