import time
import unittest

from bus import bus, SessionStarted, AgentStarted, SessionCompleted
from server.sessions import SessionManager


class TestSessionManager(unittest.TestCase):

    def _wait_until(self, predicate, timeout=2.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def test_create_session_runs_workflow_in_background_and_completes(self):
        def fake_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            return {"execution_success": True, "session_id": session_id}

        manager = SessionManager(run_workflow_fn=fake_run_workflow)
        session_id = manager.create_session(user_request="build a thing")

        self.assertTrue(self._wait_until(lambda: manager.get_session(session_id).status == "completed"))
        record = manager.get_session(session_id)
        self.assertEqual(record.result["execution_success"], True)

    def test_create_session_returns_immediately_without_blocking(self):
        started = time.time()

        def slow_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            time.sleep(0.5)
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=slow_run_workflow)
        session_id = manager.create_session(user_request="slow task")

        elapsed = time.time() - started
        self.assertLess(elapsed, 0.4)  # create_session itself must not block on the 0.5s workflow
        self.assertEqual(manager.get_session(session_id).status, "running")

    def test_workflow_exception_marks_session_as_error(self):
        def broken_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            raise RuntimeError("something broke")

        manager = SessionManager(run_workflow_fn=broken_run_workflow)
        session_id = manager.create_session(user_request="broken task")

        self.assertTrue(self._wait_until(lambda: manager.get_session(session_id).status == "error"))
        record = manager.get_session(session_id)
        self.assertIn("something broke", record.result["error"])

    def test_get_session_returns_none_for_unknown_id(self):
        manager = SessionManager(run_workflow_fn=lambda **kwargs: {})
        self.assertIsNone(manager.get_session("does-not-exist"))

    def test_events_are_captured_only_for_matching_session_id(self):
        captured_ids = []

        def fake_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            # publish an event for THIS session and one for an unrelated session
            bus.publish(AgentStarted(agent="planner", session_id=session_id))
            bus.publish(AgentStarted(agent="planner", session_id="some-other-session"))
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=fake_run_workflow)
        session_id = manager.create_session(user_request="build a thing")

        self.assertTrue(self._wait_until(lambda: manager.get_session(session_id).status == "completed"))
        record = manager.get_session(session_id)

        agent_events = [e for e in record.events if e.get("type") == "agent.started"]
        self.assertEqual(len(agent_events), 1)
        self.assertEqual(agent_events[0]["session_id"], session_id)

    def test_events_from_offset_returns_only_new_events(self):
        record_events = []

        def fake_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            bus.publish(AgentStarted(agent="planner", session_id=session_id))
            bus.publish(AgentStarted(agent="coder", session_id=session_id))
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=fake_run_workflow)
        session_id = manager.create_session(user_request="build a thing")
        self.assertTrue(self._wait_until(lambda: manager.get_session(session_id).status == "completed"))

        record = manager.get_session(session_id)
        first_batch = record.events_from(0)
        second_batch = record.events_from(len(first_batch))

        self.assertEqual(len(first_batch), 2)
        self.assertEqual(second_batch, [])

    def test_bus_subscription_is_removed_after_session_completes(self):
        def fake_run_workflow(user_request, interactive, agent_mode, auto_approve, session_id, server_mode=False):
            return {"execution_success": True}

        manager = SessionManager(run_workflow_fn=fake_run_workflow)
        session_id = manager.create_session(user_request="build a thing")
        self.assertTrue(self._wait_until(lambda: manager.get_session(session_id).status == "completed"))

        subscribers_before = len(bus._subscribers.get("*", []))
        # publishing more events for this session_id after completion should not grow the record
        bus.publish(AgentStarted(agent="late-arrival", session_id=session_id))
        record = manager.get_session(session_id)
        late_events = [e for e in record.events if e.get("agent") == "late-arrival"]
        self.assertEqual(late_events, [])


if __name__ == "__main__":
    unittest.main()
