#!/usr/bin/env bash
set -euo pipefail

MODEL_SIZE="${1:-4b}"
GPU="${2:-0}"
PORT="${3:-8000}"
MIN_FREE_MB="${MIN_FREE_MB:-22000}"
CHECK_SECONDS="${CHECK_SECONDS:-300}"
ROOT="${ROOT:-/home/chenqr/work/NLU-distillation}"
LOG_DIR="${ROOT}/experiments/logs/longprompt_remote_wait"
LOCK_DIR="${LOG_DIR}/${MODEL_SIZE}.launch.lock"

mkdir -p "$LOG_DIR"
echo "[$(date -Is)] waiting for GPU ${GPU} free memory >= ${MIN_FREE_MB} MiB" \
  | tee -a "$LOG_DIR/wait_${MODEL_SIZE}_gpu${GPU}.log"

while true; do
  free_mb="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i "$GPU" | head -1 | tr -d ' ')"
  util="$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits -i "$GPU" | head -1 | tr -d ' ')"
  echo "[$(date -Is)] gpu=${GPU} free_mb=${free_mb} util=${util}" \
    | tee -a "$LOG_DIR/wait_${MODEL_SIZE}_gpu${GPU}.log"
  if [[ "$free_mb" =~ ^[0-9]+$ ]] && (( free_mb >= MIN_FREE_MB )); then
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      echo "[$(date -Is)] acquired launch lock ${LOCK_DIR}" \
        | tee -a "$LOG_DIR/wait_${MODEL_SIZE}_gpu${GPU}.log"
      break
    fi
    echo "[$(date -Is)] another ${MODEL_SIZE} launcher already acquired ${LOCK_DIR}; exiting" \
      | tee -a "$LOG_DIR/wait_${MODEL_SIZE}_gpu${GPU}.log"
    exit 0
  fi
  sleep "$CHECK_SECONDS"
done

exec "$ROOT/scripts/remote/run_longprompt_qwen35_remote.sh" "$MODEL_SIZE" "$GPU" "$PORT"
