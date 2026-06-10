#!/usr/bin/env python3
"""Train ModernBERT on canonical author_org span data and evaluate spans."""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
from collections import defaultdict
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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORE_INDEX = -100
LABEL_LIST = ["O", "B-AUTHOR", "I-AUTHOR", "B-INSTITUTION", "I-INSTITUTION"]
FIELDS = ["author_name", "author_institution"]
FIELD_BY_LABEL = {"AUTHOR": "author_name", "INSTITUTION": "author_institution"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", default="/home/chenqr/models/BERT/ModernBERT-base")
    parser.add_argument("--span-dir", type=Path, default=PROJECT_ROOT / "data" / "processed" / "author_org" / "span")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "experiments" / "modernbert_span_ner" / "author_org")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports" / "modernbert_span_ner")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
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
    parser.add_argument("--predictions-limit", type=int, default=100)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def char_labels_from_entities(text: str, entities: list[dict[str, Any]]) -> list[str]:
    labels = ["O"] * len(text)
    for entity in sorted(entities, key=lambda item: (item["start"], item["end"])):
        start = int(entity["start"])
        end = int(entity["end"])
        label = str(entity["label"])
        if start < 0 or end > len(text) or start >= end:
            continue
        if any(item != "O" for item in labels[start:end]):
            continue
        labels[start] = f"B-{label}"
        for idx in range(start + 1, end):
            labels[idx] = f"I-{label}"
    return labels


class SpanTokenDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], tokenizer: Any, label2id: dict[str, int], max_length: int, stride: int):
        self.rows = rows
        self.features: list[dict[str, Any]] = []
        self.meta: list[dict[str, Any]] = []
        for row_idx, row in enumerate(rows):
            text = row["text"]
            char_labels = char_labels_from_entities(text, row.get("entities", []))
            encoded = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                stride=stride,
                return_overflowing_tokens=True,
                return_offsets_mapping=True,
            )
            overflow_map = encoded.pop("overflow_to_sample_mapping", None)
            input_ids = encoded["input_ids"]
            for feature_idx in range(len(input_ids)):
                offsets = encoded["offset_mapping"][feature_idx]
                labels: list[int] = []
                for start, end in offsets:
                    if start == end:
                        labels.append(IGNORE_INDEX)
                        continue
                    span_labels = char_labels[start:end]
                    label = next((item for item in span_labels if item != "O"), "O")
                    labels.append(label2id[label])
                feature = {key: value[feature_idx] for key, value in encoded.items() if key != "offset_mapping"}
                feature["labels"] = labels
                self.features.append(feature)
                self.meta.append(
                    {
                        "row_idx": row_idx if overflow_map is None else row_idx + int(overflow_map[feature_idx]) * 0,
                        "offsets": offsets,
                    }
                )

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        return self.features[idx]


def labels_to_spans(labels: list[str]) -> set[tuple[str, int, int]]:
    spans: set[tuple[str, int, int]] = set()
    current_label: str | None = None
    start = -1
    for idx, label in enumerate(labels + ["O"]):
        entity = label[2:] if label != "O" else None
        if label.startswith("B-") or entity != current_label:
            if current_label is not None:
                spans.add((current_label, start, idx))
            current_label = entity
            start = idx if entity is not None else -1
    return spans


def entity_metrics(pred: set[tuple[int, str, int, int]], true: set[tuple[int, str, int, int]]) -> dict[str, Any]:
    tp = len(pred & true)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(true) if true else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    by_entity: dict[str, dict[str, Any]] = {}
    for label in sorted({item[1] for item in pred | true}):
        p = {item for item in pred if item[1] == label}
        t = {item for item in true if item[1] == label}
        label_tp = len(p & t)
        label_precision = label_tp / len(p) if p else 0.0
        label_recall = label_tp / len(t) if t else 0.0
        label_f1 = 2 * label_precision * label_recall / (label_precision + label_recall) if label_precision + label_recall else 0.0
        by_entity[label] = {
            "tp": label_tp,
            "pred": len(p),
            "true": len(t),
            "precision": label_precision,
            "recall": label_recall,
            "f1": label_f1,
        }
    return {
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": f1,
        "entity_true_count": len(true),
        "entity_pred_count": len(pred),
        "entity_tp_count": tp,
        "by_entity": by_entity,
    }


