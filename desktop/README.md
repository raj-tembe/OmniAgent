# OmniAgent Desktop

Standalone desktop IDE shell for OmniAgent, built with Tauri (Rust) + React.

## Status

- **Frontend (`src/`)**: real, working, built and typechecked in this
  environment (`npm run build` succeeds with 0 errors). Covers:
  - A session panel — describe a task, pick build/plan mode, run it, watch
    the event stream render live via Server-Sent Events.
  - **Permission-approval UI** — the server exposes
    `POST /sessions/{id}/permission-response`; `permission/engine.py`'s
    `resolver` seam (centralized in `permission/factory.py`) blocks on it
    instead of a terminal prompt whenever `server_mode=True`. Wired into
    both `executor_agent.py` and `mcp_client/registry.py`, so an MCP tool
    call gets the same Allow/Deny dialog as a built-in one — the gate is
    mandatory for MCP calls now, not opt-in.
  - **Inline diff view** — `agents/diffing.py` computes a real unified diff
    (Python's `difflib`) between the previous and new `generated_files` on
    every coding step; `coder_agent.py` publishes a `file.diff` event per
    changed file, rendered by `DiffView.tsx`.
  - **LSP diagnostics** — `critic_agent.py` publishes an `lsp.diagnostics`
    event per checked file (including clean ones, so "checked, no issues"
    reads differently from "not checked"), rendered by
    `DiagnosticsView.tsx`.
  - **Workspace browser + agent redirection** — point the app at any local
    directory via the input field above the session panel; browse/view its
    files through `server/workspace.py`'s path-traversal-safe
    `GET /workspace/tree` / `GET /workspace/file`, rendered by
    `FileTree.tsx`. The same directory now also drives where the agent
    itself operates: `agents/executor/sandbox_runner.py` accepts a
    `workspace` override (threaded through `graph/state.py`, `main.py`,
    and both server endpoints) instead of always writing to the fixed
    `GENERATED_PROJECT_DIR`, and the desktop app passes the file browser's
    open directory straight into session creation — open a project, then
    run a session against that same real project.
  - **Editor-native actions** — select a file in the tree and use the
    Explain / Fix issues / Generate tests buttons in the file viewer header
    to pre-fill the session request with a real prompt built from that
    file's actual content (`editorActions.ts`). Pre-fills only, doesn't
    auto-run, so you can review or edit before starting a session.
  - Frontend test coverage: `npm test` runs Node's built-in test runner
    against pure-logic modules (no React/DOM involved) — this is what
    caught a real off-by-one blank-line bug in prompt composition for
    empty files before it shipped.
- **Shell (`src-tauri/`)**: written, **not compiled or run** — built in an
  environment with no Rust toolchain available. Treat
  `src-tauri/src/main.rs` as a first draft to build against, not a verified
  artifact. Needs `cargo tauri dev` on a machine with Rust + the Tauri CLI
  installed before it's known to actually work.
- **Backend**: the existing `server/app.py` (Phase 4), unmodified by the
  desktop work itself. The shell spawns it as a subprocess on port 8420
  and waits for `/health` before considering it ready.

## Remaining gaps

- No packaging story yet for shipping the Python backend as part of a
  distributable build — `main.rs` currently shells out to a system
  `python3`, which only works for local development. A standalone Python
  build (PyInstaller or similar) is a follow-up task.

## Development setup (once you have Rust + Tauri CLI installed)

From the repo root:

```bash
pip install -r requirements.txt        # Python backend deps
cd desktop
npm install                            # frontend deps
cargo install tauri-cli --version "^2" # if not already installed
cargo tauri dev
```

`cargo tauri dev` runs the Vite dev server (frontend) and opens the Tauri
window, which in turn spawns `python3 -m uvicorn server.app:app --port 8420`
from the repo root — see `src-tauri/src/main.rs`'s `spawn_server()`.

## Frontend-only development (no Rust needed)

The React app can be developed and typechecked independently of Tauri —
useful for iterating on the UI without a Rust toolchain:

```bash
cd desktop
npm install
npm run dev     # opens in a regular browser tab
npm run build   # production build + typecheck
npm test        # pure-logic behavioral tests (Node's built-in test runner)
```

In this mode you'll need the Python server running separately
(`uvicorn server.app:app --port 8420` from the repo root) for the app to
have anything to talk to.
