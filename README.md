# 🚀 OmniAgent : Autonomous Research & Coding Agent Platform

> A production-grade multi-agent AI system built using LangGraph that can research, plan, code, execute, debug, review, and improve software autonomously.

---

# 🌟 Vision

This project is designed to explore the true capabilities of **Agentic AI Systems** using:

- LangGraph
- Multi-Agent Workflows
- Tool Calling
- Autonomous Reasoning
- Human-in-the-loop Systems
- Persistent Memory
- Self-healing AI Loops

Instead of a simple chatbot, this system behaves like an **AI Engineering Team**.

The platform can:
- research topics
- generate production code
- execute programs
- debug errors
- critique outputs
- improve itself iteratively

---

# 🧠 What This Project Is

This is an advanced **AI orchestration platform** where multiple AI agents collaborate through a graph-based workflow.

The system mimics how real engineering teams work.

Example workflow:

```text
User → Planner → Researcher → Coder → Executor → Critic → Human Approval → Final Output
```

Each AI agent has:
- a role
- memory
- tools
- responsibilities
- decision-making capability

---

# ❓ Why Build This?

Modern AI applications are evolving from:
- simple prompts
- single-response chatbots

to:

✅ autonomous systems  
✅ collaborative agents  
✅ self-correcting workflows  
✅ long-running reasoning systems  

This project helps practice:
- Agent Engineering
- Workflow Orchestration
- AI Reliability
- Production AI Design
- Autonomous Debugging
- Stateful Systems
- Multi-Agent Collaboration

---

# 🎯 Main Goals

The project aims to:

- Build a production-style agentic AI system
- Learn advanced LangGraph concepts
- Create autonomous execution loops
- Practice real-world AI architecture
- Implement self-healing workflows
- Explore memory & persistence
- Simulate enterprise-grade AI systems

---

# 🔥 Core Features

# 1. Multi-Agent Architecture

Different AI agents specialize in different tasks.

| Agent | Responsibility |
|---|---|
| Planner Agent | Breaks goals into tasks |
| Research Agent | Searches web/docs/repos |
| Coding Agent | Generates code |
| Execution Agent | Runs generated code |
| Critic Agent | Reviews outputs |
| Memory Agent | Stores long-term knowledge |
| Human Approval Node | Adds safety layer |

---

# 2. Graph-Based Workflow

The entire system runs using LangGraph stateful workflows.

Unlike traditional pipelines:
- nodes can loop
- retry
- branch
- pause
- recover

---

# 3. Autonomous Debugging

The platform can:
1. generate code
2. execute it
3. detect errors
4. fix issues automatically
5. retry execution

Example:

```text
Generate Code
      ↓
Run Program
      ↓
Error?
   YES → Fix → Retry
      ↓
Success
```

---

# 4. Human-in-the-Loop

Critical actions require human approval.

Examples:
- deployment
- deleting files
- expensive API calls
- database modifications

This makes the system safer and more production-ready.

---

# 5. Persistent Memory

The platform remembers:
- previous tasks
- coding patterns
- successful fixes
- user preferences
- execution history

---

# 🏗️ System Architecture

```text
                        ┌────────────────────┐
                        │      USER          │
                        └─────────┬──────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │     Planner Agent       │
                    └─────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │    Research Agent       │
                    └─────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │     Coding Agent        │
                    └─────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │    Execution Agent      │
                    └─────────┬───────────────┘
                              │
                     Error? ──┴──── YES
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      Critic Agent       │
                    └─────────┬───────────────┘
                              │
                   Needs Changes?
                       YES │
                           ▼
                    ┌─────────────────────────┐
                    │     Coding Agent        │
                    └─────────────────────────┘

                              │ NO
                              ▼
                    ┌─────────────────────────┐
                    │  Human Approval Node    │
                    └─────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      Final Output       │
                    └─────────────────────────┘
```

---

# ⚙️ How It Works

# Step 1 — User Request

The user provides a goal.

Example:

```text
Build a Flask authentication API using JWT.
```

---

# Step 2 — Planning Phase

The Planner Agent:
- analyzes the request
- creates task breakdowns
- determines execution strategy

Example:

```text
1. Setup Flask app
2. Create JWT auth
3. Add database
4. Create APIs
5. Add tests
6. Generate README
```

---

# Step 3 — Research Phase

The Research Agent:
- searches documentation
- checks APIs
- finds best practices
- gathers implementation references

---

# Step 4 — Code Generation

The Coding Agent:
- generates files
- creates project structure
- writes logic
- creates tests
- updates state

---

# Step 5 — Execution

The Execution Agent:
- runs code inside a sandbox
- captures logs/errors
- validates outputs

---

# Step 6 — Self-Healing Loop

If execution fails:

```text
Error → Diagnose → Repair → Retry
```

The agent automatically attempts fixes.

---

# Step 7 — Critic Review

The Critic Agent reviews:
- code quality
- correctness
- hallucinations
- security vulnerabilities
- architecture

