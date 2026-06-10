#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/chenqr/work/NLU-distillation}"
LF_ROOT="${LF_ROOT:-/home/chenqr/work/LLaMA-Factory}"
MODEL_SIZE="${1:-4b}"
GPU="${2:-0}"
PORT="${3:-8000}"

COMMON_ARGS=(
  --project-root "$ROOT"
  --llamafactory-root "$LF_ROOT"
  --nlu-evaluator-root "/home/chenqr/work/nlu-evaluator"
  --nlu-server-root "/home/chenqr/work/nlu-server"
  --train-python "/home/chenqr/.myenv/bin/python"
  --eval-python "/home/chenqr/.myenv/bin/python"
  --llamafactory-cli "/home/chenqr/.myenv/bin/llamafactory-cli"
  --gpu "$GPU"
  --port "$PORT"
  --config-variant longprompt
  --report-subdir longprompt
  --eval-script "$ROOT/scripts/eval_local_openai_longprompt.py"
)

cd "$ROOT"
python3 scripts/maintenance/run_qwen35_nlu_pipeline.py \
  --model-size "$MODEL_SIZE" \
  "${COMMON_ARGS[@]}"
