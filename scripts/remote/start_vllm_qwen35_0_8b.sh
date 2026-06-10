#!/usr/bin/env bash
set -euo pipefail

export HF_HOME="${HF_HOME:-$HOME/cache/huggingface}"
export VLLM_WORKER_MULTIPROC_METHOD="${VLLM_WORKER_MULTIPROC_METHOD:-spawn}"

model_path="${1:-$HOME/models/Qwen/Qwen3.5-0.8B}"
host="${VLLM_HOST:-0.0.0.0}"
port="${VLLM_PORT:-8000}"
gpu="${CUDA_VISIBLE_DEVICES:-0}"
gpu_memory_utilization="${VLLM_GPU_MEMORY_UTILIZATION:-0.85}"

mkdir -p "$HOME/logs"

echo "Starting vLLM on GPU ${gpu}: ${model_path}"
exec "$HOME/vllm-env/bin/python" -m vllm.entrypoints.openai.api_server \
  --model "$model_path" \
  --served-model-name qwen35-0.8b-nlu \
  --host "$host" \
  --port "$port" \
  --dtype bfloat16 \
  --gpu-memory-utilization "$gpu_memory_utilization" \
  --max-model-len 4096
