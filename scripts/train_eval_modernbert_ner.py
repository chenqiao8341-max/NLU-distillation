#!/usr/bin/env python3
"""Train and evaluate ModernBERT token-classification models on BIO task data."""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoConfig,
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)


IGNORE_INDEX = -100
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ["author_org", "org_country", "topic_keywords"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", default=DEFAULT_TASKS)
    parser.add_argument("--model-path", default="/home/chenqr/models/BERT/ModernBERT-base")
    parser.add_argument("--data-root", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "experiments" / "modernbert_ner")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports" / "modernbert_ner")
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--epochs", type=float, default=5.0)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.06)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--logging-steps", type=int, default=20)
    parser.add_argument("--save-total-limit", type=int, default=2)
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=torch.cuda.is_available())
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--overwrite-output-dir", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--predictions-limit", type=int, default=50)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class BioDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], tokenizer: Any, label2id: dict[str, int], max_length: int):
        self.rows = rows
        self.features: list[dict[str, Any]] = []
        for row in rows:
            encoded = tokenizer(
                row["text"],
                truncation=True,
                max_length=max_length,
                return_offsets_mapping=True,
            )
            char_labels = row["char_labels"]
            labels: list[int] = []
            offsets = encoded.pop("offset_mapping")
            for start, end in offsets:
                if start == end:
                    labels.append(IGNORE_INDEX)
                    continue
                span_labels = char_labels[start:end]
                label = next((item for item in span_labels if item != "O"), "O")
                labels.append(label2id[label])
            encoded["labels"] = labels
            self.features.append(encoded)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        return self.features[idx]


def chunks(labels: list[str]) -> set[tuple[str, int, int]]:
    spans: set[tuple[str, int, int]] = set()
    current_type: str | None = None
    start = -1
    for idx, label in enumerate(labels + ["O"]):
        if label.startswith("B-"):
            if current_type is not None:
                spans.add((current_type, start, idx))
            current_type = label[2:]
            start = idx
        elif label.startswith("I-") and current_type == label[2:]:
            continue
        else:
            if current_type is not None:
                spans.add((current_type, start, idx))
            current_type = None
            start = -1
    return spans


def metric_dict(
    pred_rows: list[list[str]],
    true_rows: list[list[str]],
    label_list: list[str],
) -> dict[str, Any]:
    true_chunks = set()
    pred_chunks = set()
    correct_tokens = 0
    total_tokens = 0
    per_type: dict[str, dict[str, int]] = {}

    for row_idx, (pred_labels, true_labels) in enumerate(zip(pred_rows, true_rows)):
        for pred_label, true_label in zip(pred_labels, true_labels):
            correct_tokens += int(pred_label == true_label)
            total_tokens += 1
        row_true = {(row_idx, *span) for span in chunks(true_labels)}
        row_pred = {(row_idx, *span) for span in chunks(pred_labels)}
        true_chunks.update(row_true)
        pred_chunks.update(row_pred)
        for _, entity, _, _ in row_true:
            per_type.setdefault(entity, {"tp": 0, "pred": 0, "true": 0})["true"] += 1
        for _, entity, _, _ in row_pred:
            per_type.setdefault(entity, {"tp": 0, "pred": 0, "true": 0})["pred"] += 1
        for _, entity, _, _ in row_true & row_pred:
            per_type.setdefault(entity, {"tp": 0, "pred": 0, "true": 0})["tp"] += 1

    tp = len(true_chunks & pred_chunks)
    precision = tp / len(pred_chunks) if pred_chunks else 0.0
    recall = tp / len(true_chunks) if true_chunks else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    by_entity: dict[str, dict[str, float | int]] = {}
    for entity, counts in sorted(per_type.items()):
        ent_precision = counts["tp"] / counts["pred"] if counts["pred"] else 0.0
        ent_recall = counts["tp"] / counts["true"] if counts["true"] else 0.0
        ent_f1 = 2 * ent_precision * ent_recall / (ent_precision + ent_recall) if ent_precision + ent_recall else 0.0
        by_entity[entity] = {
            **counts,
            "precision": ent_precision,
            "recall": ent_recall,
            "f1": ent_f1,
        }
    return {
        "token_accuracy": correct_tokens / total_tokens if total_tokens else 0.0,
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": f1,
        "entity_true_count": len(true_chunks),
        "entity_pred_count": len(pred_chunks),
        "entity_tp_count": tp,
        "label_list": label_list,
        "by_entity": by_entity,
    }


def make_compute_metrics(id2label: dict[int, str], label_list: list[str]):
    def compute_metrics(eval_pred: Any) -> dict[str, float]:
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        pred_rows: list[list[str]] = []
        true_rows: list[list[str]] = []
        for pred_row, label_row in zip(preds, labels):
            pred_labels: list[str] = []
            true_labels: list[str] = []
            for pred_id, label_id in zip(pred_row, label_row):
                if int(label_id) == IGNORE_INDEX:
                    continue
                pred_labels.append(id2label[int(pred_id)])
                true_labels.append(id2label[int(label_id)])
            pred_rows.append(pred_labels)
            true_rows.append(true_labels)
        metrics = metric_dict(pred_rows, true_rows, label_list)
        return {key: value for key, value in metrics.items() if isinstance(value, float)}

    return compute_metrics


