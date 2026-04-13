#!/usr/bin/env bash
set -euo pipefail

# FinBot Bootstrap — one-command setup for native macOS or Linux.
# Usage: ./scripts/bootstrap.sh [--ci]
#   --ci   Skip interactive onboarding (for CI / automated environments)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CI_MODE=false

for arg in "$@"; do
    case "$arg" in
        --ci|--no-interactive) CI_MODE=true ;;
    esac
done

info()  { printf "\033[1;34m==>\033[0m %s\n" "$1"; }
warn()  { printf "\033[1;33mWARN:\033[0m %s\n" "$1"; }
fail()  { printf "\033[1;31mERROR:\033[0m %s\n" "$1"; exit 1; }
ok()    { printf "\033[1;32m  ✓\033[0m %s\n" "$1"; }

# ---------- Step 0: System requirements ----------

info "Checking system requirements..."

OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin)
        PLATFORM="macos"
        OS_VER="$(sw_vers -productVersion 2>/dev/null || echo "0")"
        MAJOR_VER="${OS_VER%%.*}"
        if [ "$MAJOR_VER" -lt 13 ] 2>/dev/null; then
            fail "macOS 13 (Ventura) or later required. Found: $OS_VER"
        fi
        ok "macOS $OS_VER ($ARCH)"

        RAM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
        RAM_GB=$((RAM_BYTES / 1073741824))
        ;;
    Linux)
        PLATFORM="linux"
        KERNEL="$(uname -r)"
        ok "Linux $KERNEL ($ARCH)"

        RAM_KB="$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')"
        RAM_GB=$((${RAM_KB:-0} / 1048576))
        ;;
    *)
        fail "Unsupported OS: $OS. FinBot supports macOS and Linux."
        ;;
esac

if [ "$RAM_GB" -lt 8 ]; then
    fail "At least 8 GB RAM required. Detected: ${RAM_GB} GB"
elif [ "$RAM_GB" -lt 16 ]; then
    warn "16 GB RAM recommended for good LLM performance. Detected: ${RAM_GB} GB"
else
    ok "${RAM_GB} GB RAM"
fi

DISK_FREE_KB="$(df -k "$PROJECT_DIR" | tail -1 | awk '{print $4}')"
DISK_FREE_GB=$((DISK_FREE_KB / 1048576))
if [ "$DISK_FREE_GB" -lt 10 ]; then
    fail "At least 10 GB free disk space required (model ~4 GB + deps). Available: ${DISK_FREE_GB} GB"
fi
ok "${DISK_FREE_GB} GB free disk space"

# ---------- Step 1: Install Ollama ----------

info "Checking Ollama installation..."

if command -v ollama &>/dev/null; then
    ok "Ollama already installed ($(ollama --version 2>/dev/null || echo 'unknown version'))"
else
    info "Installing Ollama..."
    if [ "$PLATFORM" = "macos" ]; then
        if ! command -v brew &>/dev/null; then
            info "Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    ok "Ollama installed"
fi

# ---------- Step 2: Start Ollama ----------

info "Checking if Ollama is running..."

if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama is already running"
else
    info "Starting Ollama in background..."
    ollama serve &>/dev/null &
    OLLAMA_PID=$!

    RETRIES=0
    while ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
        RETRIES=$((RETRIES + 1))
        if [ "$RETRIES" -gt 15 ]; then
            fail "Ollama did not start within 15 seconds"
        fi
        sleep 1
    done
    ok "Ollama started (PID $OLLAMA_PID)"
fi

# ---------- Step 3: Pull model ----------

info "Pulling LLM model..."
bash "$SCRIPT_DIR/pull-model.sh"

# ---------- Step 4: Python environment ----------

info "Setting up Python environment..."

if ! command -v uv &>/dev/null; then
    info "Installing uv..."
    if [ "$PLATFORM" = "macos" ]; then
        brew install uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    ok "uv installed"
else
    ok "uv already installed"
fi

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    cp .env.example .env
    ok "Created .env from .env.example"
else
    ok ".env already exists"
fi

info "Installing Python dependencies..."
uv sync
ok "Dependencies installed"

# ---------- Step 5: Initialize FinBot ----------

if [ "$CI_MODE" = true ]; then
    info "CI mode — skipping interactive onboarding"
    uv run finbot doctor || true
else
    info "Running FinBot onboarding..."
    uv run finbot setup
    echo
    info "Running health check..."
    uv run finbot doctor
fi

echo
info "Setup complete! Next steps:"
echo "  • Import a statement:   finbot import ~/Downloads/statement.pdf"
echo "  • Launch dashboard:     make dev"
echo "  • Check health:         finbot doctor"
echo
