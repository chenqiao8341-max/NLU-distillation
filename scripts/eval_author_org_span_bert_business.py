#!/usr/bin/env python3
"""Evaluate the span-trained ModernBERT author/org model on business eval JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NLU_BERT_ROOT = Path.home() / "work" / "nlu-bert"
if str(DEFAULT_NLU_BERT_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_NLU_BERT_ROOT))

try:
    from nlu_bert.author_variants import generate_author_variant_text, load_variant_lexicon
except Exception:  # pragma: no cover - keeps this script usable without nlu-bert.
    generate_author_variant_text = None
    load_variant_lexicon = None


FIELDS = ["author_name", "author_name英文变体", "author_institution"]
ENTITY_FIELDS = ["author_name", "author_institution"]
FIELD_BY_LABEL = {"AUTHOR": "author_name", "INSTITUTION": "author_institution"}

QUERY_PREFIX_RE = re.compile(r"^(?:[◦•·\-\s]+)?(?:请|搜索|查询|查找|列出|找到|输出|由|在|如|关于)+")
AUTHOR_SUFFIX_RE = re.compile(r"(?:教授|医生|医师|主任|院士|课题组|团队|研究者|负责的|牵头|讲课|作为.*)$")
LEADING_ORG_RE = re.compile(r"^.*(?:大学|医院|学院|诊所|研究所|研究院|中心|科室|附属[^A-Za-z\u4e00-\u9fff]*)")
INSTITUTION_TRAILING_RE = re.compile(r"(?:作为|负责|牵头|正在|进行|发起|研究状态|相关|的?所有|有哪些).*$")
ORG_KEYWORDS_RE = re.compile(r"(?:大学|医院|学院|诊所|研究所|研究院|中心|科室|实验室|机构|Clinic|Hospital|University|Institute)", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", default=str(PROJECT_ROOT / "experiments" / "modernbert_span_ner" / "author_org"))
    parser.add_argument("--dataset", default=str(Path.home() / "work" / "nlu-server" / "eval" / "作者和机构.json"))
    parser.add_argument("--output-prefix", default=str(PROJECT_ROOT / "reports" / "modernbert_span_ner" / "author_org_business_eval"))
    parser.add_argument("--variant-lexicon", default=str(DEFAULT_NLU_BERT_ROOT / "outputs" / "modernbert-author-org-ner" / "author_variant_lexicon.json"))
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--limit", type=int)
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


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def clean_author(value: str) -> str:
    text = str(value or "").strip(" \t\r\n，,；;：:。、“”\"'()（）[]【】◦•·-")
    text = QUERY_PREFIX_RE.sub("", text).strip(" ，,；;：:。")
    text = AUTHOR_SUFFIX_RE.sub("", text).strip(" ，,；;：:。")
    if "的" in text and len(text) > 4:
        text = text.rsplit("的", 1)[-1].strip(" ，,；;：:。")
    if re.search(r"[A-Za-z]", text):
        match = re.search(r"[A-Za-z][A-Za-z .,'-]*[A-Za-z]", text)
        if match:
            text = match.group(0).strip(" ，,；;：:。")
    elif ORG_KEYWORDS_RE.search(text) and len(text) > 4:
        text = LEADING_ORG_RE.sub("", text).strip(" ，,；;：:。")
    if len(text) < 2:
        return ""
    if text in {"负责的", "牵头", "讲课", "搜索", "查询", "查找"}:
        return ""
    if ORG_KEYWORDS_RE.search(text) and not re.search(r"[A-Za-z]", text):
        return ""
    return text


def clean_institution(value: str) -> str:
    text = str(value or "").strip(" \t\r\n，,；;：:。、“”\"'()（）[]【】◦•·-")
    text = QUERY_PREFIX_RE.sub("", text).strip(" ，,；;：:。")
    text = INSTITUTION_TRAILING_RE.sub("", text).strip(" ，,；;：:。的")
    if len(text) < 2:
        return ""
    if text in {"搜索", "查询", "查找", "请", "由", "在"}:
        return ""
    return text


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


class SpanAuthorOrgPredictor:
    def __init__(self, model_dir: str, variant_lexicon: str | None, max_length: int, stride: int):
        self.model_dir = Path(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForTokenClassification.from_pretrained(self.model_dir)
        self.model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.max_length = max_length
        self.stride = stride
        self.variant_lexicon = {}
        if load_variant_lexicon is not None and variant_lexicon and Path(variant_lexicon).exists():
            self.variant_lexicon = load_variant_lexicon(variant_lexicon)

    @torch.inference_mode()
    def raw_entities(self, text: str) -> list[dict[str, Any]]:
        encoded = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            stride=self.stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_tensors="pt",
        )
        offsets = encoded.pop("offset_mapping")
        encoded.pop("overflow_to_sample_mapping", None)
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        logits = self.model(**encoded).logits.detach().cpu()
        pred_ids = logits.argmax(dim=-1).tolist()
        entities_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
        for feature_pred_ids, feature_offsets in zip(pred_ids, offsets.tolist()):
            token_labels: list[str] = []
            token_offsets: list[tuple[int, int]] = []
            for pred_id, (start, end) in zip(feature_pred_ids, feature_offsets):
                if start == end:
                    continue
                token_labels.append(self.model.config.id2label[int(pred_id)])
                token_offsets.append((int(start), min(int(end), len(text))))
            for label, start_token, end_token in labels_to_spans(token_labels):
                start = token_offsets[start_token][0]
                end = token_offsets[end_token - 1][1]
                if start >= end:
                    continue
                key = (label, start, end)
                entities_by_key[key] = {
                    "label": label,
                    "field": FIELD_BY_LABEL.get(label, label),
                    "start": start,
                    "end": end,
                    "text": text[start:end],
                }
        return sorted(entities_by_key.values(), key=lambda item: (item["start"], item["end"], item["label"]))

    def predict(self, text: str) -> dict[str, Any]:
        raw_entities = self.raw_entities(text)
        grouped: dict[str, list[str]] = defaultdict(list)
        for entity in raw_entities:
            if entity["label"] == "AUTHOR":
                value = clean_author(entity["text"])
            elif entity["label"] == "INSTITUTION":
                value = clean_institution(entity["text"])
            else:
                value = str(entity["text"]).strip()
            field = entity["field"]
            if field in ENTITY_FIELDS and value:
                grouped[field].append(value)
        authors = dedupe(grouped["author_name"])
        institutions = dedupe(grouped["author_institution"])
        variant_blocks: list[str] = []
        if generate_author_variant_text is not None:
            variant_blocks = [generate_author_variant_text(author, self.variant_lexicon) for author in authors]
        parsed = {
            "author_name": "；".join(authors),
            "author_name英文变体": "\n ".join(block for block in variant_blocks if block),
            "author_institution": "；".join(institutions),
        }
        return {
            "model_type": "modernbert_token_classification_span",
            "model_dir": str(self.model_dir.resolve()),
            "raw_entities": raw_entities,
            "parsed_output": parsed,
        }


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
        return bool(pred_set & gold_set) if pred_set or gold_set else True
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
        "# Span ModernBERT Author/Org Business Evaluation",
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
        "## Output Files",
        "",
        f"- details_jsonl: `{payload['details_jsonl']}`",
        f"- details_csv: `{payload['details_csv']}`",
        "",
        "## Notes",
        "",
        "- `raw_output` is structured BERT span output, not generated text.",
        "- `parsed_output` is the final business JSON fields.",
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
    predictor = SpanAuthorOrgPredictor(args.model_dir, args.variant_lexicon, args.max_length, args.stride)

    records: list[dict[str, Any]] = []
    for idx, row in enumerate(dataset, 1):
        prediction = predictor.predict(row["query"])
        parsed = {field: prediction["parsed_output"].get(field, "") for field in FIELDS}
        raw = {
            "model_type": prediction["model_type"],
            "model_dir": prediction["model_dir"],
            "raw_entities": prediction["raw_entities"],
        }
        records.append(
            {
                "sample_id": idx,
                "query": row["query"],
                "ground_truth": {field: row.get(field, "") for field in FIELDS},
                "raw_output": raw,
                "parsed_output": parsed,
            }
        )
        if idx % 10 == 0 or idx == len(dataset):
            print(f"作者和机构 span-BERT: {idx}/{len(dataset)}")

    details_jsonl = out_prefix.with_name(out_prefix.name + "_details").with_suffix(".jsonl")
    details_csv = out_prefix.with_name(out_prefix.name + "_details").with_suffix(".csv")
    with details_jsonl.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_csv(details_csv, records)

    payload = {
        "model": "modernbert_span_author_org",
        "model_dir": str(Path(args.model_dir).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_samples": len(dataset),
        "metrics": evaluate(records),
        "details_jsonl": str(details_jsonl.resolve()),
        "details_csv": str(details_csv.resolve()),
        "samples": records,
    }
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Details JSONL: {details_jsonl}")
    print(f"CSV: {details_csv}")
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
