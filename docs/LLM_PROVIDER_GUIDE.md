# Multi-LLM Support Guide

OmniAgent now supports multiple LLM providers. Switch providers by changing the `LLM_PROVIDER` environment variable in your `.env` file.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Select a provider** by setting `LLM_PROVIDER` in `.env`

3. **Add credentials** for your chosen provider

4. **Restart OmniAgent** for changes to take effect

---

## Supported Providers

### 1. **Google Gemini** (Default)
**Provider name:** `gemini`

Best for: High-quality responses, competitive pricing

**Setup:**
```bash
# Get API key from: https://aistudio.google.com/app/apikeys
export GOOGLE_GEMINI_API_KEY=your_key_here
export GEMINI_MODEL=gemini-2.5-flash
export LLM_PROVIDER=gemini
```

**Install dependencies:**
```bash
pip install langchain-google-genai google-generativeai
```

---

### 2. **OpenAI**
**Provider name:** `openai`

Best for: GPT-4 capabilities, reliable API

**Setup:**
```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-4-turbo, gpt-3.5-turbo
export LLM_PROVIDER=openai
```

**Install dependencies:**
```bash
pip install langchain-openai
```

**Supported models:**
- `gpt-4o` - Latest multimodal model
- `gpt-4o-mini` - Smaller, faster variant
- `gpt-4-turbo` - Previous generation turbo model
- `gpt-4` - Original GPT-4
- `gpt-3.5-turbo` - Fast, economical

---

### 3. **Groq**
**Provider name:** `groq`

Best for: Lightning-fast inference, free tier available

**Setup:**
```bash
# Get API key from: https://console.groq.com/keys
export GROQ_API_KEY=your_key_here
export GROQ_MODEL=mixtral-8x7b-32768
export LLM_PROVIDER=groq
```

**Install dependencies:**
```bash
pip install langchain-groq
```

**Supported models:**
- `mixtral-8x7b-32768` - Fast multimodal
- `llama2-70b-4096` - Open source LLaMA 2
- `llama-3-8b-8192` - Smaller LLaMA 3 variant

---

### 4. **Ollama** (Local Inference)
**Provider name:** `ollama`

Best for: Privacy, offline usage, no API costs

**Setup:**

1. **Install Ollama:**
   ```bash
   # macOS/Linux: Download from https://ollama.ai
   # Or: curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama server:**
   ```bash
   ollama serve
   # Runs on http://localhost:11434 by default
   ```

3. **Pull a model:**
   ```bash
   ollama pull mistral      # ~4GB
   ollama pull llama2       # ~4GB
   ollama pull neural-chat  # ~4GB
   ollama pull orca-mini    # ~2GB
   ```

4. **Configure OmniAgent:**
   ```bash
   export OLLAMA_MODEL=mistral
   export OLLAMA_BASE_URL=http://localhost:11434
   export LLM_PROVIDER=ollama
   ```

**Install dependencies:**
```bash
pip install langchain-ollama
```

**Popular Ollama models:**
- `mistral` - Fast and smart
- `llama2` - Open source classic
- `neural-chat` - Conversation optimized
- `orca-mini` - Small and fast
- `dolphin-mixtral` - High quality reasoning

**Check available models:**
```bash
ollama list
```

---

### 5. **HuggingFace Local** (GPU/CPU)
**Provider name:** `huggingface_local`

Best for: Advanced control, on-device inference, customization

**Setup:**

1. **Install dependencies:**
   ```bash
   pip install langchain-huggingface transformers torch
   # GPU support: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Configure OmniAgent:**
   ```bash
   export HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
   export HF_DEVICE=cpu          # or "cuda" for GPU
   export HF_LOCAL_REPO=./models/huggingface
   export LLM_PROVIDER=huggingface_local
   ```

**Recommended models for local use:**
- `mistralai/Mistral-7B-Instruct-v0.1` - 7B params, good quality
- `meta-llama/Llama-2-7b-chat-hf` - 7B params, open source
- `tiiuae/falcon-7b-instruct` - 7B params, fast
- `TheBloke/Mistral-7B-Instruct-v0.1-GGUF` - Quantized, faster

**Hardware requirements (approximate):**
- **7B parameters**: 16GB RAM (CPU) or 4GB VRAM (GPU)
- **13B parameters**: 32GB RAM (CPU) or 8GB VRAM (GPU)

---

### 6. **HuggingFace Cloud** (Inference API)
**Provider name:** `huggingface_cloud`

Best for: No setup required, cloud reliability

**Setup:**

