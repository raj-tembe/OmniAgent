"""
LLM provider utilities for testing and debugging.
Run with: python -m agents.llm_utils
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.llm import llm, LLMInitializationError
from config import (
    LLM_PROVIDER, LLM_TEMPERATURE,
    GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY,
    HF_API_KEY, OLLAMA_BASE_URL, HF_MODEL, OLLAMA_MODEL
)


def print_config():
    """Print current LLM configuration."""
    print("\n" + "="*60)
    print("OmniAgent LLM Configuration")
    print("="*60)
    print(f"\nProvider: {LLM_PROVIDER}")
    print(f"Temperature: {LLM_TEMPERATURE}")
    
    print("\n" + "-"*60)
    print("Credentials Status:")
    print("-"*60)
    print(f"Gemini API Key:     {'✓ Set' if GEMINI_API_KEY else '✗ Not set'}")
    print(f"OpenAI API Key:     {'✓ Set' if OPENAI_API_KEY else '✗ Not set'}")
    print(f"Groq API Key:       {'✓ Set' if GROQ_API_KEY else '✗ Not set'}")
    print(f"HuggingFace Token:  {'✓ Set' if HF_API_KEY else '✗ Not set'}")
    
    print("\n" + "-"*60)
    print("Provider-Specific Config:")
    print("-"*60)
    print(f"Ollama Base URL:    {OLLAMA_BASE_URL}")
    print(f"Ollama Model:       {OLLAMA_MODEL}")
    print(f"HuggingFace Model:  {HF_MODEL}")


def test_provider():
    """Test if the current LLM provider works."""
    print("\n" + "="*60)
    print(f"Testing LLM Provider: {LLM_PROVIDER}")
    print("="*60 + "\n")
    
    try:
        print(f"Initializing {LLM_PROVIDER} provider...", end=" ")
        llm_instance = llm()
        print("✓ Success!\n")
        
        print(f"Provider type: {type(llm_instance).__name__}")
        print(f"Model: {getattr(llm_instance, 'model_name', getattr(llm_instance, 'model', 'Unknown'))}")
        
        # Test a simple prompt
        print("\nTesting with simple prompt: 'Say hello'")
        print("-"*60)
        response = llm_instance.invoke("Say hello in one sentence.")
        print(response.content if hasattr(response, 'content') else str(response))
        print("-"*60)
        print("\n✓ Provider test successful!")
        return True
        
    except LLMInitializationError as e:
        print(f"\n✗ Initialization Error:\n{e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting tips:")
        if "connection" in str(e).lower():
            print("- Check your internet connection")
            print("- Verify the API endpoint is accessible")
        if "key" in str(e).lower() or "auth" in str(e).lower():
            print("- Verify your API credentials in .env file")
        print("\nFor more help, see docs/LLM_PROVIDER_GUIDE.md")
        return False


def list_providers():
    """List all available providers and their status."""
    print("\n" + "="*60)
    print("Available LLM Providers")
    print("="*60 + "\n")
    
    providers = {
        "gemini": {
            "description": "Google Gemini API",
            "credential_env": "GOOGLE_GEMINI_API_KEY",
            "setup": "https://aistudio.google.com/app/apikeys"
        },
        "openai": {
            "description": "OpenAI GPT models",
            "credential_env": "OPENAI_API_KEY",
            "setup": "https://platform.openai.com/api-keys"
        },
        "groq": {
            "description": "Groq API (fastest inference)",
            "credential_env": "GROQ_API_KEY",
            "setup": "https://console.groq.com/keys"
        },
        "ollama": {
            "description": "Local Ollama inference",
            "credential_env": "None (local)",
            "setup": "https://ollama.ai"
        },
        "huggingface_local": {
            "description": "Local HuggingFace models",
            "credential_env": "None (local)",
            "setup": "pip install transformers torch"
        },
        "huggingface_cloud": {
            "description": "HuggingFace Inference API",
            "credential_env": "HF_API_KEY",
            "setup": "https://huggingface.co/settings/tokens"
        }
    }
    
    for name, info in providers.items():
        is_current = "← CURRENT" if name == LLM_PROVIDER.lower() else ""
        print(f"{name.upper()} {is_current}")
        print(f"  Description: {info['description']}")
        print(f"  Credential:  {info['credential_env']}")
        print(f"  Setup:       {info['setup']}")
        print()


def main():
    """Run diagnostic utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OmniAgent LLM Provider Utilities"
    )
    parser.add_argument(
        "command",
        choices=["config", "test", "list"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "config":
        print_config()
    elif args.command == "test":
        success = test_provider()
        sys.exit(0 if success else 1)
    elif args.command == "list":
        list_providers()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python -m agents.llm_utils config  # Show current configuration")
        print("  python -m agents.llm_utils test    # Test the current provider")
        print("  python -m agents.llm_utils list    # List all available providers")
    else:
        main()
