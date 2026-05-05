# Local Models Directory

This directory stores local LLM models for offline use.

## Gemma4 Models

### Option 1: Using Ollama (Recommended)
```bash
# Install Ollama: https://ollama.com/download
# Pull Gemma4 models:
ollama pull gemma4:8b      # ~5GB, fast, good for most tasks
ollama pull gemma4:27b     # ~17GB, better quality, needs 32GB+ RAM
```

### Option 2: Download GGUF files manually
Place GGUF files in this directory:

| Model | Size | Min RAM | Download |
|---|---|---|---|
| gemma-4-8b-Q4_K_M.gguf | ~5GB | 8GB | [HuggingFace](https://huggingface.co/google/gemma-4-8b-gguf) |
| gemma-4-27b-Q4_K_M.gguf | ~17GB | 32GB | [HuggingFace](https://huggingface.co/google/gemma-4-27b-gguf) |

### Using with Ollama
```bash
# Create custom model from GGUF
ollama create gemma4-8b-custom -f Modelfile

# Modelfile content:
# FROM ./models/gemma-4-8b-Q4_K_M.gguf
# PARAMETER temperature 0.7
# PARAMETER top_p 0.9
```

## Other Supported Models

| Model | Provider | Notes |
|---|---|---|
| GPT-4 | OpenAI | API key required |
| Claude 3.5 | Anthropic | API key required |
| Gemini Pro | Google | API key required |
| Qwen2 | Alibaba | API key required |

## Configuration

Set the model in the web UI Settings page or in `settings.json`:
```json
{
  "llm": {
    "provider": "ollama",
    "model": "gemma4:8b",
    "endpoint": "http://localhost:11434"
  }
}
```
