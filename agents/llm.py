"""
LLM initialisation for OmniAgent.
Uses Google Gemini 2.5 Flash. Cached as a singleton — calling llm() multiple times
returns the same instance.
"""
import os
import functools
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_MODEL, LLM_TEMPERATURE

load_dotenv()

@functools.lru_cache(maxsize=1)
def llm() -> ChatGoogleGenerativeAI:
    """Return a cached LLM instance. Raises EnvironmentError if API key is missing."""
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_GEMINI_API_KEY is not set. Add it to your .env file."
        )
    os.environ["GOOGLE_API_KEY"] = api_key
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=LLM_TEMPERATURE)