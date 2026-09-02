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
- No permission-request UI yet: the Phase 1 permission engine's "ask" tier
  currently falls back to a terminal `input()` prompt, which doesn't work
  in a GUI app with no attached terminal. A proper in-app approval dialog,
  wired through a new server endpoint, is the next piece needed here.
- No inline diff view, LSP diagnostics display, or editor-native actions
  yet — the current UI is a single session panel with a live event log,
  not a full editor surface.
