#!/usr/bin/env python3
"""Build single-slot BIO datasets for BERT extraction experiments."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = PROJECT_ROOT / "reports" / "eval_manual_review_20260610"
SLOTS = ["author", "institution", "country", "time", "impact_factor"]

RELATIVE_DATE_PATTERNS = [
    r"近\s*[0-9一二两三四五六七八九十百两]+\s*(?:年|个月|月|周|天)(?:内)?",
    r"最近\s*[0-9一二两三四五六七八九十百两]+\s*(?:年|个月|月|周|天)(?:内)?",
    r"近年来",
    r"近些年",
    r"最近几年",
]

LOOSE_TIME_PATTERNS = [
    r"最新(?:进展|研究|指南|共识|文献|成果|发现|技术|突破|用药方案)?",
    r"前沿(?:进展|关注点)?",
    r"目前",
    r"当前(?:状态)?",
    r"现状",
    r"研究现状",
    r"研究进展",
    r"领域进展",
    r"新(?:发现|进展|技术|突破)",
]

IF_3_CUE_PATTERNS = [r"高质量", r"高分"]
IF_5_CUE_PATTERNS = [r"重点研究", r"关键研究"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-root", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "data" / "processed_single")
    parser.add_argument("--reference-year", type=int, default=date.today().year)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(item for item in (normalize_value(v) for v in value) if item)
    return str(value).strip()


def split_values(value: Any) -> list[str]:
    text = normalize_value(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[；;\n]+", text) if item.strip()]


def find_all(text: str, value: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    if not value:
        return spans
    start = 0
    while start < len(text):
        idx = text.find(value, start)
        if idx < 0:
            break
        spans.append((idx, idx + len(value)))
        start = idx + max(1, len(value))
    return spans


def mark_span(labels: list[str], start: int, end: int, label: str) -> bool:
    if start < 0 or end > len(labels) or start >= end:
        return False
    if any(item != "O" for item in labels[start:end]):
        return False
    labels[start] = f"B-{label}"
    for idx in range(start + 1, end):
        labels[idx] = f"I-{label}"
    return True


def prune_contained(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    selected: list[tuple[int, int]] = []
    for start, end in sorted(spans, key=lambda item: (-(item[1] - item[0]), item[0], item[1])):
        if any(sel_start <= start and end <= sel_end for sel_start, sel_end in selected):
            continue
        selected.append((start, end))
    return sorted(selected)


def extract_bio_spans(text: str, char_labels: list[str], source_entity: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    current = False
    start = -1
    for idx, label in enumerate(char_labels + ["O"]):
        entity = label[2:] if label != "O" else None
        starts_new = label == f"B-{source_entity}" or (current and entity != source_entity)
        if starts_new and current:
            spans.append((start, idx))
            current = False
        if label == f"B-{source_entity}":
            current = True
            start = idx
        elif not current and label == f"I-{source_entity}":
            current = True
            start = idx
    return spans


def make_row_from_spans(text: str, spans: Iterable[tuple[int, int]], label: str, source: str) -> dict[str, Any]:
    labels = ["O"] * len(text)
    values: list[str] = []
    missed = 0
    for start, end in prune_contained(spans):
        if mark_span(labels, start, end, label):
            value = text[start:end]
            if value not in values:
                values.append(value)
        else:
            missed += 1
    return {
        "text": text,
        "char_labels": labels,
        "task": f"single_{label.lower()}",
        "slot": label,
        "values": "；".join(values),
        "source": source,
        "missed_spans": missed,
    }


def rows_from_existing_bio(
    rows: list[dict[str, Any]],
    source_entity: str,
    target_label: str,
    source: str,
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        text = row["text"]
        spans = extract_bio_spans(text, row["char_labels"], source_entity)
        output.append(make_row_from_spans(text, spans, target_label, source))
    return output


def rows_from_values(
    rows: list[dict[str, Any]],
    fields: list[str],
    label: str,
    source: str,
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        text = normalize_value(row.get("question") or row.get("query") or row.get("text"))
        spans: list[tuple[int, int]] = []
        for field in fields:
            for value in split_values(row.get(field)):
                spans.extend(find_all(text, value))
        output.append(make_row_from_spans(text, spans, label, source))
    return output


def regex_spans(text: str, patterns: Iterable[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            spans.append((match.start(), match.end()))
    return spans


def date_variants(value: str) -> list[str]:
    text = normalize_value(value)
    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not match:
        return [text] if text else []
    year, month, day = (int(item) for item in match.groups())
    variants = [
        f"{year}-{month:02d}-{day:02d}",
        f"{year}-{month}-{day}",
        f"{year}年{month}月{day}日",
        f"{year}年{month:02d}月{day:02d}日",
    ]
    if day == 1:
        variants.extend([f"{year}年{month}月", f"{year}年{month:02d}月"])
    if (month, day) in {(1, 1), (12, 31)}:
        variants.append(f"{year}年")
    return list(dict.fromkeys(variants))


def parse_chinese_number(text: str) -> int | None:
    stripped = text.strip()
    if stripped.isdigit():
        return int(stripped)
    digits = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if stripped == "十":
        return 10
    if "十" in stripped:
        left, _, right = stripped.partition("十")
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    return digits.get(stripped) if len(stripped) == 1 else None


def filter_relative_spans(text: str, spans: list[tuple[int, int]], value: str, reference_year: int) -> list[tuple[int, int]]:
    match = re.fullmatch(r"(\d{4})-\d{1,2}-\d{1,2}", normalize_value(value))
    if not match:
        return spans
    target_year = int(match.group(1))
    matched: list[tuple[int, int]] = []
    saw_year_span = False
    for start, end in spans:
        phrase = text[start:end]
        m = re.search(r"(?:近|最近)\s*([0-9一二两三四五六七八九十]+)\s*(年|个月|月|周|天)", phrase)
        if not m:
            matched.append((start, end))
            continue
        count = parse_chinese_number(m.group(1))
        unit = m.group(2)
        if count is None:
            continue
        if unit == "年":
            saw_year_span = True
            if abs(reference_year - count - target_year) <= 1:
                matched.append((start, end))
        else:
            matched.append((start, end))
    if matched:
        return matched
    return [] if saw_year_span else spans


def time_spans_from_targets(text: str, targets: dict[str, str], reference_year: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for field in ["filter_start_datetime", "filter_end_datetime"]:
        value = targets.get(field, "")
        if not value:
            continue
        exact: list[tuple[int, int]] = []
        for variant in date_variants(value):
            exact.extend(find_all(text, variant))
        if exact:
            spans.extend(exact)
            continue
        cue_spans = regex_spans(text, RELATIVE_DATE_PATTERNS + LOOSE_TIME_PATTERNS)
        spans.extend(filter_relative_spans(text, cue_spans, value, reference_year))
    return spans


def if_value_variants(value: str) -> list[str]:
    text = normalize_value(value)
    if not text:
        return []
    variants = [text]
    try:
        number = float(text)
    except ValueError:
        return variants
    if number.is_integer():
        variants.append(str(int(number)))
    return list(dict.fromkeys(variants))


def has_if_context(text: str, start: int, end: int) -> bool:
    if text[end : end + 1] in {"年", "月", "日", "岁"}:
        return False
    window = text[max(0, start - 24) : min(len(text), end + 8)]
    return bool(re.search(r"IF|if|影响因子|因子|分以上|分以下|高分|高质量|重点研究|关键研究", window, flags=re.I))


def if_spans_from_targets(text: str, targets: dict[str, str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for field in ["filter_start_if", "filter_end_if"]:
        value = targets.get(field, "")
        if not value:
            continue
        field_spans: list[tuple[int, int]] = []
        for variant in if_value_variants(value):
            for start, end in find_all(text, variant):
                if has_if_context(text, start, end):
                    field_spans.append((start, end))
        if field_spans:
            spans.extend(field_spans)
            continue
        if normalize_value(value) == "3":
            spans.extend(regex_spans(text, IF_3_CUE_PATTERNS))
        elif normalize_value(value) == "5":
            spans.extend(regex_spans(text, IF_5_CUE_PATTERNS))
    return spans


def sft_targets(row: dict[str, Any]) -> dict[str, str]:
    output = row.get("output", "")
    parsed = json.loads(output) if isinstance(output, str) else output
    return {key: normalize_value(parsed.get(key)) for key in ["filter_start_datetime", "filter_end_datetime", "filter_start_if", "filter_end_if"]}


def rows_from_time_if_sft(rows: list[dict[str, Any]], label: str, source: str, reference_year: int) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        text = normalize_value(row.get("input"))
        targets = sft_targets(row)
        spans = time_spans_from_targets(text, targets, reference_year) if label == "TIME" else if_spans_from_targets(text, targets)
        output.append(make_row_from_spans(text, spans, label, source))
    return output


def rows_from_time_if_eval(rows: list[dict[str, Any]], label: str, source: str, reference_year: int) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        text = normalize_value(row.get("question") or row.get("query"))
        targets = {
            "filter_start_datetime": normalize_value(row.get("filter_start_datetime-标准答案")),
            "filter_end_datetime": normalize_value(row.get("filter_end_datetime-标准答案")),
            "filter_start_if": normalize_value(row.get("filter_start_if-标准答案")),
            "filter_end_if": normalize_value(row.get("filter_end_if-标准答案")),
        }
        spans = time_spans_from_targets(text, targets, reference_year) if label == "TIME" else if_spans_from_targets(text, targets)
        output.append(make_row_from_spans(text, spans, label, source))
    return output


def write_slot(output_root: Path, slot: str, label: str, train: list[dict[str, Any]], valid: list[dict[str, Any]], test: list[dict[str, Any]]) -> dict[str, Any]:
    slot_dir = output_root / slot / "bio"
    all_rows = train + valid + test
    for split, rows in [("train", train), ("valid", valid), ("test", test), ("all", all_rows)]:
        write_jsonl(slot_dir / f"{split}.jsonl", rows)
    label_list = ["O", f"B-{label}", f"I-{label}"]
    slot_dir.mkdir(parents=True, exist_ok=True)
    (slot_dir / "label_list.json").write_text(json.dumps(label_list, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = summarize(slot, label, train, valid, test)
    stats_text = json.dumps(stats, ensure_ascii=False, indent=2)
    (output_root / slot / "stats.json").write_text(stats_text, encoding="utf-8")
    (slot_dir / "stats.json").write_text(stats_text, encoding="utf-8")
    return stats


def summarize(slot: str, label: str, train: list[dict[str, Any]], valid: list[dict[str, Any]], test: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {"slot": slot, "label": label, "splits": {}}
    for split, rows in [("train", train), ("valid", valid), ("test", test), ("all", train + valid + test)]:
        source_counts = Counter(row.get("source", "") for row in rows)
        positives = sum(any(x != "O" for x in row["char_labels"]) for row in rows)
        entities = sum(1 for row in rows for item in row["char_labels"] if item == f"B-{label}")
        payload["splits"][split] = {
            "rows": len(rows),
            "positive_rows": positives,
            "empty_rows": len(rows) - positives,
            "entities": entities,
            "missed_spans": sum(int(row.get("missed_spans", 0)) for row in rows),
            "source_counts": dict(sorted(source_counts.items())),
        }
    return payload


def main() -> None:
    args = parse_args()
    processed = args.processed_root
    eval_dir = args.eval_dir

    author_train = rows_from_existing_bio(read_jsonl(processed / "author_org" / "bio" / "train.jsonl"), "AUTHOR", "AUTHOR", "author_org_train")
    author_valid = rows_from_existing_bio(read_jsonl(processed / "author_org" / "bio" / "valid.jsonl"), "AUTHOR", "AUTHOR", "author_org_valid")
    author_test = rows_from_values(read_json(eval_dir / "作者和机构.json"), ["author_name-标准答案"], "AUTHOR", "eval_author_org")

    inst_train = (
        rows_from_existing_bio(read_jsonl(processed / "author_org" / "bio" / "train.jsonl"), "INSTITUTION", "INSTITUTION", "author_org_train")
        + rows_from_existing_bio(read_jsonl(processed / "org_country" / "bio" / "train.jsonl"), "INSTITUTION", "INSTITUTION", "org_country_train")
    )
    inst_valid = (
        rows_from_existing_bio(read_jsonl(processed / "author_org" / "bio" / "valid.jsonl"), "INSTITUTION", "INSTITUTION", "author_org_valid")
        + rows_from_existing_bio(read_jsonl(processed / "org_country" / "bio" / "valid.jsonl"), "INSTITUTION", "INSTITUTION", "org_country_valid")
    )
    inst_test = rows_from_values(read_json(eval_dir / "作者和机构.json"), ["author_institution-标准答案"], "INSTITUTION", "eval_author_org") + rows_from_values(
        read_json(eval_dir / "机构和国家.json"), ["机构名称-标准答案"], "INSTITUTION", "eval_org_country"
    )

    country_train = rows_from_existing_bio(read_jsonl(processed / "org_country" / "bio" / "train.jsonl"), "COUNTRY", "COUNTRY", "org_country_train")
    country_valid = rows_from_existing_bio(read_jsonl(processed / "org_country" / "bio" / "valid.jsonl"), "COUNTRY", "COUNTRY", "org_country_valid")
    country_test = rows_from_values(read_json(eval_dir / "机构和国家.json"), ["国家-标准答案"], "COUNTRY", "eval_org_country")

    time_train = rows_from_time_if_sft(read_jsonl(processed / "time_if" / "sft" / "train.jsonl"), "TIME", "time_if_train", args.reference_year)
    time_valid = rows_from_time_if_sft(read_jsonl(processed / "time_if" / "sft" / "valid.jsonl"), "TIME", "time_if_valid", args.reference_year)
    time_test = rows_from_time_if_eval(read_json(eval_dir / "时间和if值.json"), "TIME", "eval_time_if", args.reference_year)

    if_train = rows_from_time_if_sft(read_jsonl(processed / "time_if" / "sft" / "train.jsonl"), "IMPACT_FACTOR", "time_if_train", args.reference_year)
    if_valid = rows_from_time_if_sft(read_jsonl(processed / "time_if" / "sft" / "valid.jsonl"), "IMPACT_FACTOR", "time_if_valid", args.reference_year)
    if_test = rows_from_time_if_eval(read_json(eval_dir / "时间和if值.json"), "IMPACT_FACTOR", "eval_time_if", args.reference_year)

    stats = {
        "author": write_slot(args.output_root, "author", "AUTHOR", author_train, author_valid, author_test),
        "institution": write_slot(args.output_root, "institution", "INSTITUTION", inst_train, inst_valid, inst_test),
        "country": write_slot(args.output_root, "country", "COUNTRY", country_train, country_valid, country_test),
        "time": write_slot(args.output_root, "time", "TIME", time_train, time_valid, time_test),
        "impact_factor": write_slot(args.output_root, "impact_factor", "IMPACT_FACTOR", if_train, if_valid, if_test),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "prepare_single_slot_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
