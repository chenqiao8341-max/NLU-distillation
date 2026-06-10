#!/usr/bin/env python3
"""Build canonical author_org span data from existing char-level BIO data."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIELD_BY_LABEL = {"AUTHOR": "author_name", "INSTITUTION": "author_institution"}
FIELDS = ["author_name", "author_name英文变体", "author_institution"]
SPLITS = ["train", "valid", "test", "all"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bio-dir", type=Path, default=PROJECT_ROOT / "data" / "processed" / "author_org" / "bio")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "processed" / "author_org" / "span")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def bio_to_entities(text: str, labels: list[str]) -> list[dict[str, Any]]:
    if len(text) != len(labels):
        raise ValueError(f"text length {len(text)} != label length {len(labels)}")

    entities: list[dict[str, Any]] = []
    current_label: str | None = None
    start: int | None = None
    for idx, label in enumerate(labels + ["O"]):
        entity_label = label[2:] if label != "O" else None
        starts_new = label.startswith("B-") or entity_label != current_label
        if not starts_new:
            continue
        if current_label is not None and start is not None:
            value = text[start:idx]
            entities.append(
                {
                    "start": start,
                    "end": idx,
                    "text": value,
                    "label": current_label,
                    "field": FIELD_BY_LABEL[current_label],
                }
            )
        current_label = entity_label
        start = idx if entity_label is not None else None
    return entities


def convert_row(row: dict[str, Any]) -> dict[str, Any]:
    text = row["text"]
    entities = bio_to_entities(text, row["char_labels"])
    output = {
        "text": text,
        "task": row.get("task", "作者和机构"),
        "entities": entities,
    }
    for field in FIELDS:
        output[field] = row.get(field, "")
    return output


def summarize(split_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for split, rows in split_rows.items():
        entity_counts = Counter()
        positive_rows = 0
        long_rows = 0
        entities_after_256 = 0
        for row in rows:
            entities = row["entities"]
            positive_rows += bool(entities)
            long_rows += len(row["text"]) > 256
            for entity in entities:
                entity_counts[entity["label"]] += 1
                entities_after_256 += entity["start"] >= 256
        summary[split] = {
            "rows": len(rows),
            "positive_rows": positive_rows,
            "empty_rows": len(rows) - positive_rows,
            "entity_counts": dict(sorted(entity_counts.items())),
            "long_rows_gt_256_chars": long_rows,
            "entities_start_after_char_256": entities_after_256,
        }
    return summary


def main() -> None:
    args = parse_args()
    split_rows: dict[str, list[dict[str, Any]]] = {}
    for split in SPLITS:
        rows = [convert_row(row) for row in read_jsonl(args.bio_dir / f"{split}.jsonl")]
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)
        split_rows[split] = rows

    stats = {
        "source": str(args.bio_dir.resolve()),
        "output": str(args.output_dir.resolve()),
        "fields": FIELDS,
        "labels": FIELD_BY_LABEL,
        "summary": summarize(split_rows),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
