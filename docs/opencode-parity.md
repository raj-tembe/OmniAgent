# OpenCode parity tracker

One line per opencode core module (`packages/opencode/src/*`), tracking
whether OmniAgent has an equivalent. Status is `have` / `partial` / `missing`.
Update this file at the end of each phase in `omniagent-opencode-parity-plan.md`
rather than letting it drift — it's the source of truth for "are we actually
catching up."

No terminal UI is planned (see the plan doc) — `tui` is intentionally
excluded from this tracker. IDE work is tracked separately once Phase 5 starts.

| opencode module | status  | OmniAgent equivalent | notes |
|---|---|---|---|
| bus | have | `bus/` | Phase 0. Sync in-process pub/sub, typed pydantic events, wildcard subscribe. Wired into `graph/workflow.py` callbacks + `main.py` session lifecycle. |
| config | partial | `config/` | Phase 0. New `omniagent.json` schema + loader (permission/agent/provider/mcp/plugin) added alongside the existing env-based settings (`config/env.py`). Nothing consumes the new schema yet — that's Phase 1+. |
| agent | partial | `agents/planner`, `agents/coder`, `agents/critic`, `agents/executor`, `agents/researcher`, `agents/memory`, `agents/human`, `agents/subagent.py` | Fixed-role graph nodes exist, plus a general-purpose subagent spawn (`run_subagent`). `graph/state.py` now carries `agent_mode` (build/plan) and `auto_approve`, and `main.py` exposes `--agent-mode`/`--plan`/`--auto` CLI flags — but only `executor_agent` actually consults `agent_mode` so far; coder/researcher/critic don't yet branch on it. Remaining for a later Phase 1 pass. |
| permission | have | `permission/` | Phase 1. `PermissionEngine` — per-tool allow/ask/deny, wildcards, `--auto`, mode-aware defaults. Wired into `executor_agent.py` gating the real "write"/"bash"-equivalent actions (save + run generated code in sandbox), not just the previously-unused `FileWriterTool`/`TerminalRunnerTool` classes. |
| provider | partial | `agents/llm.py`, `config/env.py` | Multi-provider already (Gemini/OpenAI/Groq/Ollama/HF), but wiring is a big if/elif, not a declarative catalog. Phase 2. |
| session | partial | `graph/state.py`, `graph/checkpoint.py`, `memory/checkpoints/` | LangGraph checkpointing exists. No compaction/overflow/summary policy layer. Phase 2. |
| lsp | missing | — | Phase 2. |
| mcp | missing | — | Phase 2. |
| skill | have | `skill/` | Phase 1. `SKILL.md` discovery (project + `.claude`/`.agents`-compatible dirs, walked to git root) + global dirs, on-demand full-body loading. Wired into `planner_chain.py`'s prompt so the planner sees available skills every turn. |
| tool | partial | `tools/code_tools`, `tools/github_tools`, `tools/validation_tools`, `tools/web_tools`, `agents/subagent.py` (task) | Have file read/write, terminal runner, web search, validators, and now a `task`-tool equivalent (`run_subagent`, wired into the planner's repeated-failure escalation path). Still missing: `glob`/`grep` fast search, structured `edit`/`apply_patch`, `todo`/`todowrite`, `question` (agent-initiated clarification). Carry to next Phase 1 pass. |
| plugin | missing | — | Not planned until custom-tools convention (Phase 3) proves out; may fold together. |
| server | missing | — | Phase 4. |
| sdk / protocol | missing | — | Phase 4, generated from the Phase 4 server's OpenAPI schema. |
| share | missing | — | Phase 4 (static export, not opencode's hosted links). |
| worktree / git | partial | `tools/github_tools/` | Have repo analysis / commit generation / search. No worktree management. |
| snapshot | missing | — | Not yet scoped; likely folds into session/checkpoint work. |
| question | missing | — | Covered under `tool` (Phase 1) — agent-initiated clarification prompt. |
| ide | missing | — | Phase 5. This is the planned replacement for opencode's `tui`. |
| account / auth | n/a | — | Deprioritized (Phase 7) — no hosted product to authenticate against yet. |
| control-plane | n/a | — | Deprioritized (Phase 7) — enterprise/hosted concept, out of scope. |
| desktop app | n/a | — | Deprioritized (Phase 7) beyond what the Phase 5 IDE covers. |
| web console | n/a | — | Deprioritized (Phase 7). |

## Legend

- **have** — a real equivalent exists and does the job.
- **partial** — something exists but doesn't cover the full behavior opencode has.
- **missing** — nothing built yet, and it's in-scope on the roadmap.
- **n/a** — explicitly out of scope per the parity plan's Phase 7.
