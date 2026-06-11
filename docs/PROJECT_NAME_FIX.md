# Project Name Tracking Fix

## Problem
When the coder_agent created a new project, the directory was always named "current_project" instead of using the actual project name from the user request.

## Root Cause
The `project_name` was not:
1. Extracted from user requests
2. Tracked through the workflow state
3. Passed to the `execute_generated_project()` function
4. Used when saving project files

## Solution Implemented

### 1. **Added `project_name` field to AgentState** (`graph/state.py`)
   - Added `project_name: str = ""` in the CODE GENERATION section
   - Allows tracking project name through entire workflow

### 2. **Added `project_name` to CoderOutput schema** (`schemas/coder_schema.py`)
   - Added `project_name: str = Field(default="current_project", ...)`
   - Enables LLM to optionally specify project name in structured output

### 3. **Created project name extraction function** (`agents/coder/coder_agent.py`)
   ```python
   def _extract_project_name(user_request: str) -> str
   ```
   - Extracts project name from quoted strings: `"'name'"` or `'"name"'`
   - Removes file extensions: `"calculator.html"` → `"calculator"`
   - Sanitizes names (removes spaces, special characters)
   - Falls back to first 2 words of request if no quotes found
   - Examples:
     - `"create 'calculator.html'"` → `"calculator"`
     - `"build a project named 'my_api'"` → `"my_api"`
     - `"create 'todo_app' with React"` → `"todo_app"`

### 4. **Updated coder_agent** (`agents/coder/coder_agent.py`)
   - Extracts project_name at start of agent execution
   - Returns `project_name` in state update along with generated files
   - Preserves project_name across retries

### 5. **Updated executor_agent** (`agents/executor/executor_agent.py`)
   - Extracts `project_name` from state
   - Passes `project_name` to `execute_generated_project()`
   - Preserves `project_name` in all return paths

### 6. **Updated execute_generated_project()** (`agents/executor/sandbox_runner.py`)
   - Added `project_name: str = "current_project"` parameter
   - Passes `project_name` to `save_generated_files()`
   - Uses actual project name when creating directories

## File Structure Example
Before fix:
```
execution/generated_project/
└── current_project/
    ├── index.html
    ├── style.css
    └── script.js
```

After fix with user request: `"create simple calculator page 'calculator.html'"`
```
execution/generated_project/
└── calculator/
    ├── calculator.html
    ├── style.css
    └── script.js
```

## Files Modified
1. `graph/state.py` - Added project_name field
2. `schemas/coder_schema.py` - Added project_name to CoderOutput
3. `agents/coder/coder_agent.py` - Added extraction logic and return field
4. `agents/executor/executor_agent.py` - Added project_name extraction and passing
5. `agents/executor/sandbox_runner.py` - Updated function signature

## Testing
✅ All integration tests pass:
- AgentState stores project_name
- Project name extraction works correctly
- Functions accept project_name parameter
- Workflow chain maintains project_name through all agents

## Usage
The project name is now automatically extracted and used:
```bash
python main.py "create simple calculator page 'calculator.html' app using html, css & js."
# Creates: execution/generated_project/calculator/
```

Users can also influence project naming through:
- Quoted filenames: `"create 'myapp.py'"` → `myapp`
- Explicit naming: `"build project 'my_api'"` → `my_api`
- Default fallback: `"generate a REST API"` → `generate_a`
