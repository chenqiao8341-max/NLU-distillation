#!/usr/bin/env python3
"""
Evaluate local OpenAI-compatible NLU models with the same long prompt used by SFT.

This runner keeps evaluation inside this repository and uses the current SFT
instruction from data/processed_longprompt/<task>/sft/all.jsonl:

  user = instruction + "\n" + query

That matches LLaMA-Factory's Alpaca conversion for the long-prompt training data.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]

TASK_FILES = {
    "data_type": "data_type.json",
    "作者和机构": "作者和机构.json",
    "机构和国家": "机构和国家.json",
    "时间和if值": "时间和if值.json",
    "topic和keywords": "topic和keywords.json",
}

TASK_SLUGS = {
    "data_type": "data_type",
    "作者和机构": "author_org",
    "机构和国家": "org_country",
    "时间和if值": "time_if",
    "topic和keywords": "topic_keywords",
}

DATE_FIELDS = {"filter_start_datetime", "filter_end_datetime"}
DATE_LIKE_FIELDS = DATE_FIELDS | {"研究开始时间范围", "研究结束时间范围", "研究更新时间范围"}
IF_LIKE_FIELDS = {"filter_start_if", "filter_end_if"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="长 prompt 本地 OpenAI-compatible NLU 评测")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", default="qwen-3.5")
    parser.add_argument("--dataset-dir", default="/home/qiao/work/nlu-server/eval")
    parser.add_argument("--tasks", nargs="*", choices=sorted(TASK_FILES), default=list(TASK_FILES))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--rate-limit", type=float, default=0.0)
    parser.add_argument("--output-prefix")
    parser.add_argument("--no-xlsx", action="store_true")
    parser.add_argument("--keep-excel-date-serial", action="store_true")
    parser.add_argument("--show-raw-samples", type=int, default=0)
    parser.add_argument(
        "--message-style",
        choices=["alpaca-user", "system-user"],
        default="alpaca-user",
        help="alpaca-user matches current SFT; system-user is available for comparison.",
    )
    return parser.parse_args()


def clean_field_name(key: str) -> str:
    name = str(key).strip()
    name = name.replace("-标准答案", "")
    name = name.replace("标准答案", "")
    return name


def excel_serial_to_iso(value: Any) -> Any:
    text = str(value).strip() if value is not None else ""
    if not re.fullmatch(r"\d{4,5}", text):
        return value
    serial = int(text)
    if serial < 20000 or serial > 60000:
        return value
    return (date(1899, 12, 30) + timedelta(days=serial)).isoformat()


def load_offline_dataset(path: Path, keep_excel_date_serial: bool = False) -> list[dict[str, Any]]:
    raw_rows = json.loads(path.read_text(encoding="utf-8"))
    dataset: list[dict[str, Any]] = []
    for row in raw_rows:
        query = row.get("query") or row.get("question") or row.get("用户query")
        if not query:
            continue
        normalized: dict[str, Any] = {"query": str(query).strip()}
        for key, value in row.items():
            if key in {"query", "question", "用户query"}:
                continue
            field = clean_field_name(key)
            if not keep_excel_date_serial and field in DATE_FIELDS:
                value = excel_serial_to_iso(value)
            normalized[field] = value
        dataset.append(normalized)
    return dataset


def fields_for_dataset(dataset: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for row in dataset:
        for key in row:
            if key == "query" or key in seen:
                continue
            seen.append(key)
    return seen


def load_long_instruction(task_type: str) -> str:
    slug = TASK_SLUGS[task_type]
    path = ROOT / "data" / "processed_longprompt" / slug / "sft" / "all.jsonl"
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            instruction = str(row.get("instruction") or "").strip()
            if instruction:
                return instruction
    raise ValueError(f"cannot load SFT instruction for task: {task_type}")


def extract_json_text(content: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", str(content), flags=re.S).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def normalize_scalar(value: Any) -> str:
    text = str(value).strip().lower()
    return re.sub(r"[\s\-_.,;:，；：]+", "", text)


def normalize_date_like_value(text: str) -> str:
    normalized = re.sub(r"\s+", "", str(text).strip())
    match = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", normalized)
    if not match:
        return normalized
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def normalize_if_like_value(text: str) -> str:
    normalized = str(text).strip()
    try:
        number = Decimal(normalized)
    except (InvalidOperation, ValueError):
        return normalized
    if number == number.to_integral():
        return str(int(number))
    return format(number.normalize(), "f").rstrip("0").rstrip(".")


def normalize_field_value(field: str, value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return ""
    if field in DATE_LIKE_FIELDS:
        return normalize_date_like_value(text)
    if field in IF_LIKE_FIELDS:
        return normalize_if_like_value(text)
    return value


def is_empty(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def split_multi_values(value: Any) -> list[str] | None:
    text = str(value or "").strip()
    if not text:
        return []
    if "<variant>" in text and "</variant>" in text:
        parts = re.findall(r"<variant>(.*?)</variant>", text, flags=re.S)
        return [normalize_scalar(p) for p in parts if str(p).strip()]
    if "；" not in text and ";" not in text and "\n" not in text:
        return None
    parts = [p.strip() for p in re.split(r"[；;\n]+", text) if p.strip()]
    return [normalize_scalar(p) for p in parts if p]


def exact_match(pred: Any, gold: Any) -> bool:
    if is_empty(pred) and is_empty(gold):
        return True
    if is_empty(pred) or is_empty(gold):
        return False
    pred_vals = split_multi_values(pred)
    gold_vals = split_multi_values(gold)
    if pred_vals is not None or gold_vals is not None:
        return set(pred_vals or []) == set(gold_vals or [])
    return normalize_scalar(pred) == normalize_scalar(gold)


def partial_match(pred: Any, gold: Any) -> bool:
    if is_empty(pred) and is_empty(gold):
        return True
    if is_empty(pred) or is_empty(gold):
        return False
    pred_vals = split_multi_values(pred)
    gold_vals = split_multi_values(gold)
    if pred_vals is not None or gold_vals is not None:
        pred_set = set(pred_vals or [])
        gold_set = set(gold_vals or [])
        if not pred_set and not gold_set:
            return True
        if not pred_set or not gold_set:
            return False
        return bool(pred_set & gold_set)
    pred_str = normalize_scalar(pred)
    gold_str = normalize_scalar(gold)
    return pred_str in gold_str or gold_str in pred_str


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def compute_f1(pred: Any, gold: Any) -> tuple[float, float, float]:
    if is_empty(pred) and is_empty(gold):
        return 1.0, 1.0, 1.0
    if is_empty(pred) or is_empty(gold):
        return 0.0, 0.0, 0.0
    pred_tokens = set(tokenize(str(pred)))
    gold_tokens = set(tokenize(str(gold)))
    if not pred_tokens and not gold_tokens:
        return 1.0, 1.0, 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0, 0.0, 0.0
    overlap = pred_tokens & gold_tokens
    precision = len(overlap) / len(pred_tokens)
    recall = len(overlap) / len(gold_tokens)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def evaluate_predictions(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    fields: list[str],
) -> dict[str, float]:
    metrics: dict[str, dict[str, list[float | bool]]] = {}
    for field in fields:
        metrics[field] = {
            "content_exact_match": [],
            "content_partial_match": [],
            "content_precision": [],
            "content_recall": [],
            "content_f1": [],
        }

    null_total = 0
    null_correct = 0
    for pred, gt in zip(predictions, ground_truth):
        for field in fields:
            pred_val = normalize_field_value(field, pred.get(field, ""))
            gt_val = normalize_field_value(field, gt.get(field, ""))
            pred_empty = is_empty(pred_val)
            gt_empty = is_empty(gt_val)
            em = exact_match(pred_val, gt_val)
            if pred_empty and gt_empty:
                null_total += 1
                null_correct += 1
                continue
            if gt_empty:
                null_total += 1
            pm = partial_match(pred_val, gt_val)
            precision, recall, f1 = compute_f1(pred_val, gt_val)
            metrics[field]["content_exact_match"].append(em)
            metrics[field]["content_partial_match"].append(pm)
            metrics[field]["content_precision"].append(precision)
            metrics[field]["content_recall"].append(recall)
            metrics[field]["content_f1"].append(f1)

    results: dict[str, float] = {}
    all_em: list[float] = []
    all_partial: list[float] = []
    all_f1: list[float] = []
    for field in fields:
        prefix = field.replace("-标准答案", "").replace("_", "-")
        em_vals = [float(x) for x in metrics[field]["content_exact_match"]]
        partial_vals = [float(x) for x in metrics[field]["content_partial_match"]]
        precision_vals = [float(x) for x in metrics[field]["content_precision"]]
        recall_vals = [float(x) for x in metrics[field]["content_recall"]]
        f1_vals = [float(x) for x in metrics[field]["content_f1"]]
        results[f"{prefix}-EM"] = sum(em_vals) / len(em_vals) if em_vals else 0.0
        results[f"{prefix}-Partial"] = sum(partial_vals) / len(partial_vals) if partial_vals else 0.0
        results[f"{prefix}-Precision"] = sum(precision_vals) / len(precision_vals) if precision_vals else 0.0
        results[f"{prefix}-Recall"] = sum(recall_vals) / len(recall_vals) if recall_vals else 0.0
        results[f"{prefix}-F1"] = sum(f1_vals) / len(f1_vals) if f1_vals else 0.0
        all_em.extend(em_vals)
        all_partial.extend(partial_vals)
        all_f1.extend(f1_vals)
    results["Average-EM"] = sum(all_em) / len(all_em) if all_em else 0.0
    results["Average-Partial"] = sum(all_partial) / len(all_partial) if all_partial else 0.0
    results["Average-F1"] = sum(all_f1) / len(all_f1) if all_f1 else 0.0
    results["Null-accuracy"] = null_correct / null_total if null_total else 0.0
    return results


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?```$", stripped, flags=re.S)
    if match:
        return match.group(1).strip()
    return stripped


def extract_json_prefix_scalar_fields(text: str, keys: Iterable[str]) -> dict[str, Any]:
    text = strip_code_fence(text or "")
    if not text or "{" not in text:
        return {}
    recovered: dict[str, Any] = {}
    for key in keys:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', text, flags=re.S)
        if not match:
            continue
        try:
            recovered[key] = json.loads(f'"{match.group(1)}"')
        except Exception:
            recovered[key] = match.group(1).replace(r"\"", '"').replace(r"\\", "\\")
    return recovered


def parse_prediction(api_response: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    if "error" in api_response:
        return {"error": api_response["error"], "raw": api_response}

    data = api_response.get("data", {})
    result = data.get("result", data) if isinstance(data, dict) else api_response.get("result", {})
    if isinstance(result, dict):
        parsed = dict(result)
    elif isinstance(result, str):
        text = strip_code_fence(result)
        try:
            loaded = json.loads(text)
            parsed = loaded if isinstance(loaded, dict) else {"value": loaded}
        except Exception:
            parsed = extract_json_prefix_scalar_fields(text, fields)
            parsed["raw_text"] = result
    else:
        parsed = {}

    if "result" in parsed and isinstance(parsed["result"], list):
        merged: dict[str, Any] = {}
        for item in parsed["result"]:
            if isinstance(item, dict):
                for key, value in item.items():
                    if is_empty(merged.get(key)):
                        merged[key] = value
                    elif not is_empty(value):
                        merged[key] = f"{merged[key]}；{value}"
        parsed.update(merged)

    if "author_nameVariants" in parsed and "author_name英文变体" not in parsed:
        variants = parsed.get("author_nameVariants")
        if isinstance(variants, list):
            parsed["author_name英文变体"] = "\n".join(f"<variant>{v}</variant>" for v in variants if str(v).strip())
        else:
            parsed["author_name英文变体"] = variants

    return parsed


class LocalChatClient:
    def __init__(self, base_url: str, model: str, timeout: int, temperature: float, max_tokens: int, message_style: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.message_style = message_style
        self.session = requests.Session()
        self.session.trust_env = False

    def clone(self) -> "LocalChatClient":
        return LocalChatClient(self.base_url, self.model, self.timeout, self.temperature, self.max_tokens, self.message_style)

    def predict(self, instruction: str, query: str) -> dict[str, Any]:
        if self.message_style == "system-user":
            messages = [{"role": "system", "content": instruction}, {"role": "user", "content": query}]
        else:
            messages = [{"role": "user", "content": f"{instruction}\n{query}"}]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        try:
            resp = self.session.post(f"{self.base_url}/chat/completions", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            body = resp.json()
            content = body["choices"][0]["message"].get("content", "")
            return {"data": {"result": extract_json_text(content)}, "raw_openai": body}
        except Exception as exc:
            return {"error": str(exc), "query": query}


def evaluate_task(
    client: LocalChatClient,
    task_type: str,
    dataset: list[dict[str, Any]],
    rate_limit: float,
    show_raw_samples: int,
    concurrency: int,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    fields = fields_for_dataset(dataset)
    instruction = load_long_instruction(task_type)
    total = len(dataset)
    records: list[dict[str, Any] | None] = [None] * total

    def build_record(item: dict[str, Any], local_client: LocalChatClient) -> dict[str, Any]:
        raw = local_client.predict(instruction, item["query"])
        parsed = parse_prediction(raw, fields)
        return {
            "query": item["query"],
            "ground_truth": {k: v for k, v in item.items() if k != "query"},
            "raw_output": raw,
            "parsed_output": parsed,
        }

    if concurrency <= 1:
        for idx, item in enumerate(dataset, 1):
            record = build_record(item, client)
            records[idx - 1] = record
            if show_raw_samples and idx <= show_raw_samples:
                print(json.dumps(record, ensure_ascii=False, indent=2))
            if idx % 10 == 0 or idx == total:
                print(f"  {task_type}: {idx}/{total}")
            if rate_limit:
                time.sleep(rate_limit)
    else:
        completed = 0
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {executor.submit(build_record, item, client.clone()): idx for idx, item in enumerate(dataset)}
            for future in as_completed(futures):
                idx = futures[future]
                record = future.result()
                records[idx] = record
                completed += 1
                if show_raw_samples and idx < show_raw_samples:
                    print(json.dumps(record, ensure_ascii=False, indent=2))
                if completed % 10 == 0 or completed == total:
                    print(f"  {task_type}: {completed}/{total}")

    finalized = [r for r in records if r is not None]
    metrics = evaluate_predictions([r["parsed_output"] for r in finalized], dataset, fields)
    return metrics, finalized


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['model']} long-prompt local NLU evaluation",
        "",
        f"- base_url: {payload['base_url']}",
        f"- generated_at: {payload['generated_at']}",
        f"- message_style: {payload['message_style']}",
        f"- total_samples: {payload['total_samples']}",
        "",
        "## Overall",
        "",
        "```json",
        json.dumps(payload["overall_metrics"], ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    for task in payload["tasks"]:
        lines.extend(
            [
                f"## {task['task_type']}",
                "",
                f"- samples: {task['sample_count']}",
                "",
                "```json",
                json.dumps(task["metrics"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv_details(path: Path, records: list[dict[str, Any]]) -> None:
    value_headers: list[str] = []
    seen = set()
    for record in records:
        for source in (record.get("ground_truth", {}), record.get("parsed_output", {})):
            for key in source.keys():
                if key in {"raw", "raw_text", "error"} or key in seen:
                    continue
                seen.add(key)
                value_headers.append(key)

    columns = ["task_type", "query"]
    columns += [f"GT_{h}" for h in value_headers]
    columns += [f"PRED_{h}" for h in value_headers]
    columns += ["raw_output", "parsed_output"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            gt = record.get("ground_truth", {})
            pred = record.get("parsed_output", {})
            row = {"task_type": record.get("task_type", ""), "query": record.get("query", "")}
            for h in value_headers:
                row[f"GT_{h}"] = gt.get(h, "")
                row[f"PRED_{h}"] = pred.get(h, "")
            row["raw_output"] = json.dumps(record.get("raw_output", {}), ensure_ascii=False)
            row["parsed_output"] = json.dumps(pred, ensure_ascii=False)
            writer.writerow(row)


def average_task_metrics(task_payloads: list[dict[str, Any]]) -> dict[str, float]:
    keys = ["Average-EM", "Average-Partial", "Average-F1", "Null-accuracy"]
    result: dict[str, float] = {}
    for key in keys:
        vals = [float(t["metrics"].get(key, 0.0)) for t in task_payloads if "metrics" in t]
        result[key] = sum(vals) / len(vals) if vals else 0.0
    return result


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model)
    out_prefix = Path(args.output_prefix) if args.output_prefix else ROOT / "reports" / "longprompt" / f"local_{safe_model}_{timestamp}"
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    client = LocalChatClient(args.base_url, args.model, args.timeout, args.temperature, args.max_tokens, args.message_style)
    task_payloads: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []

    for task_type in args.tasks:
        dataset_path = dataset_dir / TASK_FILES[task_type]
        dataset = load_offline_dataset(dataset_path, keep_excel_date_serial=args.keep_excel_date_serial)
        if args.limit:
            dataset = dataset[: args.limit]
        print(f"\n== {task_type} ({len(dataset)} samples) ==")
        metrics, records = evaluate_task(
            client,
            task_type,
            dataset,
            args.rate_limit,
            args.show_raw_samples,
            max(1, args.concurrency),
        )
        task_payloads.append({"task_type": task_type, "sample_count": len(dataset), "metrics": metrics, "samples": records})
        for record in records:
            all_records.append({"task_type": task_type, **record})

    payload = {
        "model": args.model,
        "base_url": args.base_url,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "message_style": args.message_style,
        "total_samples": sum(t["sample_count"] for t in task_payloads),
        "overall_metrics": average_task_metrics(task_payloads),
        "tasks": task_payloads,
    }

    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    csv_path = out_prefix.with_name(out_prefix.name + "_details").with_suffix(".csv")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    write_csv_details(csv_path, all_records)
    print(f"\nJSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
