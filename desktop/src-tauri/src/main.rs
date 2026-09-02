// OmniAgent desktop shell.
//
// This process's only real job is lifecycle management for the Python
// backend (server/app.py, built in Phase 4): spawn it when the app starts,
// wait for it to answer /health, then load the frontend — which talks to
// that backend directly over HTTP/SSE (see src/api.ts). This file has no
// business logic of its own; every actual agent capability lives in the
// Python side.
//
// NOT compiled or tested in the environment this was written in — there is
// no Rust toolchain available there. This needs `cargo tauri dev` /
// `cargo tauri build` on a machine that has Rust + the Tauri CLI installed
// before it's known to work. Treat it as a first draft to build against,
// not a verified artifact.
//
// Packaging note: this spawns `python3` and assumes the OmniAgent Python
// environment (requirements.txt) is already set up in the parent directory.
// For a distributable build (not just local dev), the Python backend needs
// to be bundled as a standalone executable (e.g. via PyInstaller) rather
// than shelling out to a system `python3` — that's a follow-up task, not
// solved here.

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Manager, RunEvent};

struct ServerProcess(Mutex<Option<Child>>);

const SERVER_PORT: u16 = 8420;
const SERVER_HEALTH_URL: &str = "http://127.0.0.1:8420/health";
const HEALTH_CHECK_ATTEMPTS: u32 = 50;
const HEALTH_CHECK_INTERVAL_MS: u64 = 200;

fn repo_root() -> std::path::PathBuf {
    // desktop/src-tauri/ -> desktop/ -> repo root
    std::env::current_dir()
        .expect("could not read current directory")
        .parent()
        .and_then(|p| p.parent())
        .expect("expected desktop/src-tauri to be two levels under the repo root")
        .to_path_buf()
}

fn spawn_server() -> std::io::Result<Child> {
    Command::new("python3")
        .args([
            "-m",
            "uvicorn",
            "server.app:app",
            "--port",
            &SERVER_PORT.to_string(),
            "--log-level",
            "warning",
        ])
        .current_dir(repo_root())
        .stdout(Stdio::null())
        .stderr(Stdio::inherit())
        .spawn()
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
            let child = spawn_server().expect("failed to spawn the OmniAgent server process");
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
