#!/usr/bin/env python3
"""Prepare task-specific BIO and SFT data from production NLU JSONL."""

from __future__ import annotations

import argparse
import json
import random
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = Path("/home/qiao/work/nlu-server/eval")
DEFAULT_PRODUCTION_JSONL = PROJECT_ROOT / "nlu-data" / "knows_nlu_20260101_20260603.jsonl"
DEFAULT_PROMPT_FILE = DEFAULT_EVAL_DIR / "prompt-new.md"

TASK_FILES = {
    "作者和机构": "作者和机构.json",
    "机构和国家": "机构和国家.json",
    "时间和if值": "时间和if值.json",
    "data_type": "data_type.json",
    "topic和keywords": "topic和keywords.json",
}

TASK_OUTPUT_NAMES = {
    "作者和机构": "author_org",
    "机构和国家": "org_country",
    "时间和if值": "time_if",
    "data_type": "data_type",
    "topic和keywords": "topic_keywords",
}

TASK_TARGET_FIELDS = {
    "作者和机构": ["author_name", "author_name英文变体", "author_institution"],
    "机构和国家": ["机构名称", "国家"],
    "时间和if值": ["filter_start_datetime", "filter_end_datetime", "filter_start_if", "filter_end_if"],
    "data_type": ["data_type"],
    "topic和keywords": ["topics", "keywords"],
}

BIO_TASKS = {"作者和机构", "机构和国家", "topic和keywords"}

BIO_LABEL_ENTITIES = {
    "作者和机构": {"author_name": "AUTHOR", "author_institution": "INSTITUTION"},
    "机构和国家": {"机构名称": "INSTITUTION", "国家": "COUNTRY"},
    "topic和keywords": {"topics": "TOPIC", "keywords": "KEYWORD"},
}

SFT_INSTRUCTIONS = {
    "作者和机构": (
        "你是一个医学检索 NLU 抽取器。请从用户 query 中抽取作者和机构信息。"
        "只输出一个合法 JSON 对象，不要输出解释、Markdown、代码块或思考过程。"
        "JSON 必须包含 author_name、author_name英文变体、author_institution 三个字段。"
        "缺失或不确定时填空字符串。不要臆造未在 query 中出现或无法明确推出的信息。"
    ),
    "机构和国家": (
        "你是一个医学检索 NLU 抽取器。请从用户 query 中抽取发布机构和国家/地区。"
        "只输出一个合法 JSON 对象，必须包含 机构名称、国家 两个字段。"
        "多个值用中文分号连接；缺失或不确定时填空字符串；禁止根据机构名自行推断国家。"
    ),
    "时间和if值": (
        "你是一个医学检索 NLU 抽取器。请从用户 query 中抽取发布时间范围和影响因子范围。"
        "只输出一个合法 JSON 对象，必须包含 filter_start_datetime、filter_end_datetime、filter_start_if、filter_end_if。"
        "日期格式为 YYYY-MM-DD；IF 只填数字；缺失或不确定时填空字符串。"
    ),
    "data_type": (
        "你是一个医学检索 NLU 抽取器。请判断 query 是否明确要求限定医学研究类型。"
        "只输出一个合法 JSON 对象，必须包含 data_type 字段。"
        "可选值包括：综述、Meta分析/系统性综述、RCT、观察性研究、病例系列/病例报告、基础研究。"
        "多个值用中文分号连接；没有明确研究类型时填空字符串。"
    ),
    "topic和keywords": (
        "你是一个医学检索 NLU 抽取器。请从用户 query 中抽取主题词 topics 和关键词 keywords。"
        "只输出一个合法 JSON 对象，必须包含 topics、keywords 两个字段。"
        "多个值用中文分号连接；提取文本必须来自 query，缺失或不确定时填空字符串。"
    ),
}

PROMPT_SECTION_NAMES = {
    "作者和机构": "作者和机构",
    "机构和国家": "机构和国家",
    "时间和if值": "时间和if值",
    "data_type": "data_type",
    "topic和keywords": "topic和keywords",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", help="Input JSON/JSONL file. Defaults to production NLU JSONL.")
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--tasks", nargs="*", choices=sorted(TASK_FILES), default=list(TASK_FILES))
    parser.add_argument("--formats", nargs="*", choices=["sft", "bio"], default=["sft", "bio"])
    parser.add_argument("--source-format", choices=["eval", "production"], default="production")
    parser.add_argument("--positive-limit", type=int, default=3000, help="Max non-empty examples per task.")
    parser.add_argument("--negative-limit", type=int, default=2000, help="Max empty examples per task.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--limit", type=int, help="Maximum source rows to scan per input file.")
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT_FILE)
    return parser.parse_args()