---

# Step 8 — Human Approval

High-risk actions pause execution until approved.

---

# Step 9 — Final Delivery

The system returns:
- source code
- documentation
- reports
- logs
- architecture explanations

---

# 🧩 LangGraph Concepts Used

| Concept | Usage |
|---|---|
| Stateful Graphs | Workflow orchestration |
| Conditional Edges | Error routing |
| Cyclic Graphs | Repair loops |
| Parallel Branches | Concurrent research |
| Interrupts | Human approval |
| Checkpointing | Persistence |
| Tool Calling | Web/Python/File tools |
| Memory | Long-term context |
| Multi-Agent Systems | Specialized AI workers |

---

# 🧠 Shared State Design

The graph uses a centralized state object.

Example:

```python
class AgentState(TypedDict):
    user_request: str
    plan: list
    current_task: str
    generated_code: dict
    execution_logs: str
    error: str
    critic_feedback: str
    approved: bool
```

Every node can:
- read state
- modify state
- route workflow

---

# 🔄 Workflow Design

```mermaid
flowchart TD

    START([User Request])

    START --> API[API / CLI Interface]

    API --> STATE[Initialize Shared State]

    STATE --> PLANNER[Planner Agent]

    PLANNER --> RESEARCHER[Research Agent]

    RESEARCHER --> CODER[Coding Agent]

    CODER --> EXECUTOR[Execution Agent]

    EXECUTOR --> EXEC_CHECK{Execution Successful?}

    EXEC_CHECK -- No --> ERROR_HANDLER[Error Handler]

    ERROR_HANDLER --> RETRY_CHECK{Retry Limit Reached?}

    RETRY_CHECK -- No --> CODER

    RETRY_CHECK -- Yes --> HUMAN_FAIL[Human Intervention Required]

    EXEC_CHECK -- Yes --> CRITIC[Critic Agent]

    CRITIC --> QUALITY_CHECK{Quality Score Acceptable?}

    QUALITY_CHECK -- No --> CODER

    QUALITY_CHECK -- Yes --> SECURITY[Security Validation]

    SECURITY --> SECURITY_CHECK{Safe Output?}

    SECURITY_CHECK -- No --> CODER

    SECURITY_CHECK -- Yes --> MEMORY[Store Memory & Logs]

    MEMORY --> APPROVAL{Human Approval Needed?}

    APPROVAL -- Yes --> HUMAN_APPROVAL[Human Approval Node]

    HUMAN_APPROVAL --> APPROVAL_RESULT{Approved?}

    APPROVAL_RESULT -- No --> STOPPED([Workflow Stopped])

    APPROVAL_RESULT -- Yes --> FINAL[Final Output]

    APPROVAL -- No --> FINAL

    FINAL --> END([Workflow Complete])



    %% Memory Connections
    MEMORY_DB[( Vector Memory DB)]
    CHECKPOINTS[( Checkpoints)]
    LOGS[( Execution Logs)]

    MEMORY --> MEMORY_DB
    MEMORY --> CHECKPOINTS
    MEMORY --> LOGS



    %% Tool Connections
    WEBTOOLS[ Web Search Tools]
    FILETOOLS[ File System Tools]
    GITHUBTOOLS[ GitHub Tools]
    PYTHONTOOLS[ Python Runtime]

    RESEARCHER --> WEBTOOLS

    CODER --> FILETOOLS
    CODER --> GITHUBTOOLS

    EXECUTOR --> PYTHONTOOLS



    %% Observability
    OBSERVE[Observability / LangSmith]

    PLANNER --> OBSERVE
    RESEARCHER --> OBSERVE
    CODER --> OBSERVE
    EXECUTOR --> OBSERVE
    CRITIC --> OBSERVE
```


---

# 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLMs | OpenAI / Groq / Gemini |
| Backend | FastAPI |
| Frontend | Next.js |
| Memory | Redis / SQLite |
| Vector DB | ChromaDB |
| Sandbox | Docker |
| Observability | LangSmith |
| Authentication | Clerk/Auth0 |

---

# 📂 Proposed Project Structure

