#!/usr/bin/env bash
set -euo pipefail

log_dir="$HOME/logs/nlu-train"
mkdir -p "$log_dir"

job0_config="${1:-my_configs/qwen3.5_0.8b_lora_sft_nlu_data_type_prod.yaml}"
job1_config="${2:-my_configs/qwen3.5_4b_lora_sft_nlu_author_org_prod.yaml}"

ts="$(date +%Y%m%d_%H%M%S)"

echo "GPU 0: ${job0_config}"
nohup "$HOME/work/NLU-distillation/scripts/remote/train_nlu_lora.sh" "$job0_config" 0 \
  > "$log_dir/gpu0_${ts}.log" 2>&1 &
echo "$!" > "$log_dir/gpu0_${ts}.pid"

echo "GPU 1: ${job1_config}"
nohup "$HOME/work/NLU-distillation/scripts/remote/train_nlu_lora.sh" "$job1_config" 1 \
  > "$log_dir/gpu1_${ts}.log" 2>&1 &
echo "$!" > "$log_dir/gpu1_${ts}.pid"

echo "Logs:"
echo "  $log_dir/gpu0_${ts}.log"
echo "  $log_dir/gpu1_${ts}.log"
