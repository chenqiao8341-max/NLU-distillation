#!/usr/bin/env bash
set -euo pipefail
cd /home/qiao/work/NLU-distillation
PY=/home/qiao/work/lf-env/bin/python3
PORT=8020
BASE_URL=http://127.0.0.1:${PORT}/v1
REPORT_DIR=reports/shortprompt_current
LOG_DIR=experiments/logs/shortprompt_current
mkdir -p "$REPORT_DIR" "$LOG_DIR"
kill_port_server() {
  local pids
  pids=$(pgrep -f "scripts/serve_transformers_openai.py.*--port ${PORT}" || true)
  if [[ -n "$pids" ]]; then
    kill $pids 2>/dev/null || true
    sleep 3
  fi
}
run_one() {
  local size="$1"
  local slug="$2"
  local task="$3"
  local model_path="/home/qiao/work/LLaMA-Factory/saves/qwen3.5-${size}/merged/nlu-prod-${slug}"
  local model_name="qwen35-${size}-${slug}"
  local prefix="${REPORT_DIR}/qwen35_${size//./_}_nlu_prod_${slug//-/_}_shortprompt_current"
  local serve_log="${LOG_DIR}/serve_${size}_${slug}.log"
  local eval_log="${LOG_DIR}/eval_${size}_${slug}.log"
  echo "== START ${model_name} :: ${task} =="
  if [[ -s "${prefix}.json" ]]; then
    echo "skip existing ${prefix}.json"
    return 0
  fi
  test -f scripts/eval_local_openai_shortprompt.py
  test -f "$model_path/config.json"
  kill_port_server
  "$PY" scripts/serve_transformers_openai.py \
    --model-path "$model_path" \
    --served-model-name "$model_name" \
    --host 127.0.0.1 \
    --port "$PORT" \
    --dtype bfloat16 \
    --device-map auto \
    --stop-after-first-json \
    --max-generation-seconds 60 \
    > "$serve_log" 2>&1 &
  local server_pid=$!
  echo "server_pid=${server_pid}" >> "$serve_log"
  for _ in $(seq 1 240); do
    if curl -fsS "$BASE_URL/models" >/dev/null 2>&1; then
      break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
      echo "server failed: ${model_name}" >&2
      tail -160 "$serve_log" >&2 || true
      exit 1
    fi
    sleep 2
  done
  curl -fsS "$BASE_URL/models" >/dev/null
  "$PY" scripts/eval_local_openai_shortprompt.py \
    --base-url "$BASE_URL" \
    --model "$model_name" \
    --dataset-dir /home/qiao/work/nlu-server/eval \
    --tasks "$task" \
    --max-tokens 1024 \
    --timeout 180 \
    --concurrency 1 \
    --output-prefix "$prefix" \
    > "$eval_log" 2>&1
  tail -35 "$eval_log"
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
  sleep 4
  echo "== DONE ${model_name} :: ${task} =="
}
run_one 0.8b author-org 作者和机构
run_one 0.8b data-type data_type
run_one 0.8b org-country 机构和国家
run_one 0.8b time-if 时间和if值
run_one 0.8b topic-keywords topic和keywords
run_one 4b author-org 作者和机构
run_one 4b data-type data_type
run_one 4b org-country 机构和国家
run_one 4b time-if 时间和if值
run_one 4b topic-keywords topic和keywords
kill_port_server
