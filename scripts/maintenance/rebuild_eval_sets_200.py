#!/usr/bin/env python3
"""Rebuild five local eval JSON files to 100 positive + 100 empty rows.

Rows are based on existing eval files first. Missing positive/empty rows are
borrowed from processed SFT data and then removed from processed SFT/BIO files
to avoid train/eval leakage by exact query.
"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Any


ROOT = Path("/home/qiao/work/NLU-distillation")
EVAL_DIR = Path("/home/qiao/work/nlu-server/eval")
BACKUP_DIR = ROOT / "reports/eval_backup_20260609_before_200_rebuild"
REPORT_PATH = ROOT / "reports/eval_rebuild_200_20260609.json"

SEED = 20260609
TARGET_POSITIVE = 100
TARGET_EMPTY = 100

TASKS = {
    "data_type": {
        "eval_file": "data_type.json",
        "processed": "data_type",
        "fields": ["data_type"],
        "suffix": {"data_type": "标准答案"},
    },
    "作者和机构": {
        "eval_file": "作者和机构.json",
        "processed": "author_org",
        "fields": ["author_name", "author_name英文变体", "author_institution"],
        "suffix": {
            "author_name": "-标准答案",
            "author_name英文变体": "-标准答案",
            "author_institution": "-标准答案",
        },
    },
    "机构和国家": {
        "eval_file": "机构和国家.json",
        "processed": "org_country",
        "fields": ["机构名称", "国家"],
        "suffix": {"机构名称": "-标准答案", "国家": "-标准答案"},
    },
    "时间和if值": {
        "eval_file": "时间和if值.json",
        "processed": "time_if",
        "fields": ["filter_start_datetime", "filter_end_datetime", "filter_start_if", "filter_end_if"],
        "suffix": {
            "filter_start_datetime": "-标准答案",
            "filter_end_datetime": "-标准答案",
            "filter_start_if": "-标准答案",
            "filter_end_if": "-标准答案",
        },
    },
    "topic和keywords": {
        "eval_file": "topic和keywords.json",
        "processed": "topic_keywords",
        "fields": ["topics", "keywords"],
        "suffix": {"topics": "-标准答案", "keywords": "-标准答案"},
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_answer_key(key: str) -> str:
    return str(key).replace("-标准答案", "").replace("标准答案", "").strip()


def query_of_eval_row(row: dict[str, Any]) -> str:
    return str(row.get("question") or row.get("query") or row.get("用户query") or "").strip()


def normalized_eval_targets(row: dict[str, Any]) -> dict[str, Any]:
    return {
        clean_answer_key(k): v
        for k, v in row.items()
        if k not in {"question", "query", "用户query"}
    }


def is_positive_targets(targets: dict[str, Any], fields: list[str]) -> bool:
    return any(str(targets.get(field, "") or "").strip() for field in fields)


def eval_row_from_sft(row: dict[str, Any], fields: list[str], suffix: dict[str, str]) -> dict[str, Any]:
    targets = json.loads(row.get("output") or "{}")
    out: dict[str, Any] = {"question": str(row.get("input") or "").strip()}
    for field in fields:
        out[f"{field}{suffix[field]}"] = targets.get(field, "")
    return out


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sft_query(row: dict[str, Any]) -> str:
    return str(row.get("input") or "").strip()


def bio_query(row: dict[str, Any]) -> str:
    return str(row.get("text") or "").strip()


def rebuild_eval_for_task(task_name: str, cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    eval_path = EVAL_DIR / cfg["eval_file"]
    fields = cfg["fields"]
    suffix = cfg["suffix"]
    old_rows = read_json(eval_path)

    seen_queries: set[str] = set()
    kept_pos: list[dict[str, Any]] = []
    kept_empty: list[dict[str, Any]] = []
    old_pos = old_empty = old_duplicate = 0
    for row in old_rows:
        query = query_of_eval_row(row)
        if not query:
            continue
        if query in seen_queries:
            old_duplicate += 1
            continue
        seen_queries.add(query)
        targets = normalized_eval_targets(row)
        positive = is_positive_targets(targets, fields)
        if positive:
            old_pos += 1
            if len(kept_pos) < TARGET_POSITIVE:
                kept_pos.append(row)
        else:
            old_empty += 1
            if len(kept_empty) < TARGET_EMPTY:
                kept_empty.append(row)

    borrowed_queries: set[str] = set()
    borrowed_pos = borrowed_empty = 0
    sft_all = read_jsonl(ROOT / "data/processed" / cfg["processed"] / "sft/all.jsonl")
    for row in sft_all:
        if len(kept_pos) >= TARGET_POSITIVE and len(kept_empty) >= TARGET_EMPTY:
            break
        query = sft_query(row)
        if not query or query in seen_queries:
            continue
        try:
            targets = json.loads(row.get("output") or "{}")
        except Exception:
            continue
        positive = is_positive_targets(targets, fields)
        if positive and len(kept_pos) < TARGET_POSITIVE:
            kept_pos.append(eval_row_from_sft(row, fields, suffix))
            seen_queries.add(query)
            borrowed_queries.add(query)
            borrowed_pos += 1
        elif (not positive) and len(kept_empty) < TARGET_EMPTY:
            kept_empty.append(eval_row_from_sft(row, fields, suffix))
            seen_queries.add(query)
            borrowed_queries.add(query)
            borrowed_empty += 1

    if len(kept_pos) != TARGET_POSITIVE or len(kept_empty) != TARGET_EMPTY:
        raise RuntimeError(
            f"{task_name}: failed to build target split, got pos={len(kept_pos)} empty={len(kept_empty)}"
        )

    combined = kept_pos + kept_empty
    random.Random(SEED).shuffle(combined)
    report = {
        "old_rows": len(old_rows),
        "old_positive": old_pos,
        "old_empty": old_empty,
        "old_duplicate_queries": old_duplicate,
        "kept_from_old_positive": TARGET_POSITIVE - borrowed_pos,
        "kept_from_old_empty": TARGET_EMPTY - borrowed_empty,
        "borrowed_positive_from_processed": borrowed_pos,
        "borrowed_empty_from_processed": borrowed_empty,
        "final_rows": len(combined),
        "final_positive": len(kept_pos),
        "final_empty": len(kept_empty),
        "borrowed_queries": sorted(borrowed_queries),
    }
    return combined, report


def remove_eval_queries_from_processed(eval_queries_by_slug: dict[str, set[str]]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for cfg in TASKS.values():
        slug = cfg["processed"]
        query_set = eval_queries_by_slug[slug]
        task_dir = ROOT / "data/processed" / slug
        task_report: dict[str, Any] = {}
        for subdir, query_getter in (("sft", sft_query), ("bio", bio_query)):
            dir_path = task_dir / subdir
            if not dir_path.exists():
                continue
            for name in ("all.jsonl", "train.jsonl", "valid.jsonl", "test.jsonl"):
                path = dir_path / name
                rows = read_jsonl(path)
                if not rows:
                    continue
                kept = [row for row in rows if query_getter(row) not in query_set]
                removed = len(rows) - len(kept)
                if removed:
                    write_jsonl(path, kept)
                task_report[str(path.relative_to(ROOT))] = {
                    "before": len(rows),
                    "after": len(kept),
                    "removed_eval_queries": removed,
                }
        report[slug] = task_report
    return report


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for cfg in TASKS.values():
        src = EVAL_DIR / cfg["eval_file"]
        dst = BACKUP_DIR / cfg["eval_file"]
        if not dst.exists():
            shutil.copy2(src, dst)

    new_eval_rows: dict[str, list[dict[str, Any]]] = {}
    report: dict[str, Any] = {"tasks": {}, "backup_dir": str(BACKUP_DIR)}
    eval_queries_by_slug = {cfg["processed"]: set() for cfg in TASKS.values()}

    for task_name, cfg in TASKS.items():
        rows, task_report = rebuild_eval_for_task(task_name, cfg)
        new_eval_rows[task_name] = rows
        report["tasks"][task_name] = task_report
        eval_queries_by_slug[cfg["processed"]] = {query_of_eval_row(row) for row in rows}

    for task_name, cfg in TASKS.items():
        write_json(EVAL_DIR / cfg["eval_file"], new_eval_rows[task_name])

    report["processed_removal"] = remove_eval_queries_from_processed(eval_queries_by_slug)
    write_json(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
