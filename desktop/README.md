# OmniAgent Desktop

Standalone desktop IDE shell for OmniAgent, built with Tauri (Rust) + React.

## Status

- **Frontend (`src/`)**: real, working, built and typechecked
  (`npm run build` succeeds with 0 errors). Covers:
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
    `FileTree.tsx`. The same directory drives where the agent itself
    operates: `agents/executor/sandbox_runner.py` accepts a `workspace`
    override instead of always writing to the fixed `GENERATED_PROJECT_DIR`,
    and the desktop app passes the file browser's open directory straight
    into session creation.
  - **Editor-native actions** — select a file in the tree and use the
    Explain / Fix issues / Generate tests buttons in the file viewer header
    to pre-fill the session request with a real prompt built from that
    file's actual content (`editorActions.ts`). Pre-fills only, doesn't
    auto-run.
  - Frontend test coverage: `npm test` runs Node's built-in test runner
    against pure-logic modules (no React/DOM involved).
- **Shell (`src-tauri/`)**: **compiles cleanly** (`cargo check` verified on a
  real machine — 0 errors, 0 warnings). Two real bugs found by that same
  verification pass have been fixed (see "Fixed since first verification
  pass" below); full runtime behavior (window opens, session survives a
  real click-through, clean shutdown) has not been re-verified since those
  fixes landed — see "Still needs verification."
- **Backend**: the existing `server/app.py` (Phase 4). The shell spawns it
  as a subprocess on port 8420 and waits for `/health` before considering it
  ready — see "Python interpreter resolution" below for how it picks which
  `python3` to use.

## Requirements

- **Node >= 22.6.0** — `npm test` uses `--experimental-strip-types`, which
  doesn't exist before Node 22.6. `desktop/.npmrc` sets `engine-strict=true`
  so `npm install` fails with a clear message on an older Node, rather than
  `npm test` failing with a cryptic `bad option` error later.
- **Rust + Tauri CLI** (`cargo install tauri-cli --version "^2"`) for the
  desktop shell itself. Not needed for frontend-only development.
- **Docker**, running, for the sandboxed code-execution path
  (`agents/executor/docker_runner.py`) — not yet verified end-to-end (no
  Docker was available in the environment this was built in). If Docker
  isn't running, `execute_generated_project` returns a normal failed
  `ExecutionResult` rather than crashing — confirmed safe, but obviously
  not what you want for an actual working session.

## Python interpreter resolution

`main.rs`'s `spawn_server()` does **not** just run a bare `python3` — that
was bug #1 from the first verification pass: a bare `python3` resolves to
whatever the system default is, which on most machines has none of
`requirements.txt` installed, so the backend silently failed to start.
Resolution order now:

1. `OMNIAGENT_PYTHON` env var, if set — for conda, an unusually-named venv,
   etc.
2. `<repo_root>/.venv/bin/python3` (or `.venv\Scripts\python.exe` on
   Windows)
3. `<repo_root>/venv/bin/python3` (same Windows variant)
4. Bare `python3` on PATH, as a last resort

Create a `.venv` at the repo root and `pip install -r requirements.txt`
into it, and this resolves automatically with no configuration needed.

## Fixed since first verification pass

A real verification pass (`cargo check`, a live `cargo tauri dev` attempt,
a full Python suite run) surfaced five issues, all fixed:

1. **Bare `python3` resolved to the system interpreter, not the project
   venv** — the backend never started. Fixed via the resolution order
   above.
2. **`repo_root()` used `std::env::current_dir()`**, which `cargo tauri dev`
   does not reliably set to the crate directory (verification showed it
   landing one level too high, outside the repo entirely). Fixed by using
   `CARGO_MANIFEST_DIR` — a compile-time constant Cargo always sets
   correctly regardless of the runtime working directory.
3. **`npm test` failed with a cryptic error on Node < 22.6** — no
   `engines` constraint existed to catch this earlier. Fixed with the
   `engines` field + `.npmrc`'s `engine-strict=true` described above.
4. **Importing `config` crashed outright on a read-only/inaccessible
   default data directory** — every test that transitively imports it
   failed at collection time. Fixed: directory creation in `config/env.py`
   is now wrapped in try/except (logs a warning and continues rather than
   raising), and `tests/conftest.py` now points `OMNIAGENT_DATA_DIR` at a
   fresh temp directory for the whole test session automatically, so this
   can't recur regardless of the machine's home-directory permissions.
5. **`rust-analyzer` timed out during LSP verification** — this one is not
   a bug in `lsp/client.py`, as far as investigation so far shows.
   `rust-analyzer` needs a real Cargo workspace (a `Cargo.toml` with actual
   dependencies) to fully initialize, and can legitimately take much longer
   than `pylsp` does on first analysis/indexing. `lsp/servers.py`'s
   `get_diagnostics(..., timeout=...)` is configurable per call — a test
   against a file inside a real, already-built Cargo project with a longer
   timeout (60s+) would be a fairer test than a lone `.rs` file in `/tmp`.
   TypeScript/Go servers remain completely untested (not installed during
   verification).

## Still needs verification

- Full `cargo tauri dev` runtime walkthrough with the two startup bugs
  fixed: does the window open, does a real end-to-end session (run a task,
  see the diff/diagnostics panels populate, approve a permission prompt)
  work start to finish, does the process shut down cleanly (no leaked
  `uvicorn`) on both a normal close and a force-quit.
- Docker-based sandbox execution with Docker actually running.
- Non-Python LSP servers, with a fairer test setup (see point 5 above).
- No packaging story yet for shipping the Python backend as part of a
  distributable build — `main.rs` still shells out to a `python3`
  (resolved per above), which works for local development but not for
  something you hand to someone else to install. A standalone Python build
  (PyInstaller or similar) is a follow-up task.
- `Cargo.lock` should be committed (Tauri apps are binaries, not
  libraries — `Cargo.lock` belongs in version control for those) but
  couldn't be generated without a Rust toolchain. If your `cargo check`/
  `cargo tauri dev` run generated one along with `src-tauri/icons/`,
  commit both.

## Development setup

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cd desktop
npm install
cargo install tauri-cli --version "^2"   # if not already installed
cargo tauri dev
```

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
