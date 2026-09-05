# OmniAgent Desktop

Standalone desktop IDE shell for OmniAgent, built with Tauri (Rust) + React.

## Status

- **Frontend (`src/`)**: real, working, built and typechecked in this
  environment (`npm run build` succeeds with 0 errors). A session panel that
  starts a run against the Phase 4 HTTP server and streams its events live
  via Server-Sent Events.
- **Shell (`src-tauri/`)**: written, **not compiled or run** — this was
  built in an environment with no Rust toolchain available. Treat
  `src-tauri/src/main.rs` as a first draft to build against, not a verified
  artifact. It needs `cargo tauri dev` on a machine with Rust + the Tauri
  CLI installed before it's known to actually work.
- **Backend**: the existing `server/app.py` (Phase 4), unmodified. The
  desktop shell spawns it as a subprocess on port 8420 and waits for
  `/health` before considering it ready.

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
```

In this mode you'll need the Python server running separately
(`uvicorn server.app:app --port 8420` from the repo root) for the app to
have anything to talk to.

## Known gaps

- No packaging story yet for shipping the Python backend as part of a
  distributable build — `main.rs` currently shells out to a system
  `python3`, which only works for local development. A standalone Python
  build (PyInstaller or similar) is a follow-up task.
- Permission-request UI is now wired end to end: the server exposes
  `POST /sessions/{id}/permission-response`, `permission/engine.py` gained
  a `resolver` seam that blocks on it instead of a terminal prompt when
  `server_mode=True`, and the desktop app shows an Allow/Deny dialog for
  any `permission.requested` event and posts the answer back. Not yet
  wired into `mcp_client/registry.py`'s tool calls (only
  `executor_agent.py` constructs a server-aware PermissionEngine so far).
- Inline diff view is now wired end to end: coder_agent.py computes a
  real unified diff (agents/diffing.py, Python's difflib) between the
  previous and new generated_files on every coding step, publishes a
  file.diff bus event per changed file, and the desktop app renders it
  with DiffView.tsx instead of the generic event log line.
- LSP diagnostics are now surfaced in the UI too: critic_agent.py
  publishes an lsp.diagnostics event per checked file (including clean
  ones, so "checked, no issues" is distinguishable from "not checked"),
  rendered by DiagnosticsView.tsx.
- No editor-native actions or workspace scoping yet — those are the
  remaining editor-surface gaps.
