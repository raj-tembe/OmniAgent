import threading
import time
import unittest

from server.permission_bridge import PendingPermissionStore, make_server_resolver


class TestPendingPermissionStore(unittest.TestCase):

    def test_resolve_before_wait_is_still_delivered(self):
        # resolve() racing ahead of wait_for_resolution() starting is a real
        # possibility (fast HTTP response vs. thread scheduling), so the
        # store must not lose a decision that arrives first — but resolve()
        # itself requires a registered pending request, so register it via
        # a short-lived wait on another thread first.
        store = PendingPermissionStore()
        results = []

        def waiter():
            results.append(store.wait_for_resolution("req-1", timeout=2.0))

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.05)  # let wait_for_resolution register the pending entry
        resolved = store.resolve("req-1", True)
        t.join(timeout=2.0)

        self.assertTrue(resolved)
        self.assertEqual(results, [True])

    def test_resolve_with_no_pending_request_returns_false(self):
        store = PendingPermissionStore()
        self.assertFalse(store.resolve("does-not-exist", True))

    def test_timeout_resolves_to_false(self):
        store = PendingPermissionStore()
        started = time.time()

        result = store.wait_for_resolution("req-timeout", timeout=0.2)

        self.assertFalse(result)
        self.assertGreaterEqual(time.time() - started, 0.2)

    def test_deny_decision_is_delivered_correctly(self):
        store = PendingPermissionStore()
        results = []

        def waiter():
            results.append(store.wait_for_resolution("req-deny", timeout=2.0))

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.05)
        store.resolve("req-deny", False)
        t.join(timeout=2.0)

        self.assertEqual(results, [False])

    def test_pending_entry_is_cleaned_up_after_resolution(self):
        store = PendingPermissionStore()

        def waiter():
            store.wait_for_resolution("req-cleanup", timeout=2.0)

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.05)
        store.resolve("req-cleanup", True)
        t.join(timeout=2.0)

        # a second resolve for the same (now-consumed) id should find nothing pending
        self.assertFalse(store.resolve("req-cleanup", True))


class TestMakeServerResolver(unittest.TestCase):

    def test_resolver_blocks_until_store_resolves(self):
        store = PendingPermissionStore()
        resolver = make_server_resolver(store=store, timeout=2.0)
        results = []

        def call_resolver():
            results.append(resolver("bash", "executor", "run tests", "req-42"))

        t = threading.Thread(target=call_resolver)
        t.start()
        time.sleep(0.05)
        store.resolve("req-42", True)
        t.join(timeout=2.0)

        self.assertEqual(results, [True])

    def test_resolver_times_out_to_deny(self):
        store = PendingPermissionStore()
        resolver = make_server_resolver(store=store, timeout=0.2)

        result = resolver("bash", "executor", "run tests", "req-unanswered")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
