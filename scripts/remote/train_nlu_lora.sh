#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 my_configs/<config.yaml> [gpu_id]" >&2
  exit 2
fi

config="$1"
gpu="${2:-0}"

export CUDA_VISIBLE_DEVICES="$gpu"
export HF_HOME="${HF_HOME:-$HOME/cache/huggingface}"
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-$HOME/cache/modelscope}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

cd "$HOME/work/LLaMA-Factory"
exec "$HOME/.myenv/bin/llamafactory-cli" train "$config"
