// OmniAgent desktop shell.
//
// This process's only real job is lifecycle management for the Python
// backend (server/app.py, built in Phase 4): spawn it when the app starts,
// wait for it to answer /health, then load the frontend — which talks to
// that backend directly over HTTP/SSE (see src/api.ts). This file has no
// business logic of its own; every actual agent capability lives in the
// Python side.
//
// Verified against a real `cargo tauri dev` run (see PR/commit history for
// the verification report) after two real bugs were found and fixed here:
// repo_root() previously derived the repo root from the runtime working
// directory, which `cargo tauri dev` does not reliably set to the crate
// directory — it now uses CARGO_MANIFEST_DIR, a compile-time constant Cargo
// always sets correctly regardless of how the binary is launched. And
// spawn_server() previously always shelled out to a bare `python3`, which
// resolves to the system interpreter (no OmniAgent dependencies installed)
// rather than the project's virtualenv — it now looks for `.venv`/`venv`
// under the repo root first. See python_executable() below.
//
// Packaging note: this still assumes a Python environment (venv or system)
// with requirements.txt already installed is present at the repo root. For
// a distributable build (not just local dev), the Python backend needs to
// be bundled as a standalone executable (e.g. via PyInstaller) rather than
// shelling out to any `python3` at all — that's a separate, larger task not
// solved here.

use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Manager, RunEvent};

struct ServerProcess(Mutex<Option<Child>>);

const SERVER_PORT: u16 = 8420;
const SERVER_HEALTH_URL: &str = "http://127.0.0.1:8420/health";
const HEALTH_CHECK_ATTEMPTS: u32 = 50;
const HEALTH_CHECK_INTERVAL_MS: u64 = 200;

fn repo_root() -> PathBuf {
    // CARGO_MANIFEST_DIR is baked in at compile time as the absolute path to
    // this crate (desktop/src-tauri/) — unlike std::env::current_dir(), it
    // does not depend on where `cargo tauri dev`/the packaged binary happens
    // to be launched from, which verification showed does NOT reliably
    // match the crate directory.
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()   // desktop/src-tauri -> desktop
        .and_then(|p| p.parent())   // desktop -> repo root
        .expect("expected desktop/src-tauri to be two levels under the repo root")
        .to_path_buf()
}

/// Resolve which Python interpreter to launch the server with. Prefers a
/// project virtualenv over the bare `python3` on PATH, since the latter
/// resolves to the system interpreter — which has none of
/// requirements.txt's dependencies installed and makes the desktop app
/// fail silently at startup (confirmed: this was the actual cause of the
/// server never becoming healthy during verification).
///
/// Resolution order:
///   1. `OMNIAGENT_PYTHON` env var, if set — explicit escape hatch for
///      unusual setups (conda, a differently-named venv, etc.)
///   2. `<repo_root>/.venv/bin/python3` (or `Scripts/python.exe` on Windows)
///   3. `<repo_root>/venv/bin/python3` (same Windows variant)
///   4. Bare `python3` on PATH, as a last resort
fn python_executable(root: &Path) -> String {
    if let Ok(explicit) = std::env::var("OMNIAGENT_PYTHON") {
        if !explicit.is_empty() {
            return explicit;
        }
    }

    let candidates = if cfg!(windows) {
        [".venv/Scripts/python.exe", "venv/Scripts/python.exe"]
    } else {
        [".venv/bin/python3", "venv/bin/python3"]
    };

    for candidate in candidates {
        let path = root.join(candidate);
        if path.exists() {
            return path.to_string_lossy().to_string();
        }
    }

    "python3".to_string()
}

/// Path to the bundled standalone server executable, checked in this order:
///   1. `resource_dir` — where Tauri's `externalBin` (see tauri.conf.json)
///      places the sidecar in a properly built/installed app via
///      `cargo tauri build`. `None` during `cargo tauri dev` (no bundle
///      exists yet) or if resolution fails for any reason — falls through
///      to the next check rather than erroring, since dev mode never has
///      a resource dir and that's expected, not a problem.
///   2. `<repo_root>/dist/` — where `scripts/build_desktop_backend.sh`
///      leaves it, for local `cargo tauri dev` testing before wiring up a
///      real `cargo tauri build`. This is the path Round 3 verification
///      actually exercised; the `resource_dir` path above has not been
///      compiled or run yet — see desktop/README.md.
/// Checked before falling back to spawning any `python3` at all — this is
/// what makes a built app not require the end user to have Python or this
/// repo's dependencies installed.
fn bundled_server_path(root: &Path, resource_dir: Option<&Path>) -> Option<PathBuf> {
    let name = if cfg!(windows) { "omniagent-server.exe" } else { "omniagent-server" };

    if let Some(dir) = resource_dir {
        let candidate = dir.join(name);
        if candidate.exists() {
            return Some(candidate);
        }
    }

    let candidate = root.join("dist").join(name);
    candidate.exists().then_some(candidate)
}

