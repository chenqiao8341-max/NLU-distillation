#!/usr/bin/env python3
"""Run NLU LoRA train -> merge -> local OpenAI eval for five tasks."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path


TASKS = [
    ("author_org", "作者和机构", "author-org", "author_org"),
    ("data_type", "data_type", "data-type", "data_type"),
    ("org_country", "机构和国家", "org-country", "org_country"),
    ("time_if", "时间和if值", "time-if", "time_if"),
    ("topic_keywords", "topic和keywords", "topic-keywords", "topic_keywords"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-size", choices=["0.8b", "4b"], required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--llamafactory-root", required=True)
    parser.add_argument("--nlu-evaluator-root", required=True)
    parser.add_argument("--nlu-server-root", required=True)
    parser.add_argument("--train-python", required=True)
    parser.add_argument("--eval-python", required=True)
    parser.add_argument("--llamafactory-cli", required=True)
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--config-variant", default="prod", help="Config/model variant token, e.g. prod or longprompt.")
    parser.add_argument("--train-config-suffix", default="")
    parser.add_argument("--report-subdir", default="clean200")
    parser.add_argument(
        "--eval-script",
        help="Evaluation script path. Defaults to nlu-evaluator/scripts/eval_local_openai.py.",
    )
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-merge", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument(
        "--delete-merged-after-eval",
        action="store_true",
        help="Delete each merged model directory after its eval report is written.",
    )
    parser.add_argument(
        "--start-task",
        choices=[task[0] for task in TASKS],
        help="Start from this task slug and skip earlier tasks.",
    )
    return parser.parse_args()


def run_command(
    cmd: list[str],
    log_path: Path,
    cwd: Path,
    env: dict[str, str],
    status: dict,
    status_path: Path,
    step: str,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    status["current_step"] = step
    status["updated_at"] = int(time.time())
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"{step} failed with rc={rc}; log={log_path}")


def wait_for_server(base_url: str, model: str, timeout: int = 180) -> None:
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{base_url}/models", timeout=5)
            if resp.ok and model in resp.text:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"server not ready: {base_url}")


def terminate_process(proc: subprocess.Popen | None, log_path: Path) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n[server stopped rc={proc.returncode}]\n")


def train_config_name(size: str, task_slug: str, variant: str, suffix: str) -> str:
    if size == "0.8b":
        size_part = "0.8b"
    else:
        size_part = "4b"
    base = f"qwen3.5_{size_part}_lora_sft_nlu_{task_slug}_{variant}"
    if suffix:
        base += suffix
    return base + ".yaml"


def merge_config_name(size: str, task_slug: str, variant: str) -> str:
    size_part = "0.8b" if size == "0.8b" else "4b"
    return f"qwen3.5_{size_part}_lora_sft_nlu_{task_slug}_{variant}_merge.yaml"


def model_dir_size_part(size: str) -> str:
    return "qwen3.5-0.8b" if size == "0.8b" else "qwen3.5-4b"


def max_tokens_for_task(task_slug: str) -> int:
    return 1024 if task_slug == "author_org" else 256


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root)
    lf_root = Path(args.llamafactory_root)
    evaluator_root = Path(args.nlu_evaluator_root)
    server_root = Path(args.nlu_server_root)
    logs_root = project_root / "experiments/logs" / args.report_subdir / args.model_size
    reports_root = project_root / "reports" / args.report_subdir / "merged"
    eval_script = Path(args.eval_script) if args.eval_script else evaluator_root / "scripts/eval_local_openai.py"
    status_path = logs_root / "pipeline_status.json"
    logs_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = args.gpu
    env.setdefault("HF_HOME", str(Path.home() / "cache/huggingface"))
    env.setdefault("MODELSCOPE_CACHE", str(Path.home() / "cache/modelscope"))
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    status = {
        "model_size": args.model_size,
        "started_at": int(time.time()),
        "tasks": {},
    }
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    start_index = 0
    if args.start_task:
        start_index = next(index for index, task in enumerate(TASKS) if task[0] == args.start_task)

    for config_task_slug, task_name, model_task_slug, report_slug in TASKS[start_index:]:
        task_status = {"started_at": int(time.time()), "state": "running"}
        status["tasks"][config_task_slug] = task_status
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        if not args.skip_train:
            cfg = "my_configs/" + train_config_name(
                args.model_size,
                config_task_slug,
                args.config_variant,
                args.train_config_suffix,
            )
            run_command(
                [args.llamafactory_cli, "train", cfg],
                logs_root / f"train_{report_slug}.log",
                lf_root,
                env,
                status,
                status_path,
                f"train:{config_task_slug}",
            )
            task_status["trained_at"] = int(time.time())

        if not args.skip_merge:
            cfg = "my_configs/" + merge_config_name(args.model_size, config_task_slug, args.config_variant)
            run_command(
                [args.llamafactory_cli, "export", cfg],
                logs_root / f"merge_{report_slug}.log",
                lf_root,
                env,
                status,
                status_path,
                f"merge:{config_task_slug}",
            )
            task_status["merged_at"] = int(time.time())

        if not args.skip_eval:
            served_name = f"qwen35-{args.model_size}-nlu-{args.config_variant}-{model_task_slug}"
            merged_path = lf_root / "saves" / model_dir_size_part(args.model_size) / "merged" / f"nlu-{args.config_variant}-{model_task_slug}"
            serve_log = logs_root / f"serve_{report_slug}.log"
            serve_cmd = [
                args.train_python,
                str(project_root / "scripts/serve_transformers_openai.py"),
                "--model-path",
                str(merged_path),
                "--served-model-name",
                served_name,
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
                "--dtype",
                "bfloat16",
                "--stop-after-first-json",
            ]
            server_proc: subprocess.Popen | None = None
            eval_ok = False
            try:
                serve_log.parent.mkdir(parents=True, exist_ok=True)
                serve_fp = serve_log.open("w", encoding="utf-8")
                serve_fp.write("$ " + " ".join(serve_cmd) + "\n")
                serve_fp.flush()
                server_proc = subprocess.Popen(serve_cmd, cwd=str(project_root), env=env, stdout=serve_fp, stderr=subprocess.STDOUT, text=True)
                time.sleep(3)
                wait_for_server(f"http://127.0.0.1:{args.port}/v1", served_name)
                eval_cmd = [
                    args.eval_python,
                    str(eval_script),
                    "--base-url",
                    f"http://127.0.0.1:{args.port}/v1",
                    "--model",
                    served_name,
                    "--dataset-dir",
                    str(server_root / "eval"),
                    "--tasks",
                    task_name,
                    "--concurrency",
                    "1",
                    "--max-tokens",
                    str(max_tokens_for_task(config_task_slug)),
                    "--timeout",
                    "180",
                    "--no-xlsx",
                    "--output-prefix",
                    str(reports_root / f"qwen35_{args.model_size.replace('.', '_')}_nlu_{args.config_variant}_{report_slug}"),
                ]
                run_command(
                    eval_cmd,
                    logs_root / f"eval_{report_slug}.log",
                    eval_script.parent.parent if eval_script.name.startswith("eval_local_openai_") else evaluator_root,
                    env,
                    status,
                    status_path,
                    f"eval:{config_task_slug}",
                )
                task_status["evaluated_at"] = int(time.time())
                eval_ok = True
            finally:
                terminate_process(server_proc, serve_log)
            if eval_ok and args.delete_merged_after_eval and merged_path.exists():
                shutil.rmtree(merged_path)
                task_status["deleted_merged_at"] = int(time.time())
        task_status["state"] = "done"
        task_status["finished_at"] = int(time.time())
        status["updated_at"] = int(time.time())
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    status["state"] = "done"
    status["finished_at"] = int(time.time())
    status["current_step"] = "done"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[pipeline failed] {exc}", file=sys.stderr)
        raise
