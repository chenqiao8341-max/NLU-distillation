#!/usr/bin/env bash
set -euo pipefail

echo "== GPU =="
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader

echo "== LLaMA-Factory =="
"$HOME/.myenv/bin/llamafactory-cli" version

echo "== vLLM =="
"$HOME/vllm-env/bin/python" - <<'PY'
import vllm
print("vllm", vllm.__version__)
PY

echo "== NLU datasets =="
cd "$HOME/work/LLaMA-Factory"
for name in nlu_author_org_prod_sft nlu_org_country_prod_sft nlu_time_if_prod_sft nlu_data_type_prod_sft nlu_topic_keywords_prod_sft; do
  file="data/${name}.jsonl"
  printf "%-32s %s\n" "$name" "$(wc -l < "$file")"
done
