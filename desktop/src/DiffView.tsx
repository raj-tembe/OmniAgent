/**
 * Renders unified diff text (the exact format Python's difflib.unified_diff
 * produces, and the same shape `git diff` uses) as colored +/- lines.
 * No external diff library — the format is simple enough to parse directly
 * and this keeps the desktop app's dependency footprint small.
 */

interface DiffViewProps {
  filename: string;
  changeType: "added" | "modified" | string;
  diff: string;
}

type DiffLineKind = "add" | "remove" | "context" | "hunk" | "header";

interface ParsedLine {
  kind: DiffLineKind;
  text: string;
}

function parseDiff(diff: string): ParsedLine[] {
  return diff.split("\n").filter((line) => line.length > 0).map((line): ParsedLine => {
    if (line.startsWith("+++") || line.startsWith("---")) return { kind: "header", text: line };
    if (line.startsWith("@@")) return { kind: "hunk", text: line };
    if (line.startsWith("+")) return { kind: "add", text: line };
    if (line.startsWith("-")) return { kind: "remove", text: line };
    return { kind: "context", text: line };
  });
}

export function DiffView({ filename, changeType, diff }: DiffViewProps) {
  const lines = parseDiff(diff);

  return (
    <div className="diff-view">
      <div className="diff-view-header">
        <span className={`diff-badge diff-badge-${changeType}`}>{changeType}</span>
        <span className="diff-filename">{filename}</span>
      </div>
      <pre className="diff-body">
        {lines.map((line, i) => (
          <div key={i} className={`diff-line diff-line-${line.kind}`}>
            {line.text}
          </div>
        ))}
      </pre>
    </div>
  );
}
