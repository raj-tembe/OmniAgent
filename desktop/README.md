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
- **Shell (`src-tauri/`)**: **compiles cleanly and runs** — Round 2
  verification confirmed a real `cargo tauri dev` window opens, the backend
  becomes healthy (using the project venv, not system Python), and a clean
  window-close shuts everything down with no leaked process. A force-quit
  (SIGKILL) still leaked the spawned server as of Round 1; fixed for Linux
  via `PR_SET_PDEATHSIG` (see "Round 2 verification" below) — **not yet
  re-verified after that fix**. The full in-app session walkthrough (run a
  task, see the diff/diagnostics panels populate, approve a permission
  prompt, use the workspace browser) also hasn't been exercised yet — Round
  2 confirmed the app *opens* but didn't have an LLM provider configured to
  run an actual session through it.
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

## Round 1 verification: found and fixed

A real verification pass (`cargo check`, a live `cargo tauri dev` attempt,
a full Python suite run) surfaced five issues:

1. **Bare `python3` resolved to the system interpreter, not the project
   venv** — the backend never started. Fixed via the resolution order
   above.
2. **`repo_root()` used `std::env::current_dir()`**, which `cargo tauri dev`
   does not reliably set to the crate directory. Fixed by using
   `CARGO_MANIFEST_DIR` — a compile-time constant Cargo always sets
   correctly regardless of the runtime working directory.
3. **`npm test` failed with a cryptic error on Node < 22.6** — no
   `engines` constraint existed to catch this earlier. Fixed with the
   `engines` field + `.npmrc`'s `engine-strict=true` described above.
4. **Importing `config` crashed outright on a read-only/inaccessible
   default data directory.** Fixed: directory creation in `config/env.py`
   is now wrapped in try/except (logs a warning, doesn't raise), and
   `tests/conftest.py` points `OMNIAGENT_DATA_DIR` at a fresh temp
   directory for the whole test session automatically.
5. **`rust-analyzer` timed out during LSP verification** — turned out to be
   an unfair test (a lone `.rs` file with no surrounding Cargo project),
   not a code bug on its own — see Round 2 below for what the fair retest
   actually found.

## Round 2 verification: found and fixed

With Round 1's fixes in place, a second pass confirmed the backend now
starts correctly and the app window opens, and found two more real issues:

1. **Force-quit (SIGKILL) leaked the spawned `uvicorn` process.** This is
   expected in one sense — no process can catch or react to a signal that
   kills it, on any OS — but there's a real kernel-level mechanism for
   exactly this case. On Linux, `spawn_server()` now uses
   `PR_SET_PDEATHSIG` (via the `libc` crate, Linux-only dependency) to ask
   the kernel to send the child SIGTERM automatically when this process
   dies for *any* reason, including one it never got a chance to react to.
   **No equivalent exists yet for macOS** (`prctl` has no direct analogue)
   **or Windows** (would need a Job Object configured with
   `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) — those platforms don't get this
   guarantee. A graceful close (window close, Ctrl+C) already worked
   correctly on every platform before this fix, via the existing
   `ExitRequested` handler; this only closes the "couldn't react" gap, and
   only on Linux so far.
2. **`rust-analyzer` returned `[]` for a file with a genuine, obvious type
   error**, even with a real Cargo project and a 90-second budget — not a
   timeout after all, a wrong answer returned quickly (~3 seconds). Root
   cause: `lsp/client.py`'s `_wait_for_diagnostics` returned on the *first*
   `textDocument/publishDiagnostics` notification for the file's URI.
   `rust-analyzer` publishes progressively — an initial (often empty)
   result immediately after the file opens, then a real one once
   background analysis/indexing actually finishes — and the first, empty
   one was winning the race. Fixed with a settle window: after each publish
   for a URI, wait `settle_seconds` (default 1.5s) for a possible
   follow-up before returning the latest one seen, rather than the first.
   Verified two ways: new unit tests proving a later publish supersedes an
   earlier one (and vice versa — an empty follow-up correctly supersedes a
   real earlier result too, since "latest" is the actual rule, not "prefer
   non-empty"), and confirming the existing live `pylsp` tests still pass
   unchanged — `pylsp` only ever publishes once in practice, so this adds
   at most `settle_seconds` of latency for it, not the full timeout.
   TypeScript/Go servers remain completely untested.

## Still needs verification (Round 3)

- Re-run the force-quit leak test now that `PR_SET_PDEATHSIG` is in place —
  Round 2 found the bug but predates this fix.
- Re-run the `rust-analyzer` retest now that the settle-window fix is in
  place — Round 2 found the bug but predates this fix too.
- The full in-app session walkthrough end to end with a configured LLM
  provider: run a task, watch the diff/diagnostics panels populate from a
  real session (not just confirm the window opens), approve a permission
  prompt through the actual dialog, use the workspace browser + redirection
  through the UI.
- Docker-based sandbox execution with Docker actually running — still
  entirely unverified; confirmed only that its absence fails gracefully
  (a normal failed `ExecutionResult`, not a crash).
- Non-Python LSP servers other than `rust-analyzer` (TypeScript, Go).
- No packaging story yet for shipping the Python backend as part of a
  distributable build — `main.rs` still shells out to a `python3`
  (resolved per above), which works for local development but not for
  something you hand to someone else to install. A standalone Python build
  (PyInstaller or similar) is a follow-up task.

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
