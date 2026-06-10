#!/usr/bin/env bash
set -euo pipefail

export HF_HOME="${HF_HOME:-$HOME/cache/huggingface}"
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-$HOME/cache/modelscope}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"

models=(
  "Qwen/Qwen3.5-0.8B:$HOME/models/Qwen/Qwen3.5-0.8B"
  "Qwen/Qwen3.5-4B:$HOME/models/Qwen/Qwen3.5-4B"
)

mkdir -p "$HOME/models/Qwen" "$HF_HOME" "$MODELSCOPE_CACHE"

for item in "${models[@]}"; do
  repo="${item%%:*}"
  local_dir="${item#*:}"
  echo "Downloading ${repo} -> ${local_dir}"
  if "$HOME/.myenv/bin/python" - "$repo" "$local_dir" <<'PY'; then
import sys
from modelscope import snapshot_download

repo, local_dir = sys.argv[1], sys.argv[2]
snapshot_download(repo, local_dir=local_dir)
print(f"ModelScope download finished: {repo}")
PY
    continue
  fi

  echo "ModelScope failed for ${repo}; falling back to Hugging Face."
  "$HOME/.myenv/bin/huggingface-cli" download "$repo" --local-dir "$local_dir"
done

echo "Done."