def token_metrics(eval_pred: Any, id2label: dict[int, str]) -> dict[str, float]:
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    pred_entities: set[tuple[int, str, int, int]] = set()
    true_entities: set[tuple[int, str, int, int]] = set()
    correct = 0
    total = 0
    for row_idx, (pred_row, label_row) in enumerate(zip(preds, labels)):
        pred_labels: list[str] = []
        true_labels: list[str] = []
        for pred_id, label_id in zip(pred_row, label_row):
            if int(label_id) == IGNORE_INDEX:
                continue
            pred_label = id2label[int(pred_id)]
            true_label = id2label[int(label_id)]
            pred_labels.append(pred_label)
            true_labels.append(true_label)
            correct += pred_label == true_label
            total += 1
        pred_entities.update((row_idx, *span) for span in labels_to_spans(pred_labels))
        true_entities.update((row_idx, *span) for span in labels_to_spans(true_labels))
    metrics = entity_metrics(pred_entities, true_entities)
    return {
        "token_accuracy": correct / total if total else 0.0,
        "entity_f1": float(metrics["entity_f1"]),
        "entity_precision": float(metrics["entity_precision"]),
        "entity_recall": float(metrics["entity_recall"]),
    }


def training_args_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "output_dir": str(args.output_dir),
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
        "save_strategy": "epoch",
    }
    parameters = inspect.signature(TrainingArguments.__init__).parameters
    kwargs["eval_strategy" if "eval_strategy" in parameters else "evaluation_strategy"] = "epoch"
    return {key: value for key, value in kwargs.items() if key in parameters}


def predicted_entities_from_features(
    rows: list[dict[str, Any]],
    dataset: SpanTokenDataset,
    predictions: np.ndarray,
    id2label: dict[int, str],
) -> list[list[dict[str, Any]]]:
    pred_ids = np.argmax(predictions, axis=-1)
    row_entities: list[dict[tuple[str, int, int], dict[str, Any]]] = [dict() for _ in rows]
    for feature_idx, token_ids in enumerate(pred_ids):
        meta = dataset.meta[feature_idx]
        row_idx = meta["row_idx"]
        offsets = meta["offsets"]
        token_labels: list[str] = []
        token_offsets: list[tuple[int, int]] = []
        for pred_id, (start, end) in zip(token_ids, offsets):
            if start == end:
                continue
            token_labels.append(id2label[int(pred_id)])
            token_offsets.append((start, end))
        for label, start_token, end_token in labels_to_spans(token_labels):
            start = token_offsets[start_token][0]
            end = token_offsets[end_token - 1][1]
            if start >= end:
                continue
            key = (label, start, end)
            row_entities[row_idx][key] = {
                "start": start,
                "end": end,
                "text": rows[row_idx]["text"][start:end],
                "label": label,
                "field": FIELD_BY_LABEL.get(label, label),
            }
    return [list(items.values()) for items in row_entities]


