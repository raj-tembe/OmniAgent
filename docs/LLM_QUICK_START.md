# OmniAgent LLM Provider Quick Reference

## Installation

```bash
# Install dependencies for your chosen provider
python setup_llm.py groq              # Groq (fastest)
python setup_llm.py gemini            # Gemini (default)
python setup_llm.py openai            # OpenAI (GPT-4)
python setup_llm.py ollama            # Ollama (local)
python setup_llm.py huggingface_local # HuggingFace (local)
python setup_llm.py all               # All providers
```

## Configuration

```bash
# Copy template
cp .env.example .env

# Edit .env and set:
LLM_PROVIDER=your_choice          # Provider name
LLM_TEMPERATURE=0.6               # 0.0-1.0

# Add provider-specific credentials
GOOGLE_GEMINI_API_KEY=...        # For Gemini
OPENAI_API_KEY=...               # For OpenAI
GROQ_API_KEY=...                 # For Groq
HF_API_KEY=...                   # For HuggingFace Cloud
```

## Testing

```bash
# Show configuration
python -m agents.llm_utils config

# Test current provider
python -m agents.llm_utils test

# List all providers
python -m agents.llm_utils list
```

## Providers at a Glance

| Provider | Speed | Cost | Setup | Command |
|----------|-------|------|-------|---------|
| **Groq** | ⭐⭐⭐⭐⭐ | Free/$ | 2 min | `setup_llm.py groq` |
| **Gemini** | ⭐⭐⭐⭐ | $$ | 2 min | `setup_llm.py gemini` |
| **OpenAI** | ⭐⭐⭐ | $$$$ | 2 min | `setup_llm.py openai` |
| **HF Cloud** | ⭐⭐⭐⭐ | $ | 2 min | `setup_llm.py huggingface_cloud` |
| **Ollama** | ⭐⭐⭐ | Free | 10 min | `setup_llm.py ollama` |
| **HF Local** | ⭐⭐ | Free | 20 min | `setup_llm.py huggingface_local` |

## Detailed Setup

### Groq (Recommended - Fastest & Free)
```bash
python setup_llm.py groq
# 1. Get key: https://console.groq.com/keys
# 2. Edit .env: GROQ_API_KEY=your_key, LLM_PROVIDER=groq
# 3. Done!
```

### Gemini (Default - Good Balance)
```bash
python setup_llm.py gemini
# 1. Get key: https://aistudio.google.com/app/apikeys
# 2. Edit .env: GOOGLE_GEMINI_API_KEY=your_key, LLM_PROVIDER=gemini
# 3. Done!
```

### OpenAI (GPT-4 Power)
```bash
python setup_llm.py openai
# 1. Get key: https://platform.openai.com/api-keys
# 2. Edit .env: OPENAI_API_KEY=your_key, LLM_PROVIDER=openai
# 3. Edit .env: OPENAI_MODEL=gpt-4o-mini (or gpt-4o, gpt-4, etc.)
# 4. Done!
```

### Ollama (Local - No Costs)
```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Setup OmniAgent
python setup_llm.py ollama
ollama pull mistral  # Download a model
# Edit .env: LLM_PROVIDER=ollama, OLLAMA_MODEL=mistral
# Done!
```

### HuggingFace Local (Private, GPU Recommended)
```bash
python setup_llm.py huggingface_local
# Edit .env:
#   LLM_PROVIDER=huggingface_local
#   HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
#   HF_DEVICE=cuda  (or cpu)
# Done!
```

### HuggingFace Cloud (Easy Cloud)
```bash
python setup_llm.py huggingface_cloud
# 1. Get token: https://huggingface.co/settings/tokens
# 2. Edit .env: HF_API_KEY=your_token, LLM_PROVIDER=huggingface_cloud
# 3. Done!
```

## Switching Providers

Change `LLM_PROVIDER` in `.env` and restart OmniAgent:

```bash
# In .env:
LLM_PROVIDER=groq    # Change this

# Then restart your application
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not set" | Check .env file spelling and values |
| "Connection refused" (Ollama) | Run `ollama serve` in another terminal |
| "Model not found" (Ollama) | Run `ollama pull mistral` |
| "Module not installed" | Run `python setup_llm.py provider_name` |
| "Out of memory" (Local) | Use smaller model or switch to cloud |
| Slow inference | Switch to Groq (fastest), disable GPU if CPU faster |

## Environment Variables Reference

```bash
# Core
LLM_PROVIDER=gemini                          # Provider choice
LLM_TEMPERATURE=0.6                          # 0.0-1.0

# Google Gemini
GOOGLE_GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash

# OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini

# Groq
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama (Local)
OLLAMA_MODEL=mistral
OLLAMA_BASE_URL=http://localhost:11434

# HuggingFace
HF_API_KEY=your_token                       # For cloud only
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
HF_DEVICE=cpu                               # cpu or cuda
HF_LOCAL_REPO=./models/huggingface          # Cache location

# External Services
TAVILY_API_KEY=your_key                     # Web search
SERPAPI_API_KEY=your_key                    # Google search
LANGSMITH_API_KEY=your_key                  # LangChain observability
```

## Full Documentation

See `docs/LLM_PROVIDER_GUIDE.md` for complete details on all providers.

## Support

- 📚 Full Guide: `docs/LLM_PROVIDER_GUIDE.md`
- 🔍 Diagnostics: `python -m agents.llm_utils config`
- 🧪 Test: `python -m agents.llm_utils test`
- 📋 All Providers: `python -m agents.llm_utils list`
