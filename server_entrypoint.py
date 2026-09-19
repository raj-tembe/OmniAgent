"""
Standalone entrypoint for the bundled desktop distribution.

PyInstaller bundles by tracing imports from a single Python entrypoint —
`python -m uvicorn server.app:app` (what the dev-mode Tauri shell runs, see
desktop/src-tauri/src/main.rs) doesn't give it one to trace, since uvicorn's
own CLI resolves that import string at runtime, invisibly to PyInstaller's
static analysis. This script exists purely so there's a plain, traceable
`import server.app` PyInstaller can follow, then calls uvicorn the same way
the CLI would.

Not used in local dev — `main.rs` still runs the venv's `python -m uvicorn`
there, since that path already works and re-verifying it wasn't worth the
risk. This is only for `scripts/build_desktop_backend.sh`'s bundled build.
"""
import sys

import uvicorn

from server.app import app

if __name__ == "__main__":
    port = 8420
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
