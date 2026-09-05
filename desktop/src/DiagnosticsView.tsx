/**
 * Renders LSP diagnostics (from lsp/client.py via critic_agent's
 * lsp.diagnostics bus event) as a list of severity-coded findings, or a
 * clean confirmation when a file was checked and came back with nothing.
 */

interface Diagnostic {
  severity: string;
  message: string;
  line: number;
  column: number;
  source?: string;
}

interface DiagnosticsViewProps {
  filename: string;
  diagnostics: Diagnostic[];
}

export function DiagnosticsView({ filename, diagnostics }: DiagnosticsViewProps) {
  const isClean = diagnostics.length === 0;

  return (
    <div className={`diagnostics-view ${isClean ? "diagnostics-clean" : ""}`}>
      <div className="diagnostics-header">
        <span className="diagnostics-filename">{filename}</span>
        <span className="diagnostics-count">
          {isClean ? "no issues" : `${diagnostics.length} issue${diagnostics.length === 1 ? "" : "s"}`}
        </span>
      </div>
      {!isClean && (
        <ul className="diagnostics-list">
          {diagnostics.map((d, i) => (
            <li key={i} className={`diagnostic-item diagnostic-${d.severity}`}>
              <span className="diagnostic-severity">{d.severity}</span>
              <span className="diagnostic-location">
                {d.line}:{d.column}
              </span>
              <span className="diagnostic-message">{d.message}</span>
              {d.source && <span className="diagnostic-source">{d.source}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
