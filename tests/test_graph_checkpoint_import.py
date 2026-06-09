import importlib
import os
import sys
import unittest
import unittest.mock


class TestGraphCheckpointImport(unittest.TestCase):

    def test_graph_checkpoint_import_does_not_require_postgres_module(self):
        with unittest.mock.patch.dict(os.environ, {"CHECKPOINT_BACKEND": "sqlite"}, clear=False):
            sys.modules.pop("memory.checkpoints.postgres_checkpoint", None)
            sys.modules.pop("graph.checkpoint", None)
            sys.modules.pop("graph", None)

            checkpoint_module = importlib.import_module("graph.checkpoint")

            self.assertTrue(hasattr(checkpoint_module, "GraphCheckpointManager"))
            self.assertNotIn("memory.checkpoints.postgres_checkpoint", sys.modules)
