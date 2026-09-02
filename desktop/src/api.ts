/**
 * Client for the OmniAgent HTTP server (server/app.py).
 *
 * Assumes the server is running locally — the Tauri shell (src-tauri/)
 * is responsible for spawning it before the window loads. No auth: this
 * talks to a server on localhost that the same desktop app started.
 */

const BASE_URL = "http://127.0.0.1:8420";

export type AgentMode = "build" | "plan";

export interface CreateSessionRequest {
  user_request: string;
  agent_mode?: AgentMode;
  auto_approve?: boolean;
  interactive?: boolean;
}

export interface SessionStatus {
  session_id: string;
  status: "running" | "completed" | "error";
  result: Record<string, unknown> | null;
}

export interface SessionEvent {
  type: string;
  session_id?: string;
  timestamp?: number;
  [key: string]: unknown;
}

export async function createSession(request: CreateSessionRequest): Promise<{ session_id: string }> {
  const response = await fetch(`${BASE_URL}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function getSession(sessionId: string): Promise<SessionStatus> {
  const response = await fetch(`${BASE_URL}/sessions/${sessionId}`);

  if (!response.ok) {
    throw new Error(`Failed to get session: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

/**
 * Subscribe to a session's live event stream. Returns an unsubscribe
 * function. `onEvent` fires for every event including the terminal
 * `stream.closed` marker the server sends when the session finishes —
 * callers can check `event.type === "stream.closed"` to know playback is
 * done rather than guessing from a dropped connection.
 */
export function streamSessionEvents(
  sessionId: string,
  onEvent: (event: SessionEvent) => void,
  onError?: (error: Event) => void,
): () => void {
  const source = new EventSource(`${BASE_URL}/sessions/${sessionId}/events`);

  source.onmessage = (message) => {
    try {
      const parsed = JSON.parse(message.data) as SessionEvent;
      onEvent(parsed);
      if (parsed.type === "stream.closed") {
        source.close();
      }
    } catch {
      // malformed event payload — ignore rather than crash the stream
    }
  };

  if (onError) {
    source.onerror = onError;
  }

  return () => source.close();
}
