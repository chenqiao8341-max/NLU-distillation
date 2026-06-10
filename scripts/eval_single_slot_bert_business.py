#!/usr/bin/env python3
"""Evaluate single-slot ModernBERT models on nlu-server eval JSON datasets."""

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
DEFAULT_EVALUATOR_ROOT = Path.home() / "work" / "nlu-evaluator"
DEFAULT_NLU_BERT_ROOT = Path.home() / "work" / "nlu-bert"
TASK_FILES = {
    "作者和机构": "作者和机构.json",
    "机构和国家": "机构和国家.json",
}

if str(DEFAULT_EVALUATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_EVALUATOR_ROOT))

try:
    import feishu_client  # noqa: F401
except ModuleNotFoundError:
    import types

    feishu_client = types.ModuleType("feishu_client")
    feishu_client.FeishuBitableClient = object
    sys.modules["feishu_client"] = feishu_client

from main import evaluate_predictions  # noqa: E402

if str(DEFAULT_NLU_BERT_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_NLU_BERT_ROOT))

try:
    from nlu_bert.author_variants import generate_author_variant_text, load_variant_lexicon
except Exception:  # pragma: no cover - keeps evaluation usable without nlu-bert helpers.
    generate_author_variant_text = None
    load_variant_lexicon = None


QUERY_PREFIX_RE = re.compile(r"^(?:[◦•·\-\s]+)?(?:请|搜索|查询|查找|列出|找到|输出|由|在|如|关于)+")
AUTHOR_SUFFIX_RE = re.compile(r"(?:教授|医生|医师|主任|院士|课题组|团队|研究者|负责的|牵头|讲课|作为.*)$")
INSTITUTION_TRAILING_RE = re.compile(r"(?:作为|负责|牵头|正在|进行|发起|研究状态|相关|的?所有|有哪些).*$")
ORG_KEYWORDS_RE = re.compile(
    r"(?:大学|医院|学院|诊所|研究所|研究院|中心|科室|实验室|机构|协会|学会|委员会|联盟|组织|基金会|Clinic|Hospital|University|Institute|Society|Association|Committee|Organization|Foundation)",
    re.I,
)
LEADING_ORG_RE = re.compile(r"^.*(?:大学|医院|学院|诊所|研究所|研究院|中心|科室|附属[^A-Za-z\u4e00-\u9fff]*)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=Path.home() / "work" / "nlu-server" / "eval")
    parser.add_argument("--tasks", nargs="+", choices=sorted(TASK_FILES), default=list(TASK_FILES))
    parser.add_argument("--model-root", type=Path, default=PROJECT_ROOT / "experiments" / "modernbert_single_slot")
    parser.add_argument("--author-model-dir", type=Path)
    parser.add_argument("--institution-model-dir", type=Path)
    parser.add_argument("--country-model-dir", type=Path)
    parser.add_argument(
        "--variant-lexicon",
        type=Path,
        default=DEFAULT_NLU_BERT_ROOT / "outputs" / "modernbert-author-org-ner" / "author_variant_lexicon.json",
    )
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--show-raw-samples", type=int, default=0)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--no-csv", action="store_true")
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
    output: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        output.append(clean)
    return output


def join_values(values: Iterable[str]) -> str:
    return "；".join(dedupe(values))


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
    if re.search(r"(?:专家|指南|共识)$", text) and not ORG_KEYWORDS_RE.search(text):
        return ""
    return text


def clean_country(value: str) -> str:
    text = str(value or "").strip(" \t\r\n，,；;：:。、“”\"'()（）[]【】◦•·-")
    return text


def labels_to_spans(labels: list[str]) -> set[tuple[str, int, int]]:
    spans: set[tuple[str, int, int]] = set()
    current_label: str | None = None
    start = -1
    for idx, label in enumerate(labels + ["O"]):
        if label.startswith("B-"):
            if current_label is not None:
                spans.add((current_label, start, idx))
            current_label = label[2:]
            start = idx
        elif label.startswith("I-"):
            entity = label[2:]
            if current_label == entity:
                continue
            if current_label is not None:
                spans.add((current_label, start, idx))
            current_label = entity
            start = idx
        else:
            if current_label is not None:
                spans.add((current_label, start, idx))
            current_label = None
            start = -1
    return spans


