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
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
    },
    "openai": {
        "packages": ["langchain-openai"],
        "description": "OpenAI API",
        "env_vars": ["OPENAI_API_KEY"],
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
    },
    "groq": {
        "packages": ["langchain-groq"],
        "description": "Groq API",
        "env_vars": ["GROQ_API_KEY"],
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "ollama": {
        "packages": ["langchain-ollama"],
        "description": "Ollama Local Inference",
        "env_vars": [],
        "model_env": "OLLAMA_MODEL",
        "default_model": "mistral",
    },
    "huggingface_local": {
        "packages": ["langchain-huggingface", "transformers", "torch"],
        "description": "HuggingFace Local Models",
        "env_vars": [],
        "model_env": "HF_MODEL",
        "default_model": "mistralai/Mistral-7B-Instruct-v0.1",
    },
    "huggingface_cloud": {
        "packages": ["langchain-huggingface"],
        "description": "HuggingFace Cloud API",
        "env_vars": ["HF_API_KEY"],
        "model_env": "HF_MODEL",
        "default_model": "mistralai/Mistral-7B-Instruct-v0.1",
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
        "model_env": None,
        "default_model": None,
    }
}

ENV_PATH = Path(".env")


def print_available():
    """Print available providers."""
    print("\nAvailable providers:")
    for provider in PROVIDER_DEPS:
        info = PROVIDER_DEPS[provider]
        print(f"  • {provider:20} - {info['description']}")


def load_env_file(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def update_env_file(path: Path, updates: dict) -> None:
    existing = []
    if path.exists():
        existing = path.read_text().splitlines()

    remaining = updates.copy()
    output_lines = []

    for line in existing:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output_lines.append(line)
            continue

        key = line.split("=", 1)[0].strip()
        if key in remaining:
            output_lines.append(f"{key}={remaining.pop(key)}")
        else:
            output_lines.append(line)

    for key, value in remaining.items():
        output_lines.append(f"{key}={value}")

    path.write_text("\n".join(output_lines).strip() + "\n")


def prompt_for_model(provider: str, model_env: str, default_model: str, current_model: str) -> str:
    prompt_value = current_model or default_model or ""
    if prompt_value:
        prompt = (f"Enter model name for {provider.title()} "
                  f"(current: {prompt_value}) and press Enter to keep it: ")
    else:
        prompt = f"Enter model name for {provider.title()}: "

    model_name = input(prompt).strip()
    if not model_name:
        return prompt_value
    return model_name


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
        subprocess.run(cmd, check=True)
        
        print(f"\n✓ Successfully installed {provider} dependencies!\n")

        env_updates = {"LLM_PROVIDER": provider}
        if info.get("model_env"):
            current_env = load_env_file(ENV_PATH)
            current_model = current_env.get(info["model_env"], info.get("default_model", ""))
            chosen_model = prompt_for_model(
                provider,
                info["model_env"],
                info.get("default_model", ""),
                current_model,
            )
            env_updates[info["model_env"]] = chosen_model

        update_env_file(ENV_PATH, env_updates)
        print(f"Updated {ENV_PATH} with: {', '.join(f'{k}={v}' for k, v in env_updates.items())}\n")

        # Show next steps
        if info["env_vars"]:
            print("Next steps:")
            print(f"1. Edit .env file (copy from .env.example if needed)")
            print(f"2. Set these environment variables:")
            for var in info["env_vars"]:
                print(f"   - {var}")
            print(f"3. Confirm LLM_PROVIDER={provider} and model settings in .env")
        else:
            print("Next steps:")
            print(f"1. Confirm LLM_PROVIDER={provider} and model settings in .env")

        if provider == "ollama":
            print("\nAdditional steps for Ollama:")
            print("   - Download from: https://ollama.ai")
            print("   - Run: ollama serve")
            print("   - In another terminal: ollama pull mistral")
        
        if provider == "huggingface_local":
            print("\nAdditional note for HuggingFace local:")
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
