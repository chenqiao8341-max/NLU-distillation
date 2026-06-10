#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/qiao/work/NLU-distillation"
LF_ROOT="/home/qiao/work/LLaMA-Factory"

COMMON_ARGS=(
  --project-root "$ROOT"
  --llamafactory-root "$LF_ROOT"
  --nlu-evaluator-root "/home/qiao/work/nlu-evaluator"
  --nlu-server-root "/home/qiao/work/nlu-server"
  --train-python "/home/qiao/work/lf-env/bin/python3"
  --eval-python "/home/qiao/work/lf-env/bin/python3"
  --llamafactory-cli "/home/qiao/work/lf-env/bin/llamafactory-cli"
  --gpu "${CUDA_VISIBLE_DEVICES:-0}"
  --port "${NLU_LONGPROMPT_PORT:-8000}"
  --config-variant longprompt
  --report-subdir longprompt
  --eval-script "$ROOT/scripts/eval_local_openai_longprompt.py"
)

cd "$ROOT"

python3 scripts/maintenance/run_qwen35_nlu_pipeline.py \
  --model-size 0.8b \
  "${COMMON_ARGS[@]}"

python3 scripts/maintenance/run_qwen35_nlu_pipeline.py \
  --model-size 4b \
  "${COMMON_ARGS[@]}"