1. **Get API key:**
   - Visit: https://huggingface.co/settings/tokens
   - Create a "Read" access token

2. **Configure OmniAgent:**
   ```bash
   export HF_API_KEY=your_token_here
   export HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
   export LLM_PROVIDER=huggingface_cloud
   ```

3. **Install dependencies:**
   ```bash
   pip install langchain-huggingface
   ```

**Popular models:**
- `mistralai/Mistral-7B-Instruct-v0.1`
- `meta-llama/Llama-2-7b-chat-hf`
- `tiiuae/falcon-7b-instruct`

---

## Switching Between Providers

Change providers anytime by updating `.env`:

```bash
# In .env file
LLM_PROVIDER=ollama    # Local
LLM_PROVIDER=groq      # Cloud (fast)
LLM_PROVIDER=openai    # Cloud (capable)
LLM_PROVIDER=gemini    # Cloud (default)
```

The next time OmniAgent starts, it will use the new provider.

---

## Troubleshooting

### **"API key not set" error**
- Ensure you've added the correct environment variable to `.env`
- The variable name differs per provider (check `.env.example`)

### **"Connection refused" (Ollama)**
- Start the Ollama server: `ollama serve`
- Verify it's running: `curl http://localhost:11434/api/tags`

### **"Model not found" (Ollama)**
- Pull the model first: `ollama pull mistral`
- List available models: `ollama list`

### **Out of memory (HuggingFace local)**
- Use a smaller model (7B instead of 13B)
- Switch to `huggingface_cloud` for cloud inference

### **"Module not installed" errors**
- Install provider-specific dependencies:
  ```bash
  pip install langchain-openai        # For OpenAI
  pip install langchain-groq          # For Groq
  pip install langchain-ollama        # For Ollama
  pip install langchain-huggingface   # For HuggingFace
  ```

---

## Provider Comparison

| Provider | Speed | Cost | Setup | Privacy | Capabilities |
|----------|-------|------|-------|---------|--------------|
| **Gemini** | ⭐⭐⭐⭐ | $$ | Easy | Cloud | Advanced |
| **OpenAI** | ⭐⭐⭐ | $$$ | Easy | Cloud | Excellent |
| **Groq** | ⭐⭐⭐⭐⭐ | $ | Easy | Cloud | Good |
| **Ollama** | ⭐⭐⭐ | Free | Medium | Local | Good |
| **HF Local** | ⭐⭐ | Free | Hard | Local | Basic |
| **HF Cloud** | ⭐⭐⭐⭐ | $ | Easy | Cloud | Good |

---

## Configuration Reference

All LLM provider environment variables:

```bash
# Provider selection
LLM_PROVIDER=gemini                    # Options: gemini, openai, groq, ollama, huggingface_local, huggingface_cloud

# Temperature (0=deterministic, 1=creative)
LLM_TEMPERATURE=0.6

# Google Gemini
GOOGLE_GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash

# OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini

# Groq
GROQ_API_KEY=your_key
GROQ_MODEL=mixtral-8x7b-32768

# Ollama
OLLAMA_MODEL=mistral
OLLAMA_BASE_URL=http://localhost:11434

# HuggingFace
HF_API_KEY=your_token
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
HF_DEVICE=cpu
HF_LOCAL_REPO=./models/huggingface

# External Services
TAVILY_API_KEY=your_key                # Web search integration
SERPAPI_API_KEY=your_key               # Google search integration
LANGSMITH_API_KEY=your_key             # LangChain observability
```

---

## Examples

### Using Gemini (Default)
```bash
export LLM_PROVIDER=gemini
export GOOGLE_GEMINI_API_KEY=AIza...
python main.py
```

### Using Groq (Fastest)
```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_...
python main.py
```

### Using local Ollama
```bash
ollama serve                           # Terminal 1
export LLM_PROVIDER=ollama             # Terminal 2
python main.py
```

### Using GPT-4
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o
python main.py
```

---

## FAQ

**Q: Which provider should I use?**
A: Start with Groq (fastest) or Gemini (best balance). Try others based on your needs.

**Q: Can I switch providers mid-execution?**
A: No, the LLM is cached on startup. Restart OmniAgent to switch.

**Q: Does my data stay private?**
A: Only Ollama and HuggingFace Local keep data on-device. Cloud providers (Gemini, OpenAI, Groq, HF Cloud) send queries to their servers.

**Q: What if I don't have API credentials?**
A: Use Ollama (free, local) or try free tiers from Groq.

**Q: Can I use different models for different tasks?**
A: Not currently, but you can create separate scripts with different `.env` files.
