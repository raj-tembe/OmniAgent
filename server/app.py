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

from server.sessions import session_manager

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