```text
OMNIAGENT/
│
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── main.py
├── config.py
│
├── agents/
│   ├── __init__.py
│   │
│   ├── planner/
│   │   ├── planner_agent.py
│   │   ├── planner_prompt.py
│   │   ├── planner_schema.py
│   │   └── planner_utils.py
│   │
│   ├── coder/
│   │   ├── coder_agent.py
│   │   ├── coder_prompt.py
│   │   ├── coder_schema.py
│   │   └── coder_utils.py
│   │
│   ├── executor/
│   │   ├── executor_agent.py
│   │   ├── sandbox_runner.py
│   │   ├── docker_runner.py
│   │   └── execution_utils.py
│   │
│   ├── critic/
│   │   ├── critic_agent.py
│   │   ├── critic_prompt.py
│   │   ├── critic_schema.py
│   │   └── critic_utils.py
│   │
│   ├── researcher/
│   │   ├── researcher_agent.py
│   │   ├── researcher_prompt.py
│   │   ├── researcher_schema.py
│   │   └── researcher_utils.py
│   │
│   └── memory/
│       ├── memory_agent.py
│       ├── memory_manager.py
│       └── retrieval.py
│
├── graph/
│   ├── __init__.py
│   │
│   ├── state.py
│   ├── workflow.py
│   ├── router.py
│   ├── nodes.py
│   ├── edges.py
│   ├── conditional_edges.py
│   ├── checkpoint.py
│   └── graph_visualizer.py
│
├── tools/
│   ├── __init__.py
│   │
│   ├── web_tools/
│   │   ├── tavily_search.py
│   │   ├── serpapi_search.py
│   │   └── arxiv_search.py
│   │
│   ├── code_tools/
│   │   ├── python_repl.py
│   │   ├── file_writer.py
│   │   ├── file_reader.py
│   │   └── terminal_runner.py
│   │
│   ├── github_tools/
│   │   ├── github_search.py
│   │   ├── repo_analyzer.py
│   │   └── commit_generator.py
│   │
│   └── validation_tools/
│       ├── syntax_checker.py
│       ├── dependency_checker.py
│       └── security_checker.py
│
├── prompts/
│   ├── planner_prompt.md
│   ├── coder_prompt.md
│   ├── critic_prompt.md
│   ├── researcher_prompt.md
│   └── system_prompt.md
│
├── schemas/
│   ├── planner_schema.py
│   ├── coder_schema.py
│   ├── critic_schema.py
│   ├── execution_schema.py
│   └── shared_schema.py
│
├── memory/
│   ├── vector_store/
│   │   ├── chroma_store.py
│   │   └── embeddings.py
│   │
│   ├── checkpoints/
│   │   ├── sqlite_checkpoint.py
│   │   └── postgres_checkpoint.py
│   │
│   └── conversation_memory/
│       ├── short_term.py
│       └── long_term.py
│
├── execution/
│   ├── sandbox/
│   │   ├── sandbox_manager.py
│   │   ├── docker_executor.py
│   │   └── isolated_runner.py
│   │
│   ├── logs/
│   │   ├── execution_logs/
│   │   └── error_logs/
│   │
│   └── generated_projects/
│
├── api/
│   ├── app.py
│   ├── routes.py
│   ├── websocket.py
│   └── middleware.py
│
├── frontend/
│   ├── dashboard/
│   ├── workflow_visualizer/
│   ├── execution_monitor/
│   └── memory_viewer/
│
├── database/
│   ├── models.py
│   ├── db.py
│   └── migrations/
│
├── observability/
│   ├── langsmith_tracing.py
│   ├── metrics.py
│   ├── monitoring.py
│   └── token_tracking.py
│
├── tests/
│   ├── test_agents/
│   ├── test_graph/
│   ├── test_tools/
│   ├── test_execution/
│   └── integration_tests/
│
├── docs/
│   ├── architecture.md
│   ├── workflow.md
│   ├── agent_design.md
│   ├── memory_system.md
│   └── deployment.md
│
├── notebooks/
│   ├── experiments/
│   ├── prompt_testing/
│   └── langgraph_learning/
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── sandbox.Dockerfile
│
├── scripts/
│   ├── setup.sh
│   ├── run_dev.sh
│   ├── start_server.sh
│   └── clean_logs.sh
│
└── assets/
    ├── architecture_diagrams/
    ├── screenshots/
    └── workflow_images/

```

---

# 🔒 Safety & Reliability

The platform includes:
- human approval layers
- execution sandboxes
- hallucination detection
- retry limits
- validation nodes
- isolated environments

---

# 📈 Future Enhancements

Potential upgrades:

- Voice-based agents
- Autonomous deployment
- Multi-modal reasoning
- PDF understanding
- GitHub integration
- Long-term memory systems
- AI-generated UI
- Multi-user collaboration
- Agent communication protocols

---

# 🌍 Real-World Inspiration

This project is inspired by:
- OpenAI Codex Agents
- Devin AI
- AutoGPT
- Claude Code
- Enterprise AI Automation Systems

---

# 🎓 Learning Outcomes

By building this project, you will deeply understand:

- LangGraph internals
- Agent orchestration
- Autonomous workflows
- Multi-agent systems
- AI debugging loops
- Production AI architecture
- Stateful AI systems
- AI reliability engineering

---

# 🚀 End Goal

The long-term vision is to create:

> A fully autonomous AI engineering system capable of researching, coding, debugging, reviewing, and improving software with minimal human intervention.

---

# 📜 License

MIT License

---

# ⭐ Final Note

This project is not just another AI chatbot.

It is an exploration into the future of:
- autonomous software engineering
- collaborative AI systems
- intelligent orchestration
- self-improving workflows

Building this will significantly strengthen:
- AI engineering skills
- system design understanding
- production AI architecture knowledge
- LangGraph expertise

---
