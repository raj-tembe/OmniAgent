#!/usr/bin/env python3
"""
OmniAgent LLM Provider Setup Script
Installs dependencies for your chosen LLM provider.

Usage: python setup_llm.py [provider]
"""
import subprocess
import sys
from pathlib import Path


PROVIDER_DEPS = {
    "gemini": {
        "packages": ["langchain-google-genai", "google-generativeai"],
        "description": "Google Gemini API",
        "env_vars": ["GOOGLE_GEMINI_API_KEY"],
    },
    "openai": {
        "packages": ["langchain-openai"],
        "description": "OpenAI API",
        "env_vars": ["OPENAI_API_KEY"],
    },
    "groq": {
        "packages": ["langchain-groq"],
        "description": "Groq API",
        "env_vars": ["GROQ_API_KEY"],
    },
    "ollama": {
        "packages": ["langchain-ollama"],
        "description": "Ollama Local Inference",
        "env_vars": [],
    },
    "huggingface_local": {
        "packages": ["langchain-huggingface", "transformers", "torch"],
        "description": "HuggingFace Local Models",
        "env_vars": [],
    },
    "huggingface_cloud": {
        "packages": ["langchain-huggingface"],
        "description": "HuggingFace Cloud API",
        "env_vars": ["HF_API_KEY"],
    },
    "all": {
        "packages": [
            "langchain-google-genai", "google-generativeai",
            "langchain-openai",
            "langchain-groq",
            "langchain-ollama",
            "langchain-huggingface",
            "transformers",
            "torch",
        ],
        "description": "All LLM Providers",
        "env_vars": [],
    }
}


def print_available():
    """Print available providers."""
    print("\nAvailable providers:")
    for provider in PROVIDER_DEPS:
        info = PROVIDER_DEPS[provider]
        print(f"  • {provider:20} - {info['description']}")


def install_provider(provider: str):
    """Install dependencies for a specific provider."""
    provider = provider.lower().strip()
    
    if provider not in PROVIDER_DEPS:
        print(f"\n✗ Unknown provider: {provider}")
        print_available()
        sys.exit(1)
    
    info = PROVIDER_DEPS[provider]
    print(f"\n{'='*60}")
    print(f"Installing {info['description']}")
    print(f"{'='*60}\n")
    
    packages = info["packages"]
    print(f"Packages to install: {', '.join(packages)}\n")
    
    try:
        # Install with pip
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
        print(f"Running: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, check=True)
        
        print(f"\n✓ Successfully installed {provider} dependencies!\n")
        
        # Show next steps
        if info["env_vars"]:
            print("Next steps:")
            print(f"1. Edit .env file (copy from .env.example if needed)")
            print(f"2. Set these environment variables:")
            for var in info["env_vars"]:
                print(f"   - {var}")
            print(f"3. Set LLM_PROVIDER={provider}")
        
        if provider == "ollama":
            print("\n4. Install and start Ollama:")
            print("   - Download from: https://ollama.ai")
            print("   - Run: ollama serve")
            print("   - In another terminal: ollama pull mistral")
        
        if provider == "huggingface_local":
            print("\n4. Note: HuggingFace local requires GPU for good performance")
            print("   Set HF_DEVICE=cuda for GPU (requires CUDA toolkit)")
            print("   Or use HF_DEVICE=cpu for CPU inference (slower)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Installation failed with error:")
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print_available()
        print("\nExample:")
        print("  python setup_llm.py groq       # Install Groq dependencies")
        print("  python setup_llm.py ollama     # Install Ollama dependencies")
        print("  python setup_llm.py all        # Install all dependencies")
        sys.exit(0)
    
    provider = sys.argv[1]
    install_provider(provider)


if __name__ == "__main__":
    main()
