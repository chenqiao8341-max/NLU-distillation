#!/usr/bin/env python3
"""Evaluate an author/org ModernBERT model on nlu-server eval JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NLU_BERT_ROOT = Path.home() / "work" / "nlu-bert"
if str(DEFAULT_NLU_BERT_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_NLU_BERT_ROOT))

from scripts.predict_author_org import AuthorOrgPredictor  # noqa: E402


FIELDS = ["author_name", "author_name英文变体", "author_institution"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", default=str(Path.home() / "work" / "nlu-bert" / "outputs" / "modernbert-author-org-ner"))
    parser.add_argument("--dataset", default=str(Path.home() / "work" / "nlu-server" / "eval" / "作者和机构.json"))
    parser.add_argument("--output-prefix", default=str(PROJECT_ROOT / "reports" / "modernbert_ner" / "author_org_business_eval"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--show-raw-samples", type=int, default=0)
    return parser.parse_args()


def clean_field_name(key: str) -> str:
    return str(key).replace("-标准答案", "").replace("标准答案", "").strip()


def load_eval_dataset(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
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
            normalized[clean_field_name(key)] = value
        dataset.append(normalized)
        if limit is not None and len(dataset) >= limit:
            break
    return dataset


def is_empty(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def normalize_scalar(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[\s\-_.,;:，；：]+", "", text)


def split_multi_values(value: Any) -> list[str] | None:
    text = str(value or "").strip()
    if not text:
        return []
    if "<variant>" in text and "</variant>" in text:
        parts = re.findall(r"<variant>(.*?)</variant>", text, flags=re.S | re.I)
        return [normalize_scalar(part) for part in parts if str(part).strip()]
    if "；" not in text and ";" not in text and "\n" not in text:
        return None
    parts = [part.strip() for part in re.split(r"[；;\n]+", text) if part.strip()]
    return [normalize_scalar(part) for part in parts]


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
    pred_text = normalize_scalar(pred)
    gold_text = normalize_scalar(gold)
    return pred_text in gold_text or gold_text in pred_text


def tokenize(value: Any) -> list[str]:
    return re.findall(r"\b\w+\b", str(value or "").lower())


def f1_score(pred: Any, gold: Any) -> tuple[float, float, float]:
    if is_empty(pred) and is_empty(gold):
        return 1.0, 1.0, 1.0
    if is_empty(pred) or is_empty(gold):
        return 0.0, 0.0, 0.0
    pred_tokens = set(tokenize(pred))
    gold_tokens = set(tokenize(gold))
    if not pred_tokens and not gold_tokens:
        return 1.0, 1.0, 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0, 0.0, 0.0
    overlap = pred_tokens & gold_tokens
    precision = len(overlap) / len(pred_tokens)
    recall = len(overlap) / len(gold_tokens)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def evaluate(records: list[dict[str, Any]]) -> dict[str, Any]:
    field_metrics: dict[str, dict[str, list[float | bool]]] = {
        field: {"em": [], "partial": [], "precision": [], "recall": [], "f1": []}
        for field in FIELDS
    }
    null_total = 0
    null_correct = 0
    for record in records:
        pred = record["parsed_output"]
        gold = record["ground_truth"]
        for field in FIELDS:
            pred_val = pred.get(field, "")
            gold_val = gold.get(field, "")
            pred_empty = is_empty(pred_val)
            gold_empty = is_empty(gold_val)
            if pred_empty and gold_empty:
                null_total += 1
                null_correct += 1
                continue
            if gold_empty:
                null_total += 1
            em = exact_match(pred_val, gold_val)
            pm = partial_match(pred_val, gold_val)
            precision, recall, f1 = f1_score(pred_val, gold_val)
            field_metrics[field]["em"].append(em)
            field_metrics[field]["partial"].append(pm)
            field_metrics[field]["precision"].append(precision)
            field_metrics[field]["recall"].append(recall)
            field_metrics[field]["f1"].append(f1)

    metrics: dict[str, Any] = {}
    all_em: list[bool] = []
    all_partial: list[bool] = []
    all_f1: list[float] = []
    for field in FIELDS:
        values = field_metrics[field]
        prefix = field.replace("_", "-")
        metrics[f"{prefix}-EM"] = sum(values["em"]) / len(values["em"]) if values["em"] else 0.0
        metrics[f"{prefix}-Partial"] = sum(values["partial"]) / len(values["partial"]) if values["partial"] else 0.0
        metrics[f"{prefix}-Precision"] = sum(values["precision"]) / len(values["precision"]) if values["precision"] else 0.0
        metrics[f"{prefix}-Recall"] = sum(values["recall"]) / len(values["recall"]) if values["recall"] else 0.0
        metrics[f"{prefix}-F1"] = sum(values["f1"]) / len(values["f1"]) if values["f1"] else 0.0
        all_em.extend(bool(v) for v in values["em"])
        all_partial.extend(bool(v) for v in values["partial"])
        all_f1.extend(float(v) for v in values["f1"])
    metrics["Average-EM"] = sum(all_em) / len(all_em) if all_em else 0.0
    metrics["Average-Partial"] = sum(all_partial) / len(all_partial) if all_partial else 0.0
    metrics["Average-F1"] = sum(all_f1) / len(all_f1) if all_f1 else 0.0
    metrics["Null-accuracy"] = null_correct / null_total if null_total else 0.0
    return metrics


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# ModernBERT Author/Org Business Evaluation",
        "",
        f"- model_dir: {payload['model_dir']}",
        f"- dataset: {payload['dataset']}",
        f"- generated_at: {payload['generated_at']}",
        f"- total_samples: {payload['total_samples']}",
        "",
        "## Metrics",
        "",
        "```json",
        json.dumps(payload["metrics"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Notes",
        "",
        "- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.",
        "- `author_name英文变体` is generated after BERT extracts `author_name`.",
        "- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    columns = ["query"]
    for field in FIELDS:
        columns.extend([f"GT_{field}", f"PRED_{field}"])
    columns.extend(["raw_output", "parsed_output"])
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = {"query": record["query"]}
            for field in FIELDS:
                row[f"GT_{field}"] = record["ground_truth"].get(field, "")
                row[f"PRED_{field}"] = record["parsed_output"].get(field, "")
            row["raw_output"] = json.dumps(record["raw_output"], ensure_ascii=False)
            row["parsed_output"] = json.dumps(record["parsed_output"], ensure_ascii=False)
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    out_prefix = Path(args.output_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    dataset = load_eval_dataset(Path(args.dataset), args.limit)
    predictor = AuthorOrgPredictor(args.model_dir, max_length=args.max_length)

    records: list[dict[str, Any]] = []
    for idx, row in enumerate(dataset, 1):
        prediction = predictor.predict(row["query"])
        parsed = {field: prediction.get(field, "") for field in FIELDS}
        raw = {"data": {"result": parsed}}
        record = {
            "query": row["query"],
            "ground_truth": {field: row.get(field, "") for field in FIELDS},
            "raw_output": raw,
            "parsed_output": parsed,
        }
        records.append(record)
        if args.show_raw_samples and idx <= args.show_raw_samples:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        if idx % 10 == 0 or idx == len(dataset):
            print(f"作者和机构: {idx}/{len(dataset)}")

    payload = {
        "model": "modernbert-author-org-ner",
        "model_dir": str(Path(args.model_dir).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_samples": len(dataset),
        "metrics": evaluate(records),
        "samples": records,
    }
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    csv_path = out_prefix.with_name(out_prefix.name + "_details").with_suffix(".csv")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    write_csv(csv_path, records)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"CSV: {csv_path}")
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
