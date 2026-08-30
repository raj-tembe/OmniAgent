import os
import unittest
from unittest.mock import patch

from agents.llm import llm


class TestLLM(unittest.TestCase):

    def test_llm_uses_google_gemini_api_key_fallback(self):
        with patch.dict(os.environ, {"GOOGLE_GEMINI_API_KEY": "test-key"}, clear=True):
            model = llm()

        self.assertIsNotNone(model)

    def test_llm_raises_when_api_key_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(EnvironmentError):
                llm()
