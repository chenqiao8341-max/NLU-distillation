#!/usr/bin/env python3
"""Inspect production NLU JSONL schema and field coverage."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any


EMPTY_VALUES = (None, "", [], {})


def is_nonempty(value: Any) -> bool:
    return value not in EMPTY_VALUES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="Input JSONL file.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows to inspect.")
    parser.add_argument("--top", type=int, default=80, help="Maximum NLU fields to print.")
    args = parser.parse_args()

    rows = 0
    bad_rows = 0
    top_fields: collections.Counter[str] = collections.Counter()
    nlu_fields: collections.Counter[str] = collections.Counter()
    nlu_nonempty: collections.Counter[str] = collections.Counter()
    data_sources: collections.Counter[str] = collections.Counter()

    with args.jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if args.limit is not None and rows >= args.limit:
                break
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad_rows += 1
                print(f"bad_json\tline={line_no}")
                continue

            rows += 1
            for key, value in obj.items():
                top_fields[key] += 1
                if key == "data_sources" and isinstance(value, list):
                    data_sources.update(str(item) for item in value)

            nlu = obj.get("nlu") or {}
            if isinstance(nlu, dict):
                for key, value in nlu.items():
                    nlu_fields[key] += 1
                    if is_nonempty(value):
                        nlu_nonempty[key] += 1

    print(f"file\t{args.jsonl}")
    print(f"rows\t{rows}")
    print(f"bad_rows\t{bad_rows}")

    print("\ntop_fields")
    for key, count in top_fields.most_common():
        print(f"{key}\t{count}")

    print("\ndata_sources")
    for key, count in data_sources.most_common():
        print(f"{key}\t{count}")

    print("\nnlu_fields_nonempty")
    for key, count in nlu_nonempty.most_common(args.top):
        total = nlu_fields[key]
        ratio = count / total if total else 0.0
        print(f"{key}\t{count}/{total}\t{ratio:.2%}")


if __name__ == "__main__":
    main()
