import logging
from typing import Dict
from pathlib import Path

from agents.executor.docker_runner import run_in_docker
from schemas.execution_schema import ExecutionResult
from config import GENERATED_PROJECT_DIR


logger = logging.getLogger(__name__)


def _safe_child_path(base_path: Path, relative_path: str) -> Path:
    """
    Resolve a user/model supplied child path and ensure it stays under base_path.
    """
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe generated file path: {relative_path}")

    resolved_base = base_path.resolve()
    resolved_candidate = (resolved_base / candidate).resolve()
    if not resolved_candidate.is_relative_to(resolved_base):
        raise ValueError(f"Generated file escapes project directory: {relative_path}")

    return resolved_candidate


def save_generated_files(
        generated_files: Dict[str, str],
        project_name: str = "current_project"
) -> str:
    """
    Save generated files to sandbox project directory.
    """
    project_path = _safe_child_path(
        Path(GENERATED_PROJECT_DIR),
        project_name or "current_project"
    )
    
    logger.info(f"Creating project directory: {project_path}")
    
    project_path.mkdir(parents=True, exist_ok=True)

    for filename, content in generated_files.items():

        file_path = _safe_child_path(project_path, filename)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.debug(f"Saved file: {file_path} ({len(content)} bytes)")

    logger.info(f"Project '{project_name}' saved with {len(generated_files)} files")
    
    return str(project_path)

def execute_generated_project(
        generated_files: Dict[str, str],
        project_name: str = "current_project",
        command: str = None,
        entry_point: str = "app.py"
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
from pathlib import Path

try:
    from pip._vendor.packaging.requirements import Requirement
except Exception:
    Requirement = None

# Validate Python syntax for all .py files recursively.
errors = []
for path in Path('.').rglob('*.py'):
    if any(part.startswith('.') for part in path.parts):
        continue
    try:
        source = path.read_text(encoding='utf-8')
        ast.parse(source, filename=str(path))
    except SyntaxError as e:
        errors.append(f"{path}: {e}")
    except UnicodeDecodeError as e:
        errors.append(f"{path}: {e}")

requirements = Path('requirements.txt')
if requirements.exists():
    for line_number, line in enumerate(requirements.read_text(encoding='utf-8').splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if Requirement is None:
            continue
        try:
            Requirement(stripped)
        except Exception as e:
            errors.append(f"requirements.txt:{line_number}: invalid requirement {stripped!r}: {e}")

if errors:
    print("Validation errors found:")
    for err in errors:
        print(f"  {err}")
    sys.exit(1)

print("Web application validation passed: all files have valid syntax")
sys.exit(0)
"""
            # Save validation script to project
            validation_path = _safe_child_path(Path(project_path), "_validate.py")
            with open(validation_path, "w", encoding="utf-8") as f:
                f.write(validation_script)
            
            command = "python _validate.py"
        else:
            resolved_entry_point = (entry_point or "app.py").strip() or "app.py"
            command = f"python {resolved_entry_point}"

    result = run_in_docker(
        project_path=project_path, 
        command=command
        )

    return result