def training_args_kwargs(args: argparse.Namespace, output_dir: Path) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "output_dir": str(output_dir),
        "seed": args.seed,
        "logging_strategy": "steps",
        "logging_steps": args.logging_steps,
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "num_train_epochs": args.epochs,
        "weight_decay": args.weight_decay,
        "warmup_ratio": args.warmup_ratio,
        "load_best_model_at_end": True,
        "metric_for_best_model": "entity_f1",
        "greater_is_better": True,
        "save_total_limit": args.save_total_limit,
        "report_to": [],
        "overwrite_output_dir": args.overwrite_output_dir,
        "bf16": bool(args.bf16),
    }
    parameters = inspect.signature(TrainingArguments.__init__).parameters
    if "eval_strategy" in parameters:
        kwargs["eval_strategy"] = "epoch"
    else:
        kwargs["evaluation_strategy"] = "epoch"
    kwargs["save_strategy"] = "epoch"
    return {key: value for key, value in kwargs.items() if key in parameters}


def decode_prediction_rows(predictions: np.ndarray, labels: np.ndarray, id2label: dict[int, str]) -> tuple[list[list[str]], list[list[str]]]:
    pred_ids = np.argmax(predictions, axis=-1)
    pred_rows: list[list[str]] = []
    true_rows: list[list[str]] = []
    for pred_row, label_row in zip(pred_ids, labels):
        pred_labels: list[str] = []
        true_labels: list[str] = []
        for pred_id, label_id in zip(pred_row, label_row):
            if int(label_id) == IGNORE_INDEX:
                continue
            pred_labels.append(id2label[int(pred_id)])
            true_labels.append(id2label[int(label_id)])
        pred_rows.append(pred_labels)
        true_rows.append(true_labels)
    return pred_rows, true_rows


def write_report(report_path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# ModernBERT NER - {payload['task']}",
        "",
        f"- model_path: {payload['model_path']}",
        f"- model_dir: {payload['model_dir']}",
        f"- data_dir: {payload['data_dir']}",
        f"- generated_at: {payload['generated_at']}",
        f"- train_samples: {payload['train_samples']}",
        f"- valid_samples: {payload['valid_samples']}",
        f"- test_samples: {payload['test_samples']}",
        "",
        "## Test Metrics",
        "",
        "```json",
        json.dumps(payload["test_metrics"], ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_task(task: str, args: argparse.Namespace) -> dict[str, Any]:
    data_dir = args.data_root / task / "bio"
    output_dir = args.output_root / task
    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    label_list = json.loads((data_dir / "label_list.json").read_text(encoding="utf-8"))
    label2id = {label: idx for idx, label in enumerate(label_list)}
    id2label = {idx: label for label, idx in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    train_rows = read_jsonl(data_dir / "train.jsonl")
    valid_rows = read_jsonl(data_dir / "valid.jsonl")
    test_rows = read_jsonl(data_dir / "test.jsonl")
    train_ds = BioDataset(train_rows, tokenizer, label2id, args.max_length)
    valid_ds = BioDataset(valid_rows, tokenizer, label2id, args.max_length)
    test_ds = BioDataset(test_rows, tokenizer, label2id, args.max_length)

    config = AutoConfig.from_pretrained(
        args.model_path,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
    )
    if hasattr(config, "reference_compile"):
        config.reference_compile = False

    model_source = str(output_dir) if args.skip_train else args.model_path
    model = AutoModelForTokenClassification.from_pretrained(
        model_source,
        config=config,
        ignore_mismatched_sizes=not args.skip_train,
    )
    trainer_kwargs: dict[str, Any] = {
        "model": model,
        "args": TrainingArguments(**training_args_kwargs(args, output_dir)),
        "train_dataset": train_ds,
        "eval_dataset": valid_ds,
        "data_collator": DataCollatorForTokenClassification(tokenizer=tokenizer),
        "compute_metrics": make_compute_metrics(id2label, label_list),
    }
    trainer_params = inspect.signature(Trainer.__init__).parameters
    if "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    elif "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    trainer = Trainer(**trainer_kwargs)

    if not args.skip_train:
        trainer.train()
        trainer.save_model(str(output_dir))
        tokenizer.save_pretrained(str(output_dir))
        for name in ["label_list.json", "stats.json"]:
            src = data_dir / name
            if src.exists():
                shutil.copy2(src, output_dir / name)

    prediction_output = trainer.predict(test_ds)
    pred_rows, true_rows = decode_prediction_rows(prediction_output.predictions, prediction_output.label_ids, id2label)
    test_metrics = metric_dict(pred_rows, true_rows, label_list)
    payload = {
        "task": task,
        "model_path": args.model_path,
        "model_dir": str(output_dir.resolve()),
        "data_dir": str(data_dir.resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "train_samples": len(train_rows),
        "valid_samples": len(valid_rows),
        "test_samples": len(test_rows),
        "test_metrics": test_metrics,
        "trainer_test_metrics": {k: float(v) for k, v in prediction_output.metrics.items()},
    }
    json_path = report_dir / f"{task}_modernbert_ner.json"
    md_path = report_dir / f"{task}_modernbert_ner.md"
    pred_path = report_dir / f"{task}_modernbert_ner_predictions.jsonl"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(md_path, payload)
    with pred_path.open("w", encoding="utf-8") as f:
        for row, pred_labels, true_labels in zip(test_rows[: args.predictions_limit], pred_rows, true_rows):
            f.write(json.dumps({"text": row["text"], "pred_labels": pred_labels, "true_labels": true_labels}, ensure_ascii=False) + "\n")

    print(json.dumps({"task": task, "report": str(json_path), "metrics": test_metrics}, ensure_ascii=False, indent=2))
    del trainer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return payload


def main() -> None:
    args = parse_args()
    summaries = [run_task(task, args) for task in args.tasks]
    summary_path = args.report_dir / "modernbert_ner_summary.json"
    summary_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
