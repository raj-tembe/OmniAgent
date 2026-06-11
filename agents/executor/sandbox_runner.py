import os
import logging
from typing import Dict
from pathlib import Path

from agents.executor.docker_runner import run_in_docker
from schemas.execution_schema import ExecutionResult
from config import GENERATED_PROJECT_DIR


logger = logging.getLogger(__name__)


def save_generated_files(
        generated_files: Dict[str, str],
        project_name: str = "current_project"
) -> str:
    """
    Save generated files to sandbox project directory.
    """
    project_path = os.path.join(
        str(GENERATED_PROJECT_DIR), 
        project_name
        )
    
    logger.info(f"Creating project directory: {project_path}")
    
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
        
        logger.debug(f"Saved file: {file_path} ({len(content)} bytes)")

    logger.info(f"Project '{project_name}' saved with {len(generated_files)} files")
    
    return project_path

def execute_generated_project(
        generated_files: Dict[str, str],
        project_name: str = "current_project",
        command: str = "python app.py"
) -> ExecutionResult:
    
    """
    Save generated project and execute the project inside a sandbox.
    """
    project_path = save_generated_files(
        generated_files=generated_files,
        project_name=project_name
        )
    
    result = run_in_docker(
        project_path=project_path, 
        command=command
        )

    return result