fn spawn_server(resource_dir: Option<&Path>) -> std::io::Result<Child> {
    let root = repo_root();

    let mut command = if let Some(bundled) = bundled_server_path(&root, resource_dir) {
        // The bundled binary is a plain executable (see
        // server_entrypoint.py) that takes the port as its one argument —
        // no "-m uvicorn ..." invocation needed, unlike the dev-mode path.
        let mut cmd = Command::new(bundled);
        cmd.arg(SERVER_PORT.to_string());
        cmd
    } else {
        let python = python_executable(&root);
        let mut cmd = Command::new(python);
        cmd.args([
            "-m",
            "uvicorn",
            "server.app:app",
            "--port",
            &SERVER_PORT.to_string(),
            "--log-level",
            "warning",
        ]);
        cmd
    };

    command
        .current_dir(&root)
        .stdout(Stdio::null())
        .stderr(Stdio::inherit());

    // On Linux, ask the kernel to send the child SIGTERM automatically if
    // this process (its parent) dies for any reason — including a SIGKILL
    // this process itself has no way to react to, since no process can
    // catch or handle a signal that kills it. Verified against a real
    // force-quit: without this, the spawned uvicorn process was reparented
    // to PID 1 and kept running indefinitely (Round 2 verification, bug #1).
    //
    // No equivalent exists on macOS (prctl/PR_SET_PDEATHSIG is Linux-only)
    // or Windows (would need a Job Object configured with
    // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE) — those platforms don't get this
    // guarantee yet. A graceful close (window close, Ctrl+C) is already
    // handled on every platform via the ExitRequested handler in main()
    // below; this only covers the "can't react, wasn't given the chance"
    // case, and only on Linux for now.
    #[cfg(target_os = "linux")]
    {
        use std::os::unix::process::CommandExt;
        unsafe {
            command.pre_exec(|| {
                if libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGTERM) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                Ok(())
            });
        }
    }

    command.spawn()
}

fn wait_for_server_health() -> bool {
    for _ in 0..HEALTH_CHECK_ATTEMPTS {
        if let Ok(response) = ureq_get(SERVER_HEALTH_URL) {
            if response {
                return true;
            }
        }
        std::thread::sleep(Duration::from_millis(HEALTH_CHECK_INTERVAL_MS));
    }
    false
}

// Minimal blocking HTTP GET without pulling in a full HTTP client
// dependency just for a health check — swap for `ureq` or `reqwest` if this
// shell grows more HTTP needs later.
fn ureq_get(url: &str) -> std::io::Result<bool> {
    use std::io::{Read, Write};
    use std::net::TcpStream;

    let addr = url
        .trim_start_matches("http://")
        .split('/')
        .next()
        .unwrap_or("127.0.0.1:8420");

    let mut stream = TcpStream::connect(addr)?;
    stream.set_read_timeout(Some(Duration::from_millis(300)))?;
    let request = format!(
        "GET /health HTTP/1.1\r\nHost: {addr}\r\nConnection: close\r\n\r\n"
    );
    stream.write_all(request.as_bytes())?;

    let mut response = String::new();
    stream.read_to_string(&mut response).ok(); // timeout is fine, just check what we got
    Ok(response.starts_with("HTTP/1.1 200"))
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // `.ok()`: resource_dir() returns an error whenever there's no
            // real app bundle to resolve one from — always true under
            // `cargo tauri dev`, and that's expected, not a failure.
            // bundled_server_path() falls through to the dist/ check below
            // it when this is None.
            let resource_dir = app.path().resource_dir().ok();
            let child = spawn_server(resource_dir.as_deref())
                .expect("failed to spawn the OmniAgent server process");
            app.manage(ServerProcess(Mutex::new(Some(child))));

            if !wait_for_server_health() {
                eprintln!(
                    "warning: OmniAgent server did not report healthy within the startup window; \
                     the app window will still open, but requests to it may fail until it's ready."
                );
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building the OmniAgent desktop app")
        .run(|app_handle, event| {
            // Make sure the Python server doesn't outlive the window —
            // otherwise every app restart during development leaks another
            // uvicorn process bound to the same port.
            if let RunEvent::ExitRequested { .. } = event {
                if let Some(state) = app_handle.try_state::<ServerProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        });
}