def char_labels_to_entities(text: str, labels: list[str]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for label, start, end in sorted(labels_to_spans(labels), key=lambda item: (item[1], item[2], item[0])):
        entities.append(
            {
                "start": start,
                "end": end,
                "text": text[start:end],
                "label": label,
                "field": FIELD_BY_LABEL.get(label, label),
            }
        )
    return entities


def exact_span_metrics(rows: list[dict[str, Any]], pred_entities: list[list[dict[str, Any]]]) -> dict[str, Any]:
    pred: set[tuple[int, str, int, int]] = set()
    true: set[tuple[int, str, int, int]] = set()
    for row_idx, (row, entities) in enumerate(zip(rows, pred_entities)):
        pred.update((row_idx, entity["label"], int(entity["start"]), int(entity["end"])) for entity in entities)
        true.update((row_idx, entity["label"], int(entity["start"]), int(entity["end"])) for entity in row.get("entities", []))
    return entity_metrics(pred, true)


def field_values(entities: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for entity in entities:
        field = str(entity.get("field") or FIELD_BY_LABEL.get(str(entity.get("label")), ""))
        text = str(entity.get("text", "")).strip()
        if field in FIELDS and text and text not in grouped[field]:
            grouped[field].append(text)
    return {field: "；".join(grouped[field]) for field in FIELDS}


def field_metrics(rows: list[dict[str, Any]], pred_entities: list[list[dict[str, Any]]]) -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {field: {"tp": 0, "pred": 0, "true": 0, "exact_match": 0, "rows": 0} for field in FIELDS}
    for row, entities in zip(rows, pred_entities):
        pred_values = field_values(entities)
        true_values = {field: set(str(row.get(field, "")).split("；")) - {""} for field in FIELDS}
        pred_sets = {field: set(pred_values.get(field, "").split("；")) - {""} for field in FIELDS}
        for field in FIELDS:
            counts[field]["rows"] += 1
            counts[field]["tp"] += len(pred_sets[field] & true_values[field])
            counts[field]["pred"] += len(pred_sets[field])
            counts[field]["true"] += len(true_values[field])
            counts[field]["exact_match"] += pred_sets[field] == true_values[field]

    result: dict[str, Any] = {}
    f1s: list[float] = []
    for field, item in counts.items():
        precision = item["tp"] / item["pred"] if item["pred"] else 0.0
        recall = item["tp"] / item["true"] if item["true"] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        result[field] = {
            **item,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "exact_match_rate": item["exact_match"] / item["rows"] if item["rows"] else 0.0,
        }
    result["macro_f1"] = sum(f1s) / len(f1s) if f1s else 0.0
    return result


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# ModernBERT Span NER - author_org",
        "",
        f"- model_path: {payload['model_path']}",
        f"- model_dir: {payload['model_dir']}",
        f"- span_dir: {payload['span_dir']}",
        f"- generated_at: {payload['generated_at']}",
        f"- train_rows: {payload['train_rows']}",
        f"- valid_rows: {payload['valid_rows']}",
        f"- test_rows: {payload['test_rows']}",
        f"- max_length: {payload['max_length']}",
        f"- stride: {payload['stride']}",
        "",
        "## Span Metrics",
        "",
        "```json",
        json.dumps(payload["span_metrics"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Field Metrics",
        "",
        "```json",
        json.dumps(payload["field_metrics"], ensure_ascii=False, indent=2),
        "```",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    label2id = {label: idx for idx, label in enumerate(LABEL_LIST)}
    id2label = {idx: label for label, idx in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    train_rows = read_jsonl(args.span_dir / "train.jsonl")
    valid_rows = read_jsonl(args.span_dir / "valid.jsonl")
    test_rows = read_jsonl(args.span_dir / "test.jsonl")
    train_ds = SpanTokenDataset(train_rows, tokenizer, label2id, args.max_length, args.stride)
    valid_ds = SpanTokenDataset(valid_rows, tokenizer, label2id, args.max_length, args.stride)
    test_ds = SpanTokenDataset(test_rows, tokenizer, label2id, args.max_length, args.stride)

    config = AutoConfig.from_pretrained(args.model_path, num_labels=len(LABEL_LIST), id2label=id2label, label2id=label2id)
    if hasattr(config, "reference_compile"):
        config.reference_compile = False
    model_source = str(args.output_dir) if args.skip_train else args.model_path
    model = AutoModelForTokenClassification.from_pretrained(model_source, config=config, ignore_mismatched_sizes=not args.skip_train)

    trainer_kwargs: dict[str, Any] = {
        "model": model,
        "args": TrainingArguments(**training_args_kwargs(args)),
        "train_dataset": train_ds,
        "eval_dataset": valid_ds,
        "data_collator": DataCollatorForTokenClassification(tokenizer=tokenizer),
        "compute_metrics": lambda eval_pred: token_metrics(eval_pred, id2label),
    }
    trainer_params = inspect.signature(Trainer.__init__).parameters
    if "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    elif "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    trainer = Trainer(**trainer_kwargs)

    if not args.skip_train:
        trainer.train()
        trainer.save_model(str(args.output_dir))
        tokenizer.save_pretrained(str(args.output_dir))
        shutil.copy2(args.span_dir / "stats.json", args.output_dir / "span_stats.json")
        (args.output_dir / "label_list.json").write_text(json.dumps(LABEL_LIST, ensure_ascii=False, indent=2), encoding="utf-8")

    prediction_output = trainer.predict(test_ds)
    pred_entities = predicted_entities_from_features(test_rows, test_ds, prediction_output.predictions, id2label)
    span_metrics = exact_span_metrics(test_rows, pred_entities)
    field_metric_payload = field_metrics(test_rows, pred_entities)
    payload = {
        "model_path": args.model_path,
        "model_dir": str(args.output_dir.resolve()),
        "span_dir": str(args.span_dir.resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "train_rows": len(train_rows),
        "valid_rows": len(valid_rows),
        "test_rows": len(test_rows),
        "train_features": len(train_ds),
        "valid_features": len(valid_ds),
        "test_features": len(test_ds),
        "max_length": args.max_length,
        "stride": args.stride,
        "trainer_test_metrics": {key: float(value) for key, value in prediction_output.metrics.items()},
        "span_metrics": span_metrics,
        "field_metrics": field_metric_payload,
    }
    json_path = args.report_dir / "author_org_modernbert_span_ner.json"
    md_path = args.report_dir / "author_org_modernbert_span_ner.md"
    pred_path = args.report_dir / "author_org_modernbert_span_ner_predictions.jsonl"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    with pred_path.open("w", encoding="utf-8") as f:
        for row, entities in zip(test_rows[: args.predictions_limit], pred_entities[: args.predictions_limit]):
            f.write(json.dumps({"text": row["text"], "gold_entities": row["entities"], "pred_entities": entities}, ensure_ascii=False) + "\n")
    print(json.dumps({"report": str(json_path), "span_metrics": span_metrics, "field_metrics": field_metric_payload}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
