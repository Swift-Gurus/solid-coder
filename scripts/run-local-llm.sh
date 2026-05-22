#!/usr/bin/env bash
# Start llama-server using settings from .claude/solid-coder-local.toml.
#
# Usage:
#   ./scripts/run-local-llm.sh
#
# All settings live in .claude/solid-coder-local.toml [server] section.
# Edit that file — no env vars needed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read a value from the [server] section of the TOML config.
# Falls back to the supplied default if the file or key is absent.
cfg() {
    python3 "$SCRIPT_DIR/config_get.py" server "$1" "$2"
}

# ── Load settings ─────────────────────────────────────────────────────────────

LLAMA_MODEL=$(cfg model     "Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf")
LLAMA_PORT=$(cfg  port      "8080")
LLAMA_CTX=$(cfg   ctx_size  "32768")
LLAMA_GPU=$(cfg   gpu_layers "99")
LLAMA_PAR=$(cfg   parallel  "1")

# ── Locate model ──────────────────────────────────────────────────────────────

MODEL_PATH=$(find "$HOME/.cache/huggingface" -name "$LLAMA_MODEL" 2>/dev/null | head -1)

if [[ -z "$MODEL_PATH" ]]; then
  echo "error: model not found: $LLAMA_MODEL"
  echo ""
  echo "Available models in ~/.cache/huggingface:"
  find "$HOME/.cache/huggingface" -name "*.gguf" 2>/dev/null \
    | grep -v mmproj \
    | sed 's|.*/||' \
    | sort
  exit 1
fi

# ── Print configuration ───────────────────────────────────────────────────────

echo "llama-server  (settings from .claude/solid-coder-local.toml)"
echo "  model       : $(basename "$MODEL_PATH")"
echo "  port        : $LLAMA_PORT"
echo "  context     : $LLAMA_CTX tokens"
echo "  gpu layers  : $LLAMA_GPU"
echo "  parallel    : $LLAMA_PAR"
echo ""
echo "Other available models (edit [server] model in the TOML to switch):"
find "$HOME/.cache/huggingface" -name "*.gguf" 2>/dev/null \
  | grep -v mmproj \
  | sed 's|.*/||' \
  | grep -v "$(basename "$MODEL_PATH")" \
  | sort \
  | sed 's/^/  /'
echo ""
echo "Starting..."
echo ""

# ── Launch ────────────────────────────────────────────────────────────────────

exec llama-server \
  --model        "$MODEL_PATH" \
  --port         "$LLAMA_PORT" \
  --ctx-size     "$LLAMA_CTX" \
  --n-gpu-layers "$LLAMA_GPU" \
  --parallel     "$LLAMA_PAR" \
  --flash-attn   on \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --jinja \
  --reasoning    off
