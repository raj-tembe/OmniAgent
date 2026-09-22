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
# IMPORTANT: build from a venv based on requirements.txt as shipped (no
# optional provider packages uncommented). A prior version of
# requirements.txt had langchain-openai/-groq/-ollama/-huggingface, plus
# transformers and torch, uncommented despite being labeled optional — live
# verification confirmed this produced a 2.6GB binary that failed to bind
# its HTTP port at all in a frozen context. --exclude-module below is a
# second, defensive layer on top of that fix: even if you build from a dev
# venv where you've manually installed torch for local-inference work, it
# won't end up in the bundle. If you actually need a provider other than
# Gemini bundled in, install just that one package (not torch/transformers)
# into your build venv before running this script.
#
# Usage: ./scripts/build_desktop_backend.sh
# Output: dist/omniagent-server (or dist/omniagent-server.exe on Windows)

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! python3 -m PyInstaller --version >/dev/null 2>&1; then
    echo "PyInstaller not installed. Run: pip install -r requirements-build.txt" >&2
    exit 1
fi

for heavy in torch transformers; do
    if python3 -c "import $heavy" >/dev/null 2>&1; then
        echo "warning: '$heavy' is installed in this environment and will be" >&2
        echo "explicitly excluded from the bundle (see --exclude-module below)." >&2
        echo "The build will still succeed, but if you actually meant to bundle" >&2
        echo "local HuggingFace inference support, this isn't the way to do it" >&2
        echo "yet — that needs its own, much larger, opt-in build path." >&2
    fi
done

# --onefile: a single self-contained executable, simplest to spawn from
# main.rs and to distribute — at the cost of a slower first launch (it
# unpacks to a temp dir each run).
#
# --collect-submodules on each of our own top-level packages, rather than
# relying on PyInstaller's static import analysis alone: several of our
# modules are only reached via string-based dynamic dispatch (the provider
# registry's @register_provider decorators, for instance) that static
# analysis can miss.
#
# --exclude-module for torch/transformers/CUDA and other heavy ML packages:
# defensive, see the big comment above. PyInstaller drops any bundling of
# these even if it finds import statements referencing them (which it will,
# since agents/llm.py's _init_huggingface_local imports transformers/torch
# inside its own function body — that's fine, it's genuinely optional code
# that only runs if LLM_PROVIDER=huggingface_local, and the bundle isn't
# built to support that provider).
#
# --exclude-module for graph.graph_visualizer and tools.integration_test_helper:
# confirmed dev-only (grep shows nothing outside those two files itself
# imports either one) but swept in anyway by the broad --collect-submodules
# above, which walks whole packages rather than following actual reachable
# imports.
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
    --exclude-module torch \
    --exclude-module transformers \
    --exclude-module accelerate \
    --exclude-module tokenizers \
    --exclude-module sentencepiece \
    --exclude-module nvidia \
    --exclude-module graph.graph_visualizer \
    --exclude-module tools.integration_test_helper \
    --noconfirm \
    server_entrypoint.py

echo ""
echo "Built: dist/omniagent-server"
du -h dist/omniagent-server 2>/dev/null || true
echo "Verify it with: ./dist/omniagent-server 8420 &  then  curl http://127.0.0.1:8420/health"

# Also stage a copy where Tauri's `externalBin` (see tauri.conf.json) expects
# it, so `cargo tauri build` picks it up and includes it in the actual
# installer — not just cargo tauri dev's manual dist/ check. Tauri's
# convention requires the binary name to be suffixed with the Rust target
# triple, detected via `rustc -vV` when a Rust toolchain is available.
# Skipped gracefully (not a build failure) when it isn't — dist/omniagent-server
# above still works for `cargo tauri dev` either way.
if command -v rustc >/dev/null 2>&1; then
    HOST_TRIPLE="$(rustc -vV | sed -n 's/^host: //p')"
    if [ -n "$HOST_TRIPLE" ]; then
        SRC_BIN="dist/omniagent-server"
        DEST_BIN="desktop/src-tauri/binaries/omniagent-server-${HOST_TRIPLE}"
        if [[ "$HOST_TRIPLE" == *"windows"* ]]; then
            SRC_BIN="${SRC_BIN}.exe"
            DEST_BIN="${DEST_BIN}.exe"
        fi
        mkdir -p desktop/src-tauri/binaries
        cp "$SRC_BIN" "$DEST_BIN"
        echo "Also staged for 'cargo tauri build': $DEST_BIN"
    fi
else
    echo ""
    echo "note: rustc not found, skipped staging a copy for 'cargo tauri build'."
    echo "dist/omniagent-server (above) still works for 'cargo tauri dev'."
    echo "Re-run this script on a machine with Rust installed before 'cargo tauri build'"
    echo "if you want the bundled binary included in the actual installer."
fi