def prompt_section(prompt_file: Path, section_title: str) -> str:
    if not prompt_file.exists():
        return ""
    text = prompt_file.read_text(encoding="utf-8")
    pattern = rf"^##\s+{re.escape(section_title)}\s*$"
    match = re.search(pattern, text, flags=re.M)
    if not match:
        return ""
    next_match = re.search(r"^##\s+", text[match.end():], flags=re.M)
    end = match.end() + next_match.start() if next_match else len(text)
    section = text[match.end():end].strip()
    current_year = str(date.today().year)
    return section.replace("{current_time}=2026", current_year).replace("{current_time}", current_year)


def sft_output_contract(task: str) -> str:
    json_shape = json.dumps({field: "" for field in TASK_TARGET_FIELDS[task]}, ensure_ascii=False)
    if task == "data_type":
        extra = (
            "data_type 字段使用中文标准标签，多个值用中文分号连接："
            "综述；Meta分析/系统性综述；RCT；观察性研究；病例系列/病例报告；基础研究。"
            "如果原提示词要求输出字母 a-f，请在最终 JSON 中映射为上述中文标签。"
        )
    elif task == "作者和机构":
        extra = (
            "author_name英文变体 字段使用 <variant>...</variant> 片段，多个片段用换行分隔。"
            "如果原提示词要求 result 数组，请在最终 JSON 中合并到 author_name、author_name英文变体、author_institution 三个字段。"
        )
    elif task == "机构和国家":
        extra = "如果原提示词要求 XML 标签 publisher/country，请在最终 JSON 中映射为 机构名称、国家。"
    elif task == "时间和if值":
        extra = (
            "如果原提示词要求 XML 标签 filter_date_start/filter_date_end/filter_if_start/filter_if_end，"
            "请在最终 JSON 中映射为 filter_start_datetime、filter_end_datetime、filter_start_if、filter_end_if。"
        )
    elif task == "topic和keywords":
        extra = "如果原提示词要求 XML 标签 topic/keywords，请在最终 JSON 中映射为 topics、keywords；多个值用中文分号连接。"
    else:
        extra = ""
    return (
        "\n\n监督微调输出约束：只输出一个合法 JSON 对象，不要解释，不要 Markdown，不要代码块，不要思考过程。"
        f"JSON 必须包含且只包含这些字段；没有明确证据就填空字符串：{json_shape}。"
        f"{extra}"
    )


def sft_instruction(task: str, prompt_file: Path) -> str:
    section_name = PROMPT_SECTION_NAMES[task]
    detailed_prompt = prompt_section(prompt_file, section_name)
    base_prompt = detailed_prompt or SFT_INSTRUCTIONS[task]
    return base_prompt.strip() + sft_output_contract(task)


def clean_answer_key(key: str) -> str:
    return str(key).replace("-标准答案", "").replace("标准答案", "").strip()


def is_empty_output_text(text: str) -> bool:
    stripped = str(text or "").strip()
    return stripped == "" or stripped.lower() in {"none", "null", "n/a", "na", "[]", "{}"}


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [normalize_value(item) for item in value]
        return "；".join([p for p in parts if p and not is_empty_output_text(p)])
    if isinstance(value, dict):
        keyword = value.get("keyword")
        if keyword is not None:
            return normalize_value(keyword)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def is_empty_output_value(value: Any) -> bool:
    return is_empty_output_text(normalize_value(value))


