import unittest

from bus.event_bus import EventBus, WILDCARD
from bus.events import AgentStarted, SessionStarted, ToolCallStart


class TestEventBus(unittest.TestCase):

    def setUp(self):
        self.eventbus = EventBus()

    def test_subscriber_receives_matching_event(self):
        received = []
        self.eventbus.subscribe("session.started", received.append)

        self.eventbus.publish(SessionStarted(user_request="build a thing"))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].user_request, "build a thing")

    def test_subscriber_does_not_receive_other_event_types(self):
        received = []
        self.eventbus.subscribe("session.started", received.append)

        self.eventbus.publish(AgentStarted(agent="planner"))

        self.assertEqual(received, [])

    def test_wildcard_subscriber_receives_everything(self):
        received = []
        self.eventbus.subscribe(WILDCARD, lambda e: received.append(e.type))

        self.eventbus.publish(SessionStarted(user_request="x"))
        self.eventbus.publish(AgentStarted(agent="coder"))
        self.eventbus.publish(ToolCallStart(tool="read", agent="coder", args={"path": "a.py"}))

        self.assertEqual(received, ["session.started", "agent.started", "tool.call.start"])

    def test_unsubscribe_stops_delivery(self):
        received = []
        unsubscribe = self.eventbus.subscribe("agent.started", received.append)

        self.eventbus.publish(AgentStarted(agent="planner"))
        unsubscribe()
        self.eventbus.publish(AgentStarted(agent="coder"))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].agent, "planner")

    def test_broken_handler_does_not_block_other_subscribers_or_raise(self):
        received = []

        def broken_handler(event):
            raise RuntimeError("boom")

        self.eventbus.subscribe("agent.started", broken_handler)
        self.eventbus.subscribe("agent.started", received.append)

        # must not raise, and the healthy subscriber must still fire
        self.eventbus.publish(AgentStarted(agent="planner"))

        self.assertEqual(len(received), 1)

    def test_publish_sets_timestamp_when_missing(self):
        event = AgentStarted(agent="planner")
        self.assertIsNone(event.timestamp)

        self.eventbus.publish(event)

        self.assertIsNotNone(event.timestamp)

    def test_clear_removes_all_subscribers(self):
        received = []
        self.eventbus.subscribe(WILDCARD, received.append)

        self.eventbus.clear()
        self.eventbus.publish(AgentStarted(agent="planner"))

        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
