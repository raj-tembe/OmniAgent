"""
LLM initialisation for OmniAgent.
Supports multiple LLM providers: Google Gemini, OpenAI, Groq, Ollama, HuggingFace.
Cached as a singleton — calling llm() multiple times returns the same instance.
"""
import functools
import os
from pathlib import Path
from typing import TYPE_CHECKING, Union

from dotenv import load_dotenv

load_dotenv()

# Import provider-specific modules
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    OPENAI_AVAILABLE = False

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    ChatGroq = None
    GROQ_AVAILABLE = False

# HuggingFace imports (handled gracefully if not installed)
try:
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    from langchain_huggingface.llms import HuggingFacePipeline
    HF_AVAILABLE = True
except ImportError:
    HuggingFaceEndpoint = None
    ChatHuggingFace = None
    HuggingFacePipeline = None
    HF_AVAILABLE = False

# Ollama imports (handled gracefully if not installed)
try:
    from langchain_ollama import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OllamaLLM = None
    OLLAMA_AVAILABLE = False

if TYPE_CHECKING:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_openai import ChatOpenAI
    from langchain_groq import ChatGroq
    from langchain_ollama import OllamaLLM
    from langchain_huggingface import ChatHuggingFace
    from langchain_huggingface.llms import HuggingFacePipeline

from config import (
    LLM_PROVIDER, LLM_TEMPERATURE,
    GEMINI_MODEL,
    OPENAI_MODEL,
    GROQ_MODEL,
    OLLAMA_MODEL, OLLAMA_BASE_URL,
    HF_MODEL, HF_DEVICE, HF_LOCAL_REPO,
)


class LLMInitializationError(Exception):
    """Raised when LLM initialization fails."""
    pass


def _init_gemini():
    """Initialize Google Gemini LLM."""
    gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not gemini_api_key or gemini_api_key.startswith("your_"):
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add GOOGLE_GEMINI_API_KEY to your .env file."
        )
    os.environ["GOOGLE_API_KEY"] = gemini_api_key
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=LLM_TEMPERATURE
    )


def _init_openai():
    """Initialize OpenAI LLM."""
    if not OPENAI_AVAILABLE:
        raise LLMInitializationError(
            "OpenAI support is not installed. Install with: pip install langchain-openai"
        )
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key or openai_api_key.startswith("your_"):
        raise LLMInitializationError(
            "OPENAI_API_KEY is not set. Add OPENAI_API_KEY to your .env file."
        )
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=openai_api_key,
        temperature=LLM_TEMPERATURE
    )


def _init_groq():
    """Initialize Groq LLM."""
    if not GROQ_AVAILABLE:
        raise LLMInitializationError(
            "Groq support is not installed. Install with: pip install langchain-groq"
        )
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key or groq_api_key.startswith("your_"):
        raise LLMInitializationError(
            "GROQ_API_KEY is not set. Add GROQ_API_KEY to your .env file."
        )
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=groq_api_key,
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

    huggingface_api_key = os.getenv("HF_API_KEY")
    if not huggingface_api_key or huggingface_api_key.startswith("your_"):
        raise LLMInitializationError(
            "HF_API_KEY is not set. Add HF_API_KEY to your .env file. "
            "Get a token at: https://huggingface.co/settings/tokens"
        )

    endpoint = HuggingFaceEndpoint(
        repo_id=HF_MODEL,
        huggingfacehub_api_token=huggingface_api_key,
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


@functools.lru_cache(maxsize=32)
def _get_cached_llm(
    provider: str,
    gemini_api_key: str,
    openai_api_key: str,
    groq_api_key: str,
    hf_api_key: str,
    ollama_model: str,
    ollama_base_url: str,
    hf_model: str,
    hf_device: str,
    hf_local_repo: str,
    temperature: str,
):
    if provider == "gemini":
        return _init_gemini()
    if provider == "openai":
        return _init_openai()
    if provider == "groq":
        return _init_groq()
    if provider == "ollama":
        return _init_ollama()
    if provider == "huggingface_local":
        return _init_huggingface_local()
    if provider == "huggingface_cloud":
        return _init_huggingface_cloud()
    raise LLMInitializationError(
        f"Unknown LLM_PROVIDER: {provider}. "
        f"Supported providers: gemini, openai, groq, ollama, huggingface_local, huggingface_cloud"
    )


def llm() -> Union[
    "ChatGoogleGenerativeAI",
    "ChatOpenAI",
    "ChatGroq",
    "OllamaLLM",
    "ChatHuggingFace",
    "HuggingFacePipeline",
]:
    """Return a cached LLM instance based on the current provider configuration."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower().strip()
    return _get_cached_llm(
        provider,
        os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY"),
        os.getenv("OPENAI_API_KEY"),
        os.getenv("GROQ_API_KEY"),
        os.getenv("HF_API_KEY"),
        os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
        os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
        os.getenv("HF_MODEL", HF_MODEL),
        os.getenv("HF_DEVICE", HF_DEVICE),
        os.getenv("HF_LOCAL_REPO", HF_LOCAL_REPO),
        str(LLM_TEMPERATURE),
    )