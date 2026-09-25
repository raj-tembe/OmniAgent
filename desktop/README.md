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
- **Shell (`src-tauri/`)**: **compiles, runs, and now genuinely
  packages.** `cargo check` and a real `cargo tauri build` both pass
  (Round 4) — the bundled Python backend is confirmed included inside an
  actual `.deb`/`.rpm` package, not just built and left alongside it. The
  force-quit (SIGKILL) leak from Round 1 is fixed and confirmed fixed
  (Round 2, via `PR_SET_PDEATHSIG` on Linux). With a real LLM provider
  configured for the first time (Round 4), a basic session actually ran
  end to end through the API layer — real generated code, a real diff.
  What's left: the GUI-only parts (clicking through the permission
  dialog, workspace browser, and editor-native action buttons rather than
  hitting their endpoints directly) and installing/running the actual
  built package rather than just confirming the sidecar is inside it —
  see "Round 5" below.
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

**`rust-analyzer` still wasn't done, though** — Round 3's retest (with the
settle-window fix in place) found a *third*, more fundamental bug: it
still returned `[]`, this time because `get_diagnostics` had been sending
the wrong `rootUri` in the `initialize` request all along — the *calling
process's* current working directory, completely unrelated to the file
actually being checked. `pylsp` tolerated this by accident (it was always
being asked to check a file inside the same repo the server itself runs
from); `rust-analyzer` genuinely needs to discover the real project a file
belongs to, and couldn't. Fixed: `_find_workspace_root()` now walks up
from the file's own directory looking for a project marker (`Cargo.toml`,
`pyproject.toml`, `go.mod`, `package.json`, or `.git`), falling back to the
file's parent directory if none is found. Verified with unit tests
covering the exact failure shape (an unrelated cwd shouldn't affect the
result) plus nested-marker and nearest-marker-wins cases, and confirmed
the live `pylsp` tests still pass unchanged.

## Round 3 verification: found and fixed

