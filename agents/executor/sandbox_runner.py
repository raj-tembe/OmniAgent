import os
from typing import Dict
from pathlib import Path

from agents.executor.docker_runner import run_in_docker
from schemas.execution_schema import ExecutionResult

GENERATED_PROJECT_DIR = (
    "execution/generated_project"
)

def save_generated_files(
        generated_files: Dict[str, str],
        project_name: str = "current_project"
) -> str:
    """
    Save generated files to sandbox project directory.
    """
    project_path = os.path.join(
        GENERATED_PROJECT_DIR, 
        project_name
        )
    
    os.makedirs(
        project_path, 
        exist_ok=True
        )

    for filename, content in generated_files.items():

        file_path = os.path.join(
            project_path, 
            filename
            )
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return project_path

def execute_generated_project(
        generated_files: Dict[str, str],
        command: str = "python app.py"
) -> ExecutionResult:
    
    """
    Save generated project and execute the project inside a sandbox.
    """
    project_path = save_generated_files(
        generated_files=generated_files
        )
    
    result = run_in_docker(
        project_path=project_path, 
        command=command
        )

    return result