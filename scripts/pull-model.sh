#!/usr/bin/env bash
set -euo pipefail

# Pull or switch Ollama models. Works in both native and Docker modes.
# Usage:
#   ./scripts/pull-model.sh                    # pull model from .env
#   ./scripts/pull-model.sh MODEL=llama3:8b    # pull a specific model
#   DOCKER=1 ./scripts/pull-model.sh           # pull inside Docker container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

info()  { printf "\033[1;34m==>\033[0m %s\n" "$1"; }
warn()  { printf "\033[1;33mWARN:\033[0m %s\n" "$1"; }
fail()  { printf "\033[1;31mERROR:\033[0m %s\n" "$1"; exit 1; }
ok()    { printf "\033[1;32m  ✓\033[0m %s\n" "$1"; }

# Determine model name: CLI arg > .env > default
MODEL="${MODEL:-}"
if [ -z "$MODEL" ]; then
    for arg in "$@"; do
        case "$arg" in
            MODEL=*) MODEL="${arg#MODEL=}" ;;
        esac
    done
fi

if [ -z "$MODEL" ] && [ -f "$PROJECT_DIR/.env" ]; then
    MODEL="$(grep -E '^FINBOT_OLLAMA_MODEL=' "$PROJECT_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
fi

if [ -z "$MODEL" ] && [ -f "$PROJECT_DIR/.env.example" ]; then
    MODEL="$(grep -E '^FINBOT_OLLAMA_MODEL=' "$PROJECT_DIR/.env.example" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
fi

MODEL="${MODEL:-mistral:7b-instruct-v0.3-q4_K_M}"

info "Model: $MODEL"

# Check disk space (~4 GB needed for a 7B Q4 model)
DISK_FREE_KB="$(df -k "$PROJECT_DIR" | tail -1 | awk '{print $4}')"
DISK_FREE_GB=$((DISK_FREE_KB / 1048576))
if [ "$DISK_FREE_GB" -lt 5 ]; then
    warn "Only ${DISK_FREE_GB} GB free disk space. Model download is typically 3-5 GB."
    warn "The pull may fail if there is not enough space."
fi

# Detect Docker mode
DOCKER="${DOCKER:-}"
if [ -n "$DOCKER" ] || [ "${FINBOT_DOCKER:-}" = "1" ]; then
    info "Docker mode — pulling inside Ollama container..."

    if ! docker compose ps ollama 2>/dev/null | grep -q "running"; then
        fail "Ollama container is not running. Start it with: docker compose --profile full up -d"
    fi

    docker compose exec ollama ollama pull "$MODEL"
else
    if ! command -v ollama &>/dev/null; then
        fail "Ollama is not installed. Run: make setup"
    fi

    if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        fail "Ollama is not running. Start it with: ollama serve"
    fi

    # Check if model is already pulled
    if ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
        ok "Model already available"
    else
        warn "Downloading model (~4 GB). This may take several minutes on slow connections."
        ollama pull "$MODEL"
    fi
fi

# Validate
if [ -z "$DOCKER" ]; then
    if ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
        ok "Model '$MODEL' is ready"
    else
        fail "Model pull appeared to fail — '$MODEL' not found in ollama list"
    fi
else
    if docker compose exec ollama ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
        ok "Model '$MODEL' is ready in container"
    else
        fail "Model pull appeared to fail inside container"
    fi
fi
