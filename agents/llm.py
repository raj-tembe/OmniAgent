"""
LLM initialisation for OmniAgent.
Supports multiple LLM providers: Google Gemini, OpenAI, Groq, Ollama, HuggingFace.
Cached as a singleton — calling llm() multiple times returns the same instance.
"""
import os
import functools
from typing import Union
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import provider-specific modules
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# HuggingFace imports (handled gracefully if not installed)
try:
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    from langchain_huggingface.llms import HuggingFacePipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Ollama imports (handled gracefully if not installed)
try:
    from langchain_ollama import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from config import (
    LLM_PROVIDER, LLM_TEMPERATURE,
    GEMINI_MODEL, GEMINI_API_KEY,
    OPENAI_MODEL, OPENAI_API_KEY,
    GROQ_MODEL, GROQ_API_KEY,
    OLLAMA_MODEL, OLLAMA_BASE_URL,
    HF_MODEL, HF_API_KEY, HF_DEVICE, HF_LOCAL_REPO
)


class LLMInitializationError(Exception):
    """Raised when LLM initialization fails."""
    pass


def _init_gemini():
    """Initialize Google Gemini LLM."""
    if not GEMINI_API_KEY:
        raise LLMInitializationError(
            "GEMINI_API_KEY is not set. Add GOOGLE_GEMINI_API_KEY to your .env file."
        )
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=LLM_TEMPERATURE
    )


def _init_openai():
    """Initialize OpenAI LLM."""
    if not OPENAI_API_KEY:
        raise LLMInitializationError(
            "OPENAI_API_KEY is not set. Add OPENAI_API_KEY to your .env file."
        )
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=LLM_TEMPERATURE
    )


def _init_groq():
    """Initialize Groq LLM."""
    if not GROQ_API_KEY:
        raise LLMInitializationError(
            "GROQ_API_KEY is not set. Add GROQ_API_KEY to your .env file."
        )
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=LLM_TEMPERATURE
    )


def _init_ollama():
    """Initialize Ollama LLM (local inference)."""
    if not OLLAMA_AVAILABLE:
        raise LLMInitializationError(
            "Ollama not installed. Install with: pip install langchain-ollama"
        )
    
    try:
        # Test connection
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE
        )
        return llm
    except Exception as e:
        raise LLMInitializationError(
            f"Failed to connect to Ollama at {OLLAMA_BASE_URL}. "
            f"Ensure Ollama is running with: ollama serve\nError: {e}"
        )


def _init_huggingface_cloud():
    """Initialize HuggingFace cloud-based LLM (via API)."""
    if not HF_AVAILABLE:
        raise LLMInitializationError(
            "HuggingFace not installed. Install with: pip install langchain-huggingface"
        )
    
    if not HF_API_KEY:
        raise LLMInitializationError(
            "HF_API_KEY is not set. Add HF_API_KEY to your .env file. "
            "Get a token at: https://huggingface.co/settings/tokens"
        )
    
    endpoint = HuggingFaceEndpoint(
        repo_id=HF_MODEL,
        huggingfacehub_api_token=HF_API_KEY,
        temperature=LLM_TEMPERATURE
    )
    
    return ChatHuggingFace(llm=endpoint)


def _init_huggingface_local():
    """Initialize HuggingFace local model (requires transformers & torch)."""
    if not HF_AVAILABLE:
        raise LLMInitializationError(
            "HuggingFace not installed. Install with: pip install langchain-huggingface"
        )
    
    try:
        from transformers import pipeline
        
        # Create local repo directory
        repo_path = Path(HF_LOCAL_REPO)
        repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline
        pipe = pipeline(
            "text-generation",
            model=HF_MODEL,
            device=0 if HF_DEVICE == "cuda" else -1,  # 0 for GPU, -1 for CPU
            model_kwargs={"cache_dir": str(repo_path)}
        )
        
        llm = HuggingFacePipeline(
            model_id=HF_MODEL,
            task="text-generation",
            pipeline=pipe
        )
        return llm
    except ImportError as e:
        raise LLMInitializationError(
            f"HuggingFace local model requires transformers and torch. "
            f"Install with: pip install transformers torch\nError: {e}"
        )
    except Exception as e:
        raise LLMInitializationError(
            f"Failed to initialize HuggingFace local model {HF_MODEL}. "
            f"Error: {e}"
        )


@functools.lru_cache(maxsize=1)
def llm() -> Union[
    ChatGoogleGenerativeAI, ChatOpenAI, ChatGroq, OllamaLLM, ChatHuggingFace, 
    "HuggingFacePipeline"
]:
    """
    Return a cached LLM instance based on LLM_PROVIDER config.
    
    Supported providers:
    - "gemini": Google Gemini API (requires GOOGLE_GEMINI_API_KEY)
    - "openai": OpenAI API (requires OPENAI_API_KEY)
    - "groq": Groq API (requires GROQ_API_KEY)
    - "ollama": Local Ollama inference (requires Ollama running on localhost:11434)
    - "huggingface_local": Local HuggingFace model (requires transformers, torch)
    - "huggingface_cloud": HuggingFace inference API (requires HF_API_KEY)
    
    Raises LLMInitializationError if initialization fails.
    """
    provider = LLM_PROVIDER.lower().strip()
    
    if provider == "gemini":
        return _init_gemini()
    elif provider == "openai":
        return _init_openai()
    elif provider == "groq":
        return _init_groq()
    elif provider == "ollama":
        return _init_ollama()
    elif provider == "huggingface_local":
        return _init_huggingface_local()
    elif provider == "huggingface_cloud":
        return _init_huggingface_cloud()
    else:
        raise LLMInitializationError(
            f"Unknown LLM_PROVIDER: {provider}. "
            f"Supported providers: gemini, openai, groq, ollama, huggingface_local, huggingface_cloud"
        )