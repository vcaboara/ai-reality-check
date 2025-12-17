# AI Reality Check - Docker Setup

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Pull Ollama model (first time):**
   ```bash
   docker exec ai-reality-check-ollama ollama pull llama3.2:3b
   ```

4. **Access the UI:**
   Open http://localhost:5000

## Configuration

Edit `.env` to configure:
- `OLLAMA_MODEL` - Ollama model to use (default: llama3.2:3b)
- `GEMINI_API_KEY` - Optional: Use Gemini instead of Ollama
- `FLASK_ENV` - production or development

## Recommended Models

**For Technical/Engineering Analysis (Recommended):**
- `qwen2.5-coder:7b` - **Best balanced choice** (8GB RAM)
- `qwen2.5-coder:14b` - Better quality (16GB RAM)
- `qwen2.5-coder:32b` - Highest quality (32GB+ RAM)

**General Purpose (Faster but less technical):**
- `llama3.2:3b` - Fast, general knowledge (4GB RAM)
- `llama3.1:8b` - Good balance (8GB RAM)
- `phi3:mini` - Very fast, limited (2GB RAM)

**Why qwen2.5-coder:** Specifically trained on technical/code content, better at:
- Understanding engineering specifications
- Analyzing technical feasibility
- Identifying material/process constraints

## Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web
docker-compose logs -f ollama

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# List available Ollama models
docker exec ai-reality-check-ollama ollama list

# Pull a different model
docker exec ai-reality-check-ollama ollama pull qwen2.5-coder:7b

# Clean everything (including volumes)
docker-compose down -v
```

## Architecture

- **Web Service**: Flask UI on port 5000
- **Ollama Service**: Local LLM API on port 11434
- **Volumes**: 
  - `ollama_data` - Model storage
  - `./data` - Uploads and results (persisted on host)
  - `./config` - Domain configuration

## Performance Tips

- First analysis is slower (model loading)
- Subsequent analyses are much faster
- Use smaller models (3b-7b) for development
- Use larger models (32b) for production quality

## Troubleshooting

**Web service can't reach Ollama:**
```bash
docker-compose logs ollama
docker exec ai-reality-check-ollama ollama list
```

**Rebuild with fresh dependencies:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Check health:**
```bash
docker-compose ps
```
