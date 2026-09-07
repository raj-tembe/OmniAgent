"""
HTTP server for OmniAgent.

This is the API surface the desktop IDE (and, later, any other client —
CLI, a future web UI) talks to instead of embedding the LangGraph directly.
Three endpoints: start a session, check its status, and stream its events
live as they happen.

Run with: uvicorn server.app:app --reload
"""
import asyncio
import json
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.permission_bridge import pending_permissions
from server.sessions import session_manager
from server.workspace import WorkspaceError, list_directory, read_file

app = FastAPI(title="OmniAgent Server", version="0.1.0")


class CreateSessionRequest(BaseModel):
    user_request: str = Field(..., description="The task to run.")
    agent_mode: str = Field(default="build", description="'build' or 'plan'.")
    auto_approve: bool = Field(default=False, description="Auto-approve 'ask' permission rules.")
    interactive: bool = Field(default=False, description="Enable human-approval nodes.")


class CreateSessionResponse(BaseModel):
    session_id: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    result: Optional[dict] = None


class PermissionResponseRequest(BaseModel):
    request_id: str = Field(..., description="The request_id from the permission.requested event being answered.")
    approved: bool = Field(..., description="True to allow the tool call, False to deny it.")


class WorkspaceEntry(BaseModel):
    name: str
    path: str
    is_dir: bool


class WorkspaceTreeResponse(BaseModel):
    root: str
    path: str
    entries: list[WorkspaceEntry]


class WorkspaceFileResponse(BaseModel):
    root: str
    path: str
    content: str


def _default_workspace_root() -> str:
    from config import GENERATED_PROJECT_DIR
    return GENERATED_PROJECT_DIR


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    session_id = session_manager.create_session(
        user_request=request.user_request,
        agent_mode=request.agent_mode,
        auto_approve=request.auto_approve,
        interactive=request.interactive,
    )
    return CreateSessionResponse(session_id=session_id)


@app.get("/sessions/{session_id}", response_model=SessionStatusResponse)
def get_session(session_id: str) -> SessionStatusResponse:
    record = session_manager.get_session(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'.")

    return SessionStatusResponse(session_id=session_id, status=record.status, result=record.result)


@app.post("/sessions/{session_id}/permission-response")
def respond_to_permission(session_id: str, request: PermissionResponseRequest) -> dict:
    """
    Answer a pending "ask" permission request (see permission/engine.py's
    `resolver` seam and server/permission_bridge.py). `session_id` is only
    used to give a clear 404 for an unknown session — the actual match is
    by `request_id`, since that's what `pending_permissions` tracks.
    """
    if session_manager.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'.")

    resolved = pending_permissions.resolve(request.request_id, request.approved)
    if not resolved:
        raise HTTPException(
            status_code=404,
            detail=f"No pending permission request '{request.request_id}' (already resolved, timed out, or unknown).",
        )

    return {"resolved": True}


@app.get("/workspace/tree", response_model=WorkspaceTreeResponse)
def get_workspace_tree(root: Optional[str] = None, path: str = "") -> WorkspaceTreeResponse:
    """
    List the contents of a directory within a workspace. `root` defaults to
    GENERATED_PROJECT_DIR — the desktop app can override it to browse any
    directory the user points it at, since this server only ever runs
    locally for the single user who started it (see server/workspace.py's
    module docstring for why that's an acceptable trust boundary here).
    """
    from pathlib import Path

    workspace_root = Path(root or _default_workspace_root())

    try:
        entries = list_directory(workspace_root, relative=path)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return WorkspaceTreeResponse(root=str(workspace_root), path=path, entries=entries)


@app.get("/workspace/file", response_model=WorkspaceFileResponse)
def get_workspace_file(path: str, root: Optional[str] = None) -> WorkspaceFileResponse:
    """Read one file's content from within a workspace. Same root default/override as /workspace/tree."""
    from pathlib import Path

    workspace_root = Path(root or _default_workspace_root())

    try:
        content = read_file(workspace_root, path)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IsADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return WorkspaceFileResponse(root=str(workspace_root), path=path, content=content)


@app.get("/sessions/{session_id}/events")
async def stream_session_events(session_id: str):
    record = session_manager.get_session(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'.")

    async def event_stream():
        offset = 0
        while True:
            new_events = record.events_from(offset)
            for event in new_events:
                yield f"data: {json.dumps(event)}\n\n"
            offset += len(new_events)

            if record.status != "running" and offset >= len(record.events):
                yield f"data: {json.dumps({'type': 'stream.closed', 'status': record.status})}\n\n"
                return

            await asyncio.sleep(0.1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
