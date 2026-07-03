import importlib
import os
import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch


class TestCheckpointBackend(unittest.TestCase):
    def test_graph_checkpoint_uses_langgraph_sqlite_saver(self):
        fake_sqlite_module = types.ModuleType("langgraph.checkpoint.sqlite")

        class FakeSqliteSaver:
            def __init__(self, conn):
                self.conn = conn

            @classmethod
            @contextmanager
            def from_conn_string(cls, conn_string):
                yield cls(conn_string)

        fake_sqlite_module.SqliteSaver = FakeSqliteSaver
        fake_sqlite_module.__dict__["SqliteSaver"] = FakeSqliteSaver

        with patch.dict(sys.modules, {"langgraph.checkpoint.sqlite": fake_sqlite_module}):
            sys.modules.pop("graph.checkpoint", None)
            checkpoint_module = importlib.import_module("graph.checkpoint")
            manager = checkpoint_module.GraphCheckpointManager()

            self.assertIsInstance(manager.checkpointer, FakeSqliteSaver)

    def test_graph_checkpoint_falls_back_to_memory_when_backend_is_memory(self):
        with patch.dict(os.environ, {"CHECKPOINT_BACKEND": "memory"}, clear=False):
            sys.modules.pop("graph.checkpoint", None)
            checkpoint_module = importlib.import_module("graph.checkpoint")
            manager = checkpoint_module.GraphCheckpointManager()
            self.assertEqual(manager.backend, "memory")
            self.assertTrue(hasattr(manager.checkpointer, "put"))
