import { useEffect, useState } from "react";
import type { WorkspaceEntry } from "./api";
import { getWorkspaceFile, getWorkspaceTree } from "./api";

interface FileTreeProps {
  root: string;
}

interface DirState {
  loaded: boolean;
  expanded: boolean;
  entries: WorkspaceEntry[];
  error?: string;
}

export function FileTree({ root }: FileTreeProps) {
  const [dirs, setDirs] = useState<Record<string, DirState>>({});
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [fileError, setFileError] = useState<string | null>(null);

  const loadDir = async (path: string) => {
    try {
      const result = await getWorkspaceTree(path, root);
      setDirs((prev) => ({
        ...prev,
        [path]: { loaded: true, expanded: true, entries: result.entries },
      }));
    } catch (err) {
      setDirs((prev) => ({
        ...prev,
        [path]: { loaded: true, expanded: true, entries: [], error: err instanceof Error ? err.message : String(err) },
      }));
    }
  };

  useEffect(() => {
    setDirs({});
    setSelectedFile(null);
    void loadDir("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [root]);

  const toggleDir = (path: string) => {
    const state = dirs[path];
    if (!state) {
      void loadDir(path);
      return;
    }
    setDirs((prev) => ({ ...prev, [path]: { ...state, expanded: !state.expanded } }));
  };

  const openFile = async (path: string) => {
    setSelectedFile(path);
    setFileError(null);
    setFileContent("");
    try {
      const result = await getWorkspaceFile(path, root);
      setFileContent(result.content);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : String(err));
    }
  };

  const renderDir = (path: string, depth: number) => {
    const state = dirs[path];
    if (!state) return null;
    if (state.error) {
      return <div className="tree-error" style={{ paddingLeft: depth * 14 }}>{state.error}</div>;
    }

    return state.entries.map((entry) => (
      <div key={entry.path}>
        <div
          className={`tree-entry ${entry.path === selectedFile ? "tree-entry-selected" : ""}`}
          style={{ paddingLeft: depth * 14 }}
          onClick={() => (entry.is_dir ? toggleDir(entry.path) : void openFile(entry.path))}
        >
          <span className="tree-icon">{entry.is_dir ? (dirs[entry.path]?.expanded ? "▾" : "▸") : "·"}</span>
          <span className="tree-name">{entry.name}</span>
        </div>
        {entry.is_dir && dirs[entry.path]?.expanded && renderDir(entry.path, depth + 1)}
      </div>
    ));
  };

  return (
    <div className="file-tree-panel">
      <div className="file-tree">
        <div className="file-tree-root-label">{root}</div>
        {renderDir("", 0)}
      </div>
      {selectedFile && (
        <div className="file-viewer">
          <div className="file-viewer-header">{selectedFile}</div>
          {fileError ? (
            <div className="tree-error">{fileError}</div>
          ) : (
            <pre className="file-viewer-content">{fileContent}</pre>
          )}
        </div>
      )}
    </div>
  );
}
