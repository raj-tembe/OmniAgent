from graph.workflow import (
    omniagent_graph
)


def run_invoke():
    response = omniagent_graph.invoke(
        {
            "user_request":
            "Build HTML js todo page in one file in new directory"
        }
    )
    print(response)


if __name__ == "__main__":
    run_invoke()