def split_values(value: Any) -> list[str]:
    text = normalize_value(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[；;\n]+", text) if item.strip() and not is_empty_output_text(item)]


def split_values_loose(value: Any) -> list[str]:
    text = normalize_value(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[；;\n,，]+", text) if item.strip() and not is_empty_output_text(item)]


def dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = normalize_value(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def collapse_spaces_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_value(text)).strip().casefold()


def appears_in_query(query: str, value: str) -> bool:
    text = normalize_value(value)
    if not text:
        return False
    if text in query:
        return True
    return collapse_spaces_for_match(text) in collapse_spaces_for_match(query)


def strip_parenthetical_expansion(value: str) -> str:
    text = normalize_value(value)
    if not text:
        return ""
    stripped = re.sub(r"\s*[\(（][^\)）]*[\)）]\s*", "", text).strip()
    return stripped or text


def filter_loose_values_in_query(query: str, value: Any) -> str:
    visible: list[str] = []
    for raw_value in split_values_loose(value):
        candidates = [raw_value, strip_parenthetical_expansion(raw_value)]
        matched = next((candidate for candidate in candidates if candidate and appears_in_query(query, candidate)), "")
        if matched:
            visible.append(matched)
    return "；".join(dedupe_keep_order(visible))


COUNTRY_OR_REGION_VALUES = {
    "中国", "美国", "英国", "日本", "韩国", "德国", "法国", "意大利", "西班牙", "加拿大", "澳大利亚",
    "欧洲", "欧盟", "亚洲", "非洲", "香港", "澳门", "台湾", "马来西亚", "沙特阿拉伯", "立陶宛",
    "巴西", "肯尼亚", "巴勒斯坦", "印度", "新加坡", "泰国", "越南", "俄罗斯",
}

GENERIC_COUNTRY_SCOPE_VALUES = {"国内外", "国际", "全球", "国外", "海外"}


def filter_institutions_in_query(query: str, value: Any) -> str:
    values = []
    for item in split_values_loose(filter_loose_values_in_query(query, value)):
        if item in COUNTRY_OR_REGION_VALUES or item in GENERIC_COUNTRY_SCOPE_VALUES:
            continue
        values.append(item)
    return "；".join(dedupe_keep_order(values))


def filter_countries_in_query(query: str, value: Any) -> str:
    values = []
    for item in split_values_loose(filter_loose_values_in_query(query, value)):
        if item in GENERIC_COUNTRY_SCOPE_VALUES:
            continue
        values.append(item)
    return "；".join(dedupe_keep_order(values))


TOPIC_KEYWORD_METADATA_PATTERNS = [
    r"^Review$",
    r"^Basic_Research$",
    r"^Observational_Study$",
    r"^Meta_Analysis$",
    r"^Systematic_Review$",
    r"^Meta_Analysis/Systematic_Review$",
    r"^Case_Series/Case_Report$",
    r"^研究类型$",
    r"^发布时间$",
    r"^影响因子$",
    r"^IF\s*[≥>=]?\s*\d+(?:\.\d+)?$",
    r"^IF值\s*[≥>=]?\s*\d+(?:\.\d+)?$",
    r"^近\d+年$",
    r"^最近\d+年$",
    r"^\d{4}年[至-].*$",
    r"^\d{4}年$",
    r"^无限制$",
]


def is_topic_keyword_metadata_value(value: str) -> bool:
    text = normalize_value(value)
    if not text:
        return True
    return any(re.fullmatch(pattern, text, flags=re.I) for pattern in TOPIC_KEYWORD_METADATA_PATTERNS)


def filter_topic_keyword_values_in_query(query: str, value: Any) -> str:
    values = []
    for item in split_values_loose(filter_loose_values_in_query(query, value)):
        if is_topic_keyword_metadata_value(item):
            continue
        values.append(item)
    return "；".join(dedupe_keep_order(values))


def filter_values_in_query(query: str, value: Any) -> str:
    return "；".join(value for value in dedupe_keep_order(split_values(value)) if appears_in_query(query, value))


DATA_TYPE_LABEL_MAP = {
    "review": "综述",
    "literature_review_non_systematic_review": "综述",
    "overview": "综述",
    "survey": "综述",
    "meta_analysis/systematic_review": "Meta分析/系统性综述",
    "meta_analysis_systematic_review": "Meta分析/系统性综述",
    "meta analysis/systematic review": "Meta分析/系统性综述",
    "systematic_review": "Meta分析/系统性综述",
    "systematic review": "Meta分析/系统性综述",
    "meta_analysis": "Meta分析/系统性综述",
    "meta analysis": "Meta分析/系统性综述",
    "rct": "RCT",
    "randomized_controlled_trial": "RCT",
    "randomized controlled trial": "RCT",
    "observational_study": "观察性研究",
    "observational study": "观察性研究",
    "cohort_study": "观察性研究",
    "case_control_study": "观察性研究",
    "cross_sectional_study": "观察性研究",
    "case_series/case_report": "病例系列/病例报告",
    "case_series_case_report": "病例系列/病例报告",
    "case series/case report": "病例系列/病例报告",
    "case_report": "病例系列/病例报告",
    "case report": "病例系列/病例报告",
    "case_series": "病例系列/病例报告",
    "case series": "病例系列/病例报告",
    "basic_research": "基础研究",
    "basic research": "基础研究",
    "mechanistic_research": "基础研究",
    "mechanistic research": "基础研究",
    "综述": "综述",
    "meta分析/系统性综述": "Meta分析/系统性综述",
    "meta分析": "Meta分析/系统性综述",
    "系统性综述": "Meta分析/系统性综述",
    "观察性研究": "观察性研究",
    "病例系列/病例报告": "病例系列/病例报告",
    "病例报告": "病例系列/病例报告",
    "基础研究": "基础研究",
}

DATA_TYPE_COMPOUNDS = {
    "Meta_Analysis/Systematic_Review": "Meta分析/系统性综述",
    "Case_Series/Case_Report": "病例系列/病例报告",
    "meta analysis/systematic review": "Meta分析/系统性综述",
    "case series/case report": "病例系列/病例报告",
}


def normalize_data_type_value(value: Any) -> str:
    labels: list[str] = []
    for item in split_values_loose(value):
        protected = normalize_value(item)
        placeholders: dict[str, str] = {}
        for idx, compound in enumerate(DATA_TYPE_COMPOUNDS):
            placeholder = f"__DT_COMPOUND_{idx}__"
            protected = re.sub(re.escape(compound), placeholder, protected, flags=re.I)
            placeholders[placeholder.casefold()] = DATA_TYPE_COMPOUNDS[compound]
        parts = [part for part in re.split(r"[/]+", protected) if part] if "/" in protected else [protected]
        for part in parts:
            key = re.sub(r"\s+", " ", normalize_value(part)).strip().casefold()
            mapped = placeholders.get(key) or DATA_TYPE_LABEL_MAP.get(key)
            if mapped and mapped not in labels:
                labels.append(mapped)
    return "；".join(labels)


def extract_data_type_marker_from_query(query: str) -> str:
    matches = re.findall(r"研究类型\s*[:：]\s*([^。；;\n]+)", query)
    if not matches:
        return ""
    return normalize_data_type_value("；".join(matches))


def split_production_authors(query: str, authors: Any) -> tuple[str, str]:
    """Split production author values into query-visible names and variants."""
    author_values = dedupe_keep_order(split_values(authors))
    if not author_values:
        return "", ""

    names = [value for value in author_values if appears_in_query(query, value)]
    if not names:
        return "", ""
    name_set = set(names)
    variants = [value for value in author_values if value not in name_set]
    return "；".join(names), "\n".join(f"<variant>{value}</variant>" for value in variants)


def read_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if limit is not None and idx >= limit:
                    break
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array or JSONL rows")
    return data[:limit] if limit is not None else data


def iter_rows(path: Path, limit: int | None = None) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if limit is not None and idx >= limit:
                    break
                if line.strip():
                    yield json.loads(line)
        return
    for row in read_rows(path, limit):
        yield row


def eval_row_to_task_example(row: dict[str, Any], task: str) -> dict[str, Any] | None:
    query = normalize_value(row.get("query") or row.get("question") or row.get("用户query"))
    if not query:
        return None
    normalized = {clean_answer_key(k): v for k, v in row.items()}
    targets = {field: normalize_value(normalized.get(field)) for field in TASK_TARGET_FIELDS[task]}
    return {"query": query, "task": task, "targets": targets, "source": "eval"}


def production_row_to_task_example(row: dict[str, Any], task: str) -> dict[str, Any] | None:
    query = normalize_value(row.get("query") or row.get("question") or row.get("用户query"))
    nlu = row.get("nlu") if isinstance(row.get("nlu"), dict) else {}
    if not query or not nlu:
        return None
    if task == "作者和机构":
        author_name, author_variants = split_production_authors(query, nlu.get("authors"))
        targets = {
            "author_name": author_name,
            "author_name英文变体": author_variants,
            "author_institution": filter_values_in_query(query, nlu.get("institutions") or nlu.get("institutions_en")),
        }
    elif task == "机构和国家":
        targets = {
            "机构名称": filter_institutions_in_query(query, nlu.get("institutions") or nlu.get("publishers")),
            "国家": filter_countries_in_query(query, nlu.get("countries") or nlu.get("countries_standardized")),
        }
    elif task == "时间和if值":
        targets = {
            "filter_start_datetime": normalize_value(nlu.get("publish_date_start") or nlu.get("trial_start_date_start")),
            "filter_end_datetime": normalize_value(nlu.get("publish_date_end") or nlu.get("trial_start_date_end")),
            "filter_start_if": normalize_value(nlu.get("if_min_value")),
            "filter_end_if": normalize_value(nlu.get("if_max_value")),
        }
    elif task == "data_type":
        data_type = normalize_data_type_value(nlu.get("research_types")) or extract_data_type_marker_from_query(query)
        targets = {"data_type": data_type}
    elif task == "topic和keywords":
        targets = {
            "topics": filter_topic_keyword_values_in_query(query, nlu.get("topics")),
            "keywords": filter_topic_keyword_values_in_query(query, nlu.get("keyword")),
        }
    else:
        return None
    return {"query": query, "task": task, "targets": targets, "source": "production"}


def has_signal(example: dict[str, Any]) -> bool:
    return bool(example.get("query"))


def has_task_output(example: dict[str, Any]) -> bool:
    return any(not is_empty_output_value(value) for value in example.get("targets", {}).values())


def reservoir_add(bucket: list[dict[str, Any]], item: dict[str, Any], seen_count: int, limit: int, rng: random.Random) -> None:
    if limit <= 0:
        return
    if len(bucket) < limit:
        bucket.append(item)
        return
    replace_idx = rng.randrange(seen_count)
    if replace_idx < limit:
        bucket[replace_idx] = item


def make_sft_row(example: dict[str, Any], prompt_file: Path) -> dict[str, str]:
    task = example["task"]
    targets = {field: example["targets"].get(field, "") for field in TASK_TARGET_FIELDS[task]}
    return {
        "instruction": sft_instruction(task, prompt_file),
        "input": example["query"],
        "output": json.dumps(targets, ensure_ascii=False, separators=(",", ":")),
    }


def find_spans(text: str, value: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    while value:
        idx = text.find(value, start)
        if idx < 0:
            break
        spans.append((idx, idx + len(value)))
        start = idx + len(value)
    return spans


def mark_span(labels: list[str], start: int, end: int, entity: str) -> bool:
    if start < 0 or end > len(labels) or start >= end:
        return False
    if any(label != "O" for label in labels[start:end]):
        return False
    labels[start] = f"B-{entity}"
    for idx in range(start + 1, end):
        labels[idx] = f"I-{entity}"
    return True


def make_bio_row(example: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]] | None:
    task = example["task"]
    if task not in BIO_TASKS:
        return None
    text = example["query"]
    labels = ["O"] * len(text)
    misses: dict[str, int] = {}
    visible_targets: dict[str, str] = {}
    for field, entity in BIO_LABEL_ENTITIES[task].items():
        misses[field] = 0
        visible_values: list[str] = []
        for value in split_values(example["targets"].get(field)):
            spans = find_spans(text, value)
            if not spans:
                misses[field] += 1
                continue
            marked = False
            for start, end in spans:
                marked = mark_span(labels, start, end, entity) or marked
            if marked:
                visible_values.append(value)
        visible_targets[field] = "；".join(dedupe_keep_order(visible_values))
    row = {
        "text": text,
        "char_labels": labels,
        "task": task,
        **{field: visible_targets.get(field, "") for field in TASK_TARGET_FIELDS[task]},
    }
    return row, misses


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_rows(rows: list[dict[str, Any]], seed: int, valid_ratio: float, test_ratio: float) -> dict[str, list[dict[str, Any]]]:
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    test_size = int(len(shuffled) * test_ratio)
    valid_size = int(len(shuffled) * valid_ratio)
    return {"test": shuffled[:test_size], "valid": shuffled[test_size : test_size + valid_size], "train": shuffled[test_size + valid_size :]}


def labels_for_task(task: str) -> list[str]:
    entities = list(BIO_LABEL_ENTITIES.get(task, {}).values())
    labels = ["O"]
    for entity in entities:
        labels.extend([f"B-{entity}", f"I-{entity}"])
    return labels


def prepare_task(task: str, examples: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    task_dir = args.output_dir / TASK_OUTPUT_NAMES[task]
    stats: dict[str, Any] = {
        "task": task,
        "total_examples": len(examples),
        "positive_examples": sum(1 for example in examples if example.get("is_positive")),
        "negative_examples": sum(1 for example in examples if not example.get("is_positive")),
        "formats": {},
    }
    if "sft" in args.formats:
        sft_rows = [make_sft_row(example, args.prompt_file) for example in examples]
        sft_splits = split_rows(sft_rows, args.seed, args.valid_ratio, args.test_ratio)
        for split, rows in sft_splits.items():
            write_jsonl(task_dir / "sft" / f"{split}.jsonl", rows)
        write_jsonl(task_dir / "sft" / "all.jsonl", sft_rows)
        stats["formats"]["sft"] = {name: len(rows) for name, rows in sft_splits.items()} | {"all": len(sft_rows)}
    if "bio" in args.formats and task in BIO_TASKS:
        bio_rows: list[dict[str, Any]] = []
        misses: dict[str, int] = {field: 0 for field in BIO_LABEL_ENTITIES[task]}
        for example in examples:
            result = make_bio_row(example)
            if result is None:
                continue
            row, row_misses = result
            bio_rows.append(row)
            for key, value in row_misses.items():
                misses[key] = misses.get(key, 0) + value
        bio_splits = split_rows(bio_rows, args.seed, args.valid_ratio, args.test_ratio)
        for split, rows in bio_splits.items():
            write_jsonl(task_dir / "bio" / f"{split}.jsonl", rows)
        write_jsonl(task_dir / "bio" / "all.jsonl", bio_rows)
        label_list = labels_for_task(task)
        (task_dir / "bio" / "label_list.json").write_text(json.dumps(label_list, ensure_ascii=False, indent=2), encoding="utf-8")
        stats["formats"]["bio"] = {**{name: len(rows) for name, rows in bio_splits.items()}, "all": len(bio_rows), "label_list": label_list, "missed_gold_spans": misses}
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def source_paths_for_args(args: argparse.Namespace) -> tuple[list[Path], str]:
    if args.input:
        return [Path(raw_path) for raw_path in args.input], args.source_format
    if args.source_format == "eval":
        return [args.eval_dir / TASK_FILES[task] for task in args.tasks], "eval"
    return [DEFAULT_PRODUCTION_JSONL], "production"


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    grouped_pos: dict[str, list[dict[str, Any]]] = {task: [] for task in args.tasks}
    grouped_neg: dict[str, list[dict[str, Any]]] = {task: [] for task in args.tasks}
    seen_pos: dict[str, int] = {task: 0 for task in args.tasks}
    seen_neg: dict[str, int] = {task: 0 for task in args.tasks}
    source_rows = 0
    input_paths, source_format = source_paths_for_args(args)
    for path in input_paths:
        if source_format == "eval":
            fixed_tasks = [task for task in args.tasks if path.name == TASK_FILES[task]]
            tasks_for_path = fixed_tasks or args.tasks
        else:
            tasks_for_path = args.tasks
        for row in iter_rows(path, args.limit):
            source_rows += 1
            for task in tasks_for_path:
                example = eval_row_to_task_example(row, task) if source_format == "eval" else production_row_to_task_example(row, task)
                if not example or not has_signal(example):
                    continue
                example["source_path"] = str(path)
                positive = has_task_output(example)
                example["is_positive"] = positive
                if positive:
                    seen_pos[task] += 1
                    reservoir_add(grouped_pos[task], example, seen_pos[task], args.positive_limit, rng)
                else:
                    seen_neg[task] += 1
                    reservoir_add(grouped_neg[task], example, seen_neg[task], args.negative_limit, rng)
    all_stats = []
    for task in args.tasks:
        examples = grouped_pos.get(task, []) + grouped_neg.get(task, [])
        random.Random(args.seed).shuffle(examples)
        stats = prepare_task(task, examples, args)
        stats["source_rows_scanned"] = source_rows
        stats["available_positive_examples"] = seen_pos.get(task, 0)
        stats["available_negative_examples"] = seen_neg.get(task, 0)
        stats["selected_positive_examples"] = len(grouped_pos.get(task, []))
        stats["selected_negative_examples"] = len(grouped_neg.get(task, []))
        stats_path = args.output_dir / TASK_OUTPUT_NAMES[task] / "stats.json"
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        all_stats.append(stats)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "prepare_stats.json").write_text(json.dumps(all_stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
