#!/usr/bin/env bash
# Builds a standalone, dependency-free executable for the Python backend
# (server/app.py) using PyInstaller, via server_entrypoint.py.
#
# This is the packaging story that was missing: without it, running the
# desktop app requires the end user to set up a Python venv and
# `pip install -r requirements.txt` themselves (see desktop/README.md's
# "Python interpreter resolution" section for how main.rs falls back to a
# bare `python3` if that hasn't been done). A bundled executable needs
# none of that on the machine it runs on.
#
# Verified: the resulting binary was run in an isolated temp directory with
# PYTHONPATH unset and a stripped-down PATH, and correctly served /health
# and POST /sessions — confirming it's genuinely self-contained, not just
# "it built."
#
# Usage: ./scripts/build_desktop_backend.sh
# Output: dist/omniagent-server (or dist/omniagent-server.exe on Windows)

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! python3 -m PyInstaller --version >/dev/null 2>&1; then
    echo "PyInstaller not installed. Run: pip install pyinstaller" >&2
    exit 1
fi

# --onefile: a single self-contained executable, simplest to spawn from
# main.rs and to distribute — at the cost of a slower first launch (it
# unpacks to a temp dir each run) and a larger file (~125MB in testing,
# mostly transitive dependencies like scipy/matplotlib pulled in indirectly
# — see "Known follow-ups" in desktop/README.md for trimming this down).
#
# --collect-submodules on each of our own top-level packages, rather than
# relying on PyInstaller's static import analysis alone: several of our
# modules are only reached via string-based dynamic dispatch (the provider
# registry's @register_provider decorators, for instance) that static
# analysis can miss.
python3 -m PyInstaller \
    --name omniagent-server \
    --onefile \
    --hidden-import uvicorn.logging \
    --hidden-import uvicorn.loops \
    --hidden-import uvicorn.loops.auto \
    --hidden-import uvicorn.protocols \
    --hidden-import uvicorn.protocols.http \
    --hidden-import uvicorn.protocols.http.auto \
    --hidden-import uvicorn.protocols.websockets \
    --hidden-import uvicorn.protocols.websockets.auto \
    --hidden-import uvicorn.lifespan \
    --hidden-import uvicorn.lifespan.on \
    --collect-submodules server \
    --collect-submodules agents \
    --collect-submodules graph \
    --collect-submodules tools \
    --collect-submodules bus \
    --collect-submodules permission \
    --collect-submodules provider \
    --collect-submodules mcp_client \
    --collect-submodules lsp \
    --collect-submodules skill \
    --collect-submodules session \
    --collect-submodules config \
    --collect-submodules schemas \
    --collect-submodules memory \
    --collect-submodules observability \
    --noconfirm \
    server_entrypoint.py

echo ""
echo "Built: dist/omniagent-server"
echo "Verify it with: ./dist/omniagent-server 8420 &  then  curl http://127.0.0.1:8420/health"
