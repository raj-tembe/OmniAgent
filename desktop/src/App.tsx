import { useCallback, useRef, useState } from "react";
import type { AgentMode, SessionEvent } from "./api";
import { createSession, streamSessionEvents } from "./api";
import "./App.css";

type RunStatus = "idle" | "running" | "completed" | "error";

function App() {
  const [userRequest, setUserRequest] = useState("");
  const [agentMode, setAgentMode] = useState<AgentMode>("build");
  const [autoApprove, setAutoApprove] = useState(false);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const startSession = useCallback(async () => {
    if (!userRequest.trim() || status === "running") return;

    setStatus("running");
    setEvents([]);
    setErrorMessage(null);
    unsubscribeRef.current?.();

    try {
      const { session_id } = await createSession({
        user_request: userRequest,
        agent_mode: agentMode,
        auto_approve: autoApprove,
      });

      unsubscribeRef.current = streamSessionEvents(
        session_id,
        (event) => {
          setEvents((prev) => [...prev, event]);
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

      <section className="event-log" aria-live="polite">
        {events.length === 0 && status === "idle" && (
          <p className="empty-state">Session events will appear here as OmniAgent works.</p>
        )}
        {events
          .filter((e) => e.type !== "stream.closed")
          .map((event, i) => (
            <div key={i} className={`event event-${event.type.replace(/\./g, "-")}`}>
              <span className="event-type">{event.type}</span>
              <span className="event-detail">{formatEvent(event)}</span>
            </div>
          ))}
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