With Round 2's fixes confirmed working (force-quit leak fixed, `cargo
check` passing), Round 3 tested the new packaging pipeline and re-tested
`rust-analyzer` — and found two real bugs, detailed in "Packaging" below
and the `rust-analyzer` section above respectively. Also confirmed clean
in this round: 228 tests still pass, `cargo check` still passes, the
force-quit fix genuinely works (verified by killing the Tauri binary
directly and confirming the child `uvicorn` process disappears), and the
Round 1/2 venv-Python fallback path still works correctly.

## Round 4 verification: the sidecar wiring actually works

Round 4 was the strongest result yet. `cargo check` passed on the
previously-uncompiled sidecar code with zero changes needed. `cargo tauri
build` completed end to end and produced real `.deb` and `.rpm` bundles —
confirmed the sidecar binary is genuinely included at `/usr/bin/
omniagent-server` inside the `.deb` package, not just staged and forgotten.
And with a real Gemini API key configured for the first time in four
rounds, a real session actually ran: a basic build-mode task produced a
real `file.diff` with genuine generated code, and plan mode correctly
declined to execute. One real bug came out of it, fixed below. GUI-only
parts (the permission dialog's visual appearance, the workspace browser,
editor-native action buttons) still need a human at the keyboard — the API
layer underneath all three was exercised and confirmed correct, but
clicking through the actual UI hasn't happened yet.

**Bug found and fixed**: a session with a permission rule set to `"ask"`
crashed entirely once it reached the critic step, with a bare
`FileNotFoundError: 'pylsp'`. Root cause: `lsp/client.py`'s
`get_diagnostics` spawned the configured language server binary outside
any error handling, so when it isn't installed — always true in the
packaged desktop build, which doesn't bundle any LSP servers themselves —
the raw `FileNotFoundError` propagated straight past
`critic_agent.py`'s existing `except LspError: continue` handling (which
only catches `LspError`, not arbitrary `OSError`s) and crashed the whole
graph node. Fixed: `JsonRpcConnection.spawn()`'s call site now catches
`OSError` (covers both a missing binary and a found-but-not-executable
one) and re-raises it as `LspError`, which every caller already handles
correctly. Verified two ways: new tests reproduce the exact scenario end
to end (a critic_agent run against a file with no LSP server available
completes normally instead of crashing), and — extra rigor — those same
tests were confirmed to *fail* against the pre-fix code with the identical
`FileNotFoundError` from the live report, proving they're real regression
tests and not just testing themselves.

**Known limitation, not a bug**: the packaged desktop build still doesn't
include any LSP servers (`pylsp`, `rust-analyzer`, etc.) — after this fix,
a bundled-build session simply skips static-analysis diagnostics for
languages whose server isn't present, rather than crashing. Bundling
`pylsp` itself (it's a Python program, so in principle a second PyInstaller
build could produce a sidecar for it too, mirroring how the main server
is bundled) is a real follow-up, not attempted in this round.

**Also found, not yet resolved**: TypeScript LSP support
(`typescript-language-server`) didn't respond to `initialize` at all in
Round 4's environment — the process spawned but never answered, timing
out rather than erroring. Possibly a TypeScript 7+/`tsserver` packaging
change upstream rather than a bug in this codebase, but unconfirmed either
way — needs investigation with a controlled, known-working
`typescript-language-server` setup before concluding anything.

## Still needs verification (Round 5)

- The GUI-only parts of the session walkthrough: the permission dialog's
  actual on-screen appearance and click-through (the HTTP layer under it
  is confirmed correct), the workspace browser, and the editor-native
  action buttons. All three need a human clicking through `cargo tauri
  dev`, not an API-level check.
- Installing the `.deb`/`.rpm` Round 4 produced and confirming the
  installed app spawns the bundled sidecar with no Python/`uvicorn`
  visible in `ps aux` at all — Round 4 confirmed the binary is *in* the
  package but didn't install and run it.
- Re-run the packaging build with `torch`/`transformers` actually present
  in the build venv, to confirm `--exclude-module` genuinely keeps them
  out — still not tested with real `torch` present (this environment
  couldn't install it — see "Packaging" below).
- Docker-based sandbox execution with Docker actually running — still
  entirely unverified across four rounds; confirmed only that its absence
  fails gracefully (a normal failed `ExecutionResult`, not a crash). Round
  4 also noted the executor retrying multiple times before reaching
  critic without Docker available — expected behavior (the existing
  retry-then-escalate routing in `planner_agent.py`), not a new bug, but
  worth a clean confirmation once Docker's actually present.
- TypeScript LSP investigation (see above) — needs a verified-working
  `typescript-language-server` setup to determine if this is a real bug
  or an environment/tooling mismatch.
- Non-Python LSP servers other than what Round 2 already confirmed for
  `rust-analyzer` — Go untested.

## Packaging

`scripts/build_desktop_backend.sh` bundles the Python backend into a single
standalone executable via PyInstaller — this is real and verified, not just
written: the built binary was run in an isolated temp directory with
`PYTHONPATH` unset and a stripped-down `PATH`, and correctly served
`GET /health` and `POST /sessions` (creating a real session, proving the
whole import chain — config, permission, bus, the graph — works from a
frozen bundle, not just that the build step succeeded).

```bash
pip install -r requirements-build.txt
./scripts/build_desktop_backend.sh
# produces dist/omniagent-server (or dist/omniagent-server.exe on Windows)
```

`main.rs`'s `spawn_server()` now checks for `dist/omniagent-server` (see
`bundled_server_path()`) before falling back to the venv/system-Python
resolution described above — if the bundle exists, it's used; if not,
nothing changes from before. This means running the build script once,
then `cargo tauri dev`/`cargo tauri build`, no longer requires a Python
environment to be set up on the machine the app actually runs on.

### Round 3 finding: a 2.6GB binary that failed to bind its port at all

Live verification against a machine with a full `pip install -r
requirements.txt` found the bundled binary balloon to 2.6GB and silently
fail to serve `/health` — extracting but never binding the port, no error
output. Root cause, found via the size number itself:
`requirements.txt`'s "optional" LLM provider packages
(`langchain-openai`/`-groq`/`-ollama`/`-huggingface`) and the HuggingFace
utilities (`transformers`, `torch`) were labeled optional in a comment but
**not actually commented out** — a pre-existing bug, now fixed. Every
`pip install -r requirements.txt` was silently installing the full
`transformers`/`torch`/CUDA stack regardless of which provider you
actually use.

Two fixes, in this repo now:
1. `requirements.txt`'s optional provider/ML lines are now genuinely
   commented out — `pip install -r requirements.txt` installs only what's
   universally needed (Gemini by default) unless you explicitly uncomment
   more.
2. `scripts/build_desktop_backend.sh` also now passes `--exclude-module`
   for `torch`, `transformers`, and related packages defensively — even a
   build run from a dev venv that has them installed (for local-inference
   work, say) won't end up bundling them.

**Re-verified in this environment with fix #1 applied (torch/transformers
absent): binary size back to ~120MB, and it correctly served `/health` and
`POST /sessions` in the same isolated, no-`PYTHONPATH` test as before.**
**Not yet re-verified with fix #2's defense specifically**: this
environment couldn't install a real `torch` (PyTorch's own package index
isn't reachable from here, and the full PyPI wheel didn't fit available
disk space) to do an exact before/after match of the original 2.6GB
failure. The size drop and working bundle are confirmed for the "torch was
never installed" case; confirming `--exclude-module` correctly excludes it
even when it *is* present in the build venv is the next thing to verify.

What's still manual/not done:
- Tauri's `externalBin`/sidecar wiring for `cargo tauri build` is now in
  place — `tauri.conf.json` declares `externalBin: ["binaries/omniagent-server"]`,
  `scripts/build_desktop_backend.sh` stages a target-triple-suffixed copy
  at `desktop/src-tauri/binaries/` when `rustc` is available (skips this
  step gracefully otherwise — confirmed by running the script without
  `rustc` present and seeing it still produce a working `dist/omniagent-server`),
  and `spawn_server()` now checks `app.path().resource_dir()` first (the
  real installed-app location) before falling back to the `<repo_root>/dist/`
  check that Round 3 already verified. **None of this new Rust code has
  been compiled or run** — same standing caveat as the rest of `main.rs`,
  no Rust toolchain in the environment it was written in. This is
  genuinely the higher-risk kind of change to leave unverified (new
  `tauri::Manager` API usage, a changed function signature on
  `spawn_server`/`bundled_server_path`), so treat it as a first draft
  needing `cargo check` + an actual `cargo tauri build` before trusting it,
  more than usual.
- No code signing / notarization (macOS) or equivalent, needed for a
  distributable build most users could actually install without a
  security warning.
- The externalBin path has only been reasoned through for `cargo tauri
  build`'s installer bundling — it hasn't been confirmed that `cargo tauri
  dev` also picks up `binaries/` correctly (Tauri's dev-mode sidecar
  resolution may differ from its build-mode one); the `dist/` fallback is
  what Round 3 actually verified for dev mode and remains the reliable
  path there.

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
