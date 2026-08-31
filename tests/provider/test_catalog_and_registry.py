import unittest

from provider.catalog import CATALOG, get_model_info, list_providers
from provider.registry import get_initializer, register_provider, registered_providers


class TestCatalog(unittest.TestCase):

    def test_all_six_providers_present(self):
        self.assertEqual(
            list_providers(),
            ["gemini", "groq", "huggingface_cloud", "huggingface_local", "ollama", "openai"],
        )

    def test_get_model_info_returns_matching_entry(self):
        info = get_model_info("gemini")
        self.assertEqual(info.provider, "gemini")
        self.assertTrue(info.supports_tools)

    def test_get_model_info_is_case_and_whitespace_insensitive(self):
        info = get_model_info("  GEMINI  ")
        self.assertEqual(info.provider, "gemini")

    def test_unknown_provider_raises_key_error(self):
        with self.assertRaises(KeyError):
            get_model_info("does-not-exist")

    def test_local_providers_do_not_require_api_key(self):
        self.assertFalse(CATALOG["ollama"].requires_api_key)
        self.assertFalse(CATALOG["huggingface_local"].requires_api_key)

    def test_cloud_providers_require_api_key(self):
        self.assertTrue(CATALOG["gemini"].requires_api_key)
        self.assertTrue(CATALOG["openai"].requires_api_key)


class TestRegistry(unittest.TestCase):

    def setUp(self):
        # isolate from whatever agents.llm may have already registered
        import provider.registry as registry_module
        self._original = dict(registry_module._INITIALIZERS)
        registry_module._INITIALIZERS.clear()

    def tearDown(self):
        import provider.registry as registry_module
        registry_module._INITIALIZERS.clear()
        registry_module._INITIALIZERS.update(self._original)

    def test_register_and_lookup(self):
        @register_provider("test-provider")
        def _init():
            return "instance"

        self.assertIn("test-provider", registered_providers())
        self.assertEqual(get_initializer("test-provider")(), "instance")

    def test_lookup_is_case_and_whitespace_insensitive(self):
        @register_provider("test-provider")
        def _init():
            return "instance"

        self.assertEqual(get_initializer("  Test-Provider  ")(), "instance")

    def test_unregistered_provider_raises_key_error(self):
        with self.assertRaises(KeyError):
            get_initializer("nonexistent")


if __name__ == "__main__":
    unittest.main()
