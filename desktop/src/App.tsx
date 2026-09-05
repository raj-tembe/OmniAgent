import { useCallback, useRef, useState } from "react";
import type { AgentMode, SessionEvent } from "./api";
import { createSession, respondToPermission, streamSessionEvents } from "./api";
import { DiffView } from "./DiffView";
import { DiagnosticsView } from "./DiagnosticsView";
import "./App.css";

type RunStatus = "idle" | "running" | "completed" | "error";

interface PendingPermission {
  requestId: string;
  tool: string;
  agent: string;
  reason?: string;
}

function App() {
  const [userRequest, setUserRequest] = useState("");
  const [agentMode, setAgentMode] = useState<AgentMode>("build");
  const [autoApprove, setAutoApprove] = useState(false);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pendingPermissions, setPendingPermissions] = useState<PendingPermission[]>([]);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const resolvedRequestIdsRef = useRef<Set<string>>(new Set());

  const startSession = useCallback(async () => {
    if (!userRequest.trim() || status === "running") return;

    setStatus("running");
    setEvents([]);
    setErrorMessage(null);
    setPendingPermissions([]);
    resolvedRequestIdsRef.current = new Set();
    unsubscribeRef.current?.();

    try {
      const { session_id } = await createSession({
        user_request: userRequest,
        agent_mode: agentMode,
        auto_approve: autoApprove,
      });
      sessionIdRef.current = session_id;

      unsubscribeRef.current = streamSessionEvents(
        session_id,
        (event) => {
          setEvents((prev) => [...prev, event]);

          if (event.type === "permission.requested" && typeof event.request_id === "string") {
            const requestId = event.request_id;
            // auto-approved requests publish requested+resolved back to
            // back — skip showing a dialog for one that's already settled
            if (!resolvedRequestIdsRef.current.has(requestId)) {
              setPendingPermissions((prev) => [
                ...prev,
                {
                  requestId,
                  tool: String(event.tool ?? "unknown"),
                  agent: String(event.agent ?? "unknown"),
                  reason: typeof event.reason === "string" ? event.reason : undefined,
                },
              ]);
            }
          }

          if (event.type === "permission.resolved" && typeof event.request_id === "string") {
            const requestId = event.request_id;
            resolvedRequestIdsRef.current.add(requestId);
            setPendingPermissions((prev) => prev.filter((p) => p.requestId !== requestId));
          }

          if (event.type === "stream.closed") {
            setStatus(event.status === "error" ? "error" : "completed");
          }
        },
        () => {
          setStatus("error");
          setErrorMessage("Lost connection to the OmniAgent server.");
        },
      );
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  }, [userRequest, agentMode, autoApprove, status]);

  const answerPermission = useCallback(async (requestId: string, approved: boolean) => {
    const sessionId = sessionIdRef.current;
    if (!sessionId) return;

    // remove immediately (optimistic) — the server's own permission.resolved
    // event will also arrive and is a no-op against an already-removed entry
    setPendingPermissions((prev) => prev.filter((p) => p.requestId !== requestId));

    try {
      await respondToPermission(sessionId, requestId, approved);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>OmniAgent</h1>
        <p className="subtitle">Autonomous coding agent — desktop</p>
      </header>

      <section className="request-panel">
        <textarea
          className="request-input"
          placeholder="Describe what you want OmniAgent to build or fix..."
          value={userRequest}
          onChange={(e) => setUserRequest(e.target.value)}
          disabled={status === "running"}
          rows={4}
        />

        <div className="controls">
          <label className="mode-toggle">
            <span>Mode</span>
            <select
              value={agentMode}
              onChange={(e) => setAgentMode(e.target.value as AgentMode)}
              disabled={status === "running"}
            >
              <option value="build">Build (full access)</option>
              <option value="plan">Plan (read-only)</option>
            </select>
          </label>

          <label className="auto-approve-toggle">
            <input
              type="checkbox"
              checked={autoApprove}
              onChange={(e) => setAutoApprove(e.target.checked)}
              disabled={status === "running"}
            />
            <span>Auto-approve</span>
          </label>

          <button
            className="run-button"
            onClick={startSession}
            disabled={status === "running" || !userRequest.trim()}
          >
            {status === "running" ? "Running..." : "Run"}
          </button>
        </div>
      </section>

      {errorMessage && <div className="error-banner">{errorMessage}</div>}

      {pendingPermissions.map((p) => (
        <div key={p.requestId} className="permission-dialog">
          <div className="permission-text">
            <strong>{p.agent}</strong> wants to use <code>{p.tool}</code>
            {p.reason && <div className="permission-reason">{p.reason}</div>}
          </div>
          <div className="permission-actions">
            <button className="deny-button" onClick={() => answerPermission(p.requestId, false)}>
              Deny
            </button>
            <button className="allow-button" onClick={() => answerPermission(p.requestId, true)}>
              Allow
            </button>
          </div>
        </div>
      ))}

      <section className="event-log" aria-live="polite">
        {events.length === 0 && status === "idle" && (
          <p className="empty-state">Session events will appear here as OmniAgent works.</p>
        )}
        {events
          .filter((e) => e.type !== "stream.closed")
          .map((event, i) => {
            if (event.type === "file.diff") {
              return (
                <DiffView
                  key={i}
                  filename={String(event.filename ?? "unknown file")}
                  changeType={String(event.change_type ?? "modified")}
                  diff={String(event.diff ?? "")}
                />
              );
            }
            if (event.type === "lsp.diagnostics") {
              return (
                <DiagnosticsView
                  key={i}
                  filename={String(event.filename ?? "unknown file")}
                  diagnostics={Array.isArray(event.diagnostics) ? event.diagnostics : []}
                />
              );
            }
            return (
              <div key={i} className={`event event-${event.type.replace(/\./g, "-")}`}>
                <span className="event-type">{event.type}</span>
                <span className="event-detail">{formatEvent(event)}</span>
              </div>
            );
          })}
        {status === "completed" && <div className="event event-done">Session complete.</div>}
      </section>
    </div>
  );
}

function formatEvent(event: SessionEvent): string {
  if (typeof event.agent === "string") return String(event.agent);
  if (typeof event.tool === "string") return String(event.tool);
  if (typeof event.user_request === "string") return String(event.user_request);
  return "";
}

export default App;