class SingleSlotPredictor:
    def __init__(self, model_dir: Path, max_length: int = 512, stride: int = 128):
        self.model_dir = model_dir
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        self.model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.max_length = max_length
        self.stride = stride

    @torch.inference_mode()
    def predict_entities(self, text: str) -> list[dict[str, Any]]:
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
                if not token_offsets or start_token >= len(token_offsets) or end_token <= start_token:
                    continue
                start = token_offsets[start_token][0]
                end = token_offsets[end_token - 1][1]
                if start >= end:
                    continue
                entities_by_key[(label, start, end)] = {
                    "label": label,
                    "start": start,
                    "end": end,
                    "text": text[start:end],
                }
        return prune_contained_entities(entities_by_key.values())


def prune_contained_entities(entities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for entity in sorted(
        entities,
        key=lambda item: (-(int(item["end"]) - int(item["start"])), int(item["start"]), int(item["end"])),
    ):
        start = int(entity["start"])
        end = int(entity["end"])
        label = str(entity["label"])
        if any(
            str(old["label"]) == label and int(old["start"]) <= start and end <= int(old["end"])
            for old in selected
        ):
            continue
        selected.append(dict(entity))
    return sorted(selected, key=lambda item: (int(item["start"]), int(item["end"]), str(item["label"])))


class BusinessPredictor:
    def __init__(self, args: argparse.Namespace):
        model_root = args.model_root
        self.author = SingleSlotPredictor(args.author_model_dir or model_root / "author", args.max_length, args.stride)
        self.institution = SingleSlotPredictor(
            args.institution_model_dir or model_root / "institution",
            args.max_length,
            args.stride,
        )
        self.country = SingleSlotPredictor(args.country_model_dir or model_root / "country", args.max_length, args.stride)
        self.variant_lexicon: dict[str, list[str]] = {}
        if load_variant_lexicon is not None and args.variant_lexicon and args.variant_lexicon.exists():
            self.variant_lexicon = load_variant_lexicon(args.variant_lexicon)

    def predict_author_org(self, query: str) -> dict[str, Any]:
        author_entities = self.author.predict_entities(query)
        institution_entities = self.institution.predict_entities(query)
        authors = dedupe(clean_author(item["text"]) for item in author_entities)
        institutions = dedupe(clean_institution(item["text"]) for item in institution_entities)
        variant_blocks: list[str] = []
        if generate_author_variant_text is not None:
            variant_blocks = [
                generate_author_variant_text(author, self.variant_lexicon)
                for author in authors
                if author
            ]
        parsed = {
            "author_name": join_values(authors),
            "author_name英文变体": "\n ".join(block for block in variant_blocks if block),
            "author_institution": join_values(institutions),
        }
        return {
            "data": {"result": parsed},
            "raw_entities": {
                "author": author_entities,
                "institution": institution_entities,
            },
        }

    def predict_org_country(self, query: str) -> dict[str, Any]:
        institution_entities = self.institution.predict_entities(query)
        country_entities = self.country.predict_entities(query)
        institutions = dedupe(clean_institution(item["text"]) for item in institution_entities)
        countries = dedupe(clean_country(item["text"]) for item in country_entities)
        parsed = {
            "机构名称": join_values(institutions),
            "国家": join_values(countries),
        }
        return {
            "data": {"result": parsed},
            "raw_entities": {
                "institution": institution_entities,
                "country": country_entities,
            },
        }

    def predict(self, task_type: str, query: str) -> dict[str, Any]:
        if task_type == "作者和机构":
            return self.predict_author_org(query)
        if task_type == "机构和国家":
            return self.predict_org_country(query)
        raise ValueError(f"Unsupported task_type: {task_type}")


def average_task_metrics(task_payloads: list[dict[str, Any]]) -> dict[str, float]:
    keys = ["Average-EM", "Average-Partial", "Average-F1", "Null-accuracy"]
    result: dict[str, float] = {}
    for key in keys:
        vals = [float(t["metrics"].get(key, 0.0)) for t in task_payloads if "metrics" in t]
        result[key] = sum(vals) / len(vals) if vals else 0.0
    return result


def evaluate_task(
    predictor: BusinessPredictor,
    task_type: str,
    dataset: list[dict[str, Any]],
    show_raw_samples: int = 0,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for idx, row in enumerate(dataset, 1):
        raw = predictor.predict(task_type, row["query"])
        parsed = dict(raw["data"]["result"])
        record = {
            "query": row["query"],
            "ground_truth": {key: value for key, value in row.items() if key != "query"},
            "raw_output": raw,
            "parsed_output": parsed,
        }
        records.append(record)
        if show_raw_samples and idx <= show_raw_samples:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        if idx % 10 == 0 or idx == len(dataset):
            print(f"  {task_type}: {idx}/{len(dataset)}")

    metrics = evaluate_predictions(
        [record["parsed_output"] for record in records],
        dataset,
        "extraction",
        task_type=task_type,
    )
    return metrics, records


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Single-Slot ModernBERT Business Evaluation",
        "",
        f"- model: {payload['model']}",
        f"- generated_at: {payload['generated_at']}",
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
    seen: set[str] = set()
    for record in records:
        for source in (record.get("ground_truth", {}), record.get("parsed_output", {})):
            for key in source:
                if key in {"raw", "entities"} or key in seen:
                    continue
                seen.add(key)
                value_headers.append(key)

    columns = ["task_type", "query"]
    columns += [f"GT_{header}" for header in value_headers]
    columns += [f"PRED_{header}" for header in value_headers]
    columns += ["raw_output", "parsed_output"]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            gt = record.get("ground_truth", {})
            pred = record.get("parsed_output", {})
            row = {"task_type": record.get("task_type", ""), "query": record.get("query", "")}
            for header in value_headers:
                row[f"GT_{header}"] = gt.get(header, "")
                row[f"PRED_{header}"] = pred.get(header, "")
            row["raw_output"] = json.dumps(record.get("raw_output", {}), ensure_ascii=False)
            row["parsed_output"] = json.dumps(pred, ensure_ascii=False)
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_prefix = args.output_prefix or PROJECT_ROOT / "reports" / "modernbert_single_slot_business" / f"single_slot_bert_eval_{timestamp}"
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    predictor = BusinessPredictor(args)
    task_payloads: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []

    for task_type in args.tasks:
        dataset_path = args.dataset_dir / TASK_FILES[task_type]
        dataset = load_eval_dataset(dataset_path, args.limit)
        print(f"\n== {task_type} ({len(dataset)} samples) ==")
        metrics, records = evaluate_task(predictor, task_type, dataset, args.show_raw_samples)
        task_payloads.append(
            {
                "task_type": task_type,
                "dataset": str(dataset_path.resolve()),
                "sample_count": len(dataset),
                "metrics": metrics,
                "samples": records,
            }
        )
        for record in records:
            all_records.append({"task_type": task_type, **record})

    payload = {
        "model": "modernbert-single-slot",
        "model_dirs": {
            "author": str((args.author_model_dir or args.model_root / "author").resolve()),
            "institution": str((args.institution_model_dir or args.model_root / "institution").resolve()),
            "country": str((args.country_model_dir or args.model_root / "country").resolve()),
        },
        "dataset_dir": str(args.dataset_dir.resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_samples": sum(task["sample_count"] for task in task_payloads),
        "overall_metrics": average_task_metrics(task_payloads),
        "tasks": task_payloads,
    }

    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(f"\nJSON: {json_path}")
    print(f"Markdown: {md_path}")

    if not args.no_csv:
        csv_path = out_prefix.with_name(out_prefix.name + "_details").with_suffix(".csv")
        write_csv_details(csv_path, all_records)
        print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
