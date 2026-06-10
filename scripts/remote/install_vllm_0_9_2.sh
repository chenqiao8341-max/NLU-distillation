#!/usr/bin/env bash
set -euo pipefail

env_dir="$HOME/vllm-env"
log_dir="$HOME/logs"

mkdir -p "$log_dir"

if [[ ! -x "$env_dir/bin/python" ]]; then
  "$HOME/.myenv/bin/python" -m venv "$env_dir"
fi

"$env_dir/bin/python" -m pip install --upgrade pip
"$env_dir/bin/pip" install vllm==0.9.2
"$env_dir/bin/python" - <<'PY'
import vllm
print("vllm", vllm.__version__)
PY
