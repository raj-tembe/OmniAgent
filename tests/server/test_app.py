import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from server.app import app
from server.sessions import SessionManager


def _fast_completing_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False, workspace=None):
    return {"execution_success": True, "quality_score": 8.5, "session_id": session_id}


class TestServerEndpoints(unittest.TestCase):

    def setUp(self):
        self.test_manager = SessionManager(run_workflow_fn=_fast_completing_workflow)
        self.patcher = patch("server.app.session_manager", self.test_manager)
        self.patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.patcher.stop()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_create_session_returns_session_id(self):
        response = self.client.post("/sessions", json={"user_request": "build a CLI tool"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("session_id", response.json())

    def test_get_session_reflects_eventual_completion(self):
        session_id = self.client.post("/sessions", json={"user_request": "build a CLI tool"}).json()["session_id"]

        deadline = time.time() + 2.0
        status = None
        while time.time() < deadline:
            status = self.client.get(f"/sessions/{session_id}").json()["status"]
            if status == "completed":
                break
            time.sleep(0.02)

        self.assertEqual(status, "completed")

    def test_get_unknown_session_returns_404(self):
        response = self.client.get("/sessions/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_create_session_passes_through_agent_mode_and_auto_approve(self):
        received_kwargs = {}

        def capturing_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False, workspace=None):
            received_kwargs.update(dict(
                user_request=user_request, interactive=interactive,
                agent_mode=agent_mode, auto_approve=auto_approve,
            ))
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=capturing_workflow)
        with patch("server.app.session_manager", manager):
            self.client.post("/sessions", json={
                "user_request": "review this code",
                "agent_mode": "plan",
                "auto_approve": True,
                "interactive": True,
            })

        time.sleep(0.2)
        self.assertEqual(received_kwargs["agent_mode"], "plan")
        self.assertTrue(received_kwargs["auto_approve"])
        self.assertTrue(received_kwargs["interactive"])

    def test_event_stream_returns_404_for_unknown_session(self):
        response = self.client.get("/sessions/does-not-exist/events")
        self.assertEqual(response.status_code, 404)

    def test_event_stream_delivers_events_and_closes(self):
        from bus import bus, AgentStarted

        def workflow_with_events(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False, workspace=None):
            bus.publish(AgentStarted(agent="planner", session_id=session_id))
            bus.publish(AgentStarted(agent="coder", session_id=session_id))
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=workflow_with_events)
        with patch("server.app.session_manager", manager):
            session_id = self.client.post("/sessions", json={"user_request": "build"}).json()["session_id"]

            # give the background thread a moment to finish before we start streaming,
            # so the stream sees a completed session with buffered events plus the close marker
            deadline = time.time() + 2.0
            while time.time() < deadline and manager.get_session(session_id).status == "running":
                time.sleep(0.02)

            with self.client.stream("GET", f"/sessions/{session_id}/events") as response:
                lines = [line for line in response.iter_lines() if line.startswith("data: ")]

        payloads = [json.loads(line[len("data: "):]) for line in lines]
        event_types = [p["type"] for p in payloads]

        self.assertIn("agent.started", event_types)
        self.assertEqual(event_types[-1], "stream.closed")

    def test_permission_response_resolves_a_pending_request(self):
        from server.permission_bridge import PendingPermissionStore

        test_store = PendingPermissionStore()
        with patch("server.app.pending_permissions", test_store):
            session_id = self.client.post("/sessions", json={"user_request": "build"}).json()["session_id"]

            # register a pending request the way permission/engine.py would
            import threading
            results = []

            def waiter():
                results.append(test_store.wait_for_resolution("req-1", timeout=2.0))

            t = threading.Thread(target=waiter)
            t.start()
            time.sleep(0.05)

            response = self.client.post(
                f"/sessions/{session_id}/permission-response",
                json={"request_id": "req-1", "approved": True},
            )
            t.join(timeout=2.0)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(results, [True])

    def test_permission_response_for_unknown_session_is_404(self):
        response = self.client.post(
            "/sessions/does-not-exist/permission-response",
            json={"request_id": "req-1", "approved": True},
        )
        self.assertEqual(response.status_code, 404)

    def test_permission_response_for_unknown_request_id_is_404(self):
        session_id = self.client.post("/sessions", json={"user_request": "build"}).json()["session_id"]

        response = self.client.post(
            f"/sessions/{session_id}/permission-response",
            json={"request_id": "never-registered", "approved": True},
        )

        self.assertEqual(response.status_code, 404)


class TestWorkspaceEndpoints(unittest.TestCase):

    def setUp(self):
        self.test_manager = SessionManager(run_workflow_fn=_fast_completing_workflow)
        self.patcher = patch("server.app.session_manager", self.test_manager)
        self.patcher.start()
        self.client = TestClient(app)

        from tempfile import TemporaryDirectory
        self.tmpdir = TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('hi')\n")
        (self.root / "README.md").write_text("# Project\n")

    def tearDown(self):
        self.patcher.stop()
        self.tmpdir.cleanup()

    def test_tree_lists_root_contents(self):
        response = self.client.get("/workspace/tree", params={"root": str(self.root)})

        self.assertEqual(response.status_code, 200)
        names = {e["name"] for e in response.json()["entries"]}
        self.assertEqual(names, {"src", "README.md"})

    def test_tree_lists_nested_path(self):
        response = self.client.get("/workspace/tree", params={"root": str(self.root), "path": "src"})

        self.assertEqual(response.status_code, 200)
        names = {e["name"] for e in response.json()["entries"]}
        self.assertEqual(names, {"main.py"})

    def test_tree_rejects_path_traversal(self):
        response = self.client.get("/workspace/tree", params={"root": str(self.root), "path": "../../etc"})
        self.assertEqual(response.status_code, 400)

    def test_tree_missing_path_is_404(self):
        response = self.client.get("/workspace/tree", params={"root": str(self.root), "path": "nonexistent"})
        self.assertEqual(response.status_code, 404)

    def test_file_returns_content(self):
        response = self.client.get("/workspace/file", params={"root": str(self.root), "path": "src/main.py"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "print('hi')\n")

    def test_file_rejects_denied_filename(self):
        (self.root / ".env").write_text("SECRET=1")

        response = self.client.get("/workspace/file", params={"root": str(self.root), "path": ".env"})

        self.assertEqual(response.status_code, 400)

    def test_file_missing_is_404(self):
        response = self.client.get("/workspace/file", params={"root": str(self.root), "path": "nonexistent.py"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
