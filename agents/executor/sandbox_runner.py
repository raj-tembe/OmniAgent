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
        command: str = None
) -> ExecutionResult:
    
    """
    Save generated project and execute inside a sandbox.
    Auto-detects web server frameworks and validates them without running the server.
    """
    project_path = save_generated_files(
        generated_files=generated_files,
        project_name=project_name
        )
    
    # Auto-detect web server frameworks
    all_content = " ".join(generated_files.values())
    is_web_server = any(kw in all_content for kw in [
        "app.run(", "uvicorn", "Flask(", "FastAPI(", "django", "tornado"
    ])

    if command is None:
        if is_web_server:
            # For web servers, create and run a validation script
            validation_script = """import ast
import sys
import os

# Validate Python syntax for all .py files
errors = []
for filename in os.listdir('.'):
    if filename.endswith('.py'):
        try:
            with open(filename, 'r') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append(f"{filename}: {e}")

if errors:
    print("Syntax errors found:")
    for err in errors:
        print(f"  {err}")
    sys.exit(1)

# Try to install requirements
os.system("pip install -r requirements.txt -q 2>/dev/null || true")

print("Web application validation passed: all files have valid syntax")
sys.exit(0)
"""
            # Save validation script to project
            validation_path = os.path.join(project_path, "_validate.py")
            with open(validation_path, "w", encoding="utf-8") as f:
                f.write(validation_script)
            
            command = "python _validate.py"
        else:
            command = "python app.py"

    result = run_in_docker(
        project_path=project_path, 
        command=command
        )

    return result