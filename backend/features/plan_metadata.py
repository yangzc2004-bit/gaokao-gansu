from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable


POLICY_RULES_PATH = Path("configs/policy_rules.gansu.json")

# Selectable groups shown in the frontend. Hidden tags still participate in
# rule evaluation and text matching through `ALL_PLAN_GROUPS`.
PLAN_GROUPS: dict[str, list[str]] = {
    "国家专项": ["国家专项"],
    "地方专项": ["地方专项"],
    "高校专项": ["高校专项"],
    "建档立卡专项": ["建档立卡专项(本科)", "建档立卡专项(专科)"],
    "革命老区专项": ["革命老区专项"],
    "两州一县专项": ["两州一县专项"],
    "少数民族专项": ["藏区专项-民语类", "藏区专项-其他类", "其他民族地区专项"],
    "农村免费医学生（省属）": ["省属免费医学生(本科)", "省属免费医学生(专科)"],
    "农村免费医学生（国家）": ["国家免费医学生"],
    "公费师范生": ["国家公费师范生", "省属公费师范生"],
    "市级定向培养": ["市级定向培养"],
    "少数民族预科班": ["少数民族预科班"],
    "民族班": ["民族班"],
    "边防军人子女预科": ["边防军人子女预科"],
    "强基计划": ["强基计划"],
    "综合评价录取": ["综合评价录取"],
}

HIDDEN_PLAN_GROUPS: dict[str, list[str]] = {
    "农村学生专项": ["农村学生专项"],
}

ALL_PLAN_GROUPS: dict[str, list[str]] = {
    **PLAN_GROUPS,
    **HIDDEN_PLAN_GROUPS,
}

PLAN_GROUP_ORDER = list(PLAN_GROUPS.keys())
SUBTAG_TO_GROUP = {tag: group for group, tags in ALL_PLAN_GROUPS.items() for tag in tags}

PLAN_MATCH_PATTERNS: dict[str, tuple[tuple[str, ...], ...]] = {
    "国家专项": (("国家专项计划",), ("国家专项",)),
    "地方专项": (("地方专项计划",), ("地方专项",)),
    "高校专项": (("高校专项计划",), ("高校专项",)),
    "建档立卡专项": (("建档立卡专项",), ("建档立卡",)),
    "建档立卡专项(本科)": (("建档立卡专项(本科)",), ("建档立卡", "本科")),
    "建档立卡专项(专科)": (("建档立卡专项(专科)",), ("建档立卡", "专科")),
    "革命老区专项": (("革命老区专项",), ("革命老区",)),
    "两州一县专项": (("两州一县专项",), ("两州一县",)),
    "少数民族专项": (("少数民族专项",), ("藏区专项",), ("其他民族地区专项",)),
    "藏区专项-民语类": (("藏区专项-民语类",), ("藏区专项", "民语")),
    "藏区专项-其他类": (("藏区专项-其他类",), ("藏区专项", "其他")),
    "其他民族地区专项": (("其他民族地区专项",),),
    "农村免费医学生（省属）": (("省属免费医学生",), ("免费医学生", "省属")),
    "农村免费医学生（国家）": (("国家免费医学生",), ("免费医学生", "国家")),
    "省属免费医学生(本科)": (("省属免费医学生(本科)",), ("免费医学生", "省属", "本科")),
    "省属免费医学生(专科)": (("省属免费医学生(专科)",), ("免费医学生", "省属", "专科")),
    "国家免费医学生": (("国家免费医学生",), ("免费医学生", "国家")),
    "公费师范生": (("公费师范生",), ("国家公费师范",), ("省属公费师范",)),
    "国家公费师范生": (("国家公费师范生",), ("国家公费师范",)),
    "省属公费师范生": (("省属公费师范生",), ("省属公费师范",), ("公费师范", "省属")),
    "市级定向培养": (("市级定向培养",), ("定向培养", "市级")),
    "少数民族预科班": (("少数民族预科班",), ("少数民族预科",)),
    "民族班": (("民族班",),),
    "边防军人子女预科": (("边防军人子女预科",), ("边防军人子女", "预科")),
    "强基计划": (("强基计划",),),
    "综合评价录取": (("综合评价录取",), ("综合评价",)),
    "农村学生专项": (("农村学生专项",), ("农村学生", "专项")),
}


def normalize_plan_text(value: str | None) -> str:
    return str(value or "").replace("（", "(").replace("）", ")").replace(" ", "").strip()


def get_plan_patterns(tag: str) -> tuple[tuple[str, ...], ...]:
    patterns = PLAN_MATCH_PATTERNS.get(tag)
    if not patterns:
        normalized = normalize_plan_text(tag)
        if not normalized:
            return tuple()
        return ((normalized,),)

    normalized_patterns: list[tuple[str, ...]] = []
    for pattern in patterns:
        tokens = tuple(token for token in (normalize_plan_text(item) for item in pattern) if token)
        if tokens:
            normalized_patterns.append(tokens)
    return tuple(normalized_patterns)


def text_matches_plan_tag(tag: str, text: str | None) -> bool:
    normalized_text = normalize_plan_text(text)
    if not normalized_text:
        return False
    return any(all(token in normalized_text for token in pattern) for pattern in get_plan_patterns(tag))


def infer_plan_tags_from_text(text: str | None, allowed_tags: Iterable[str]) -> list[str]:
    matched: list[str] = []
    for tag in allowed_tags:
        if tag and text_matches_plan_tag(str(tag), text):
            matched.append(str(tag))
    return list(dict.fromkeys(matched))


def infer_plan_groups_from_text(text: str | None, groups: Iterable[str] | None = None) -> list[str]:
    matched: list[str] = []
    group_pool = list(groups) if groups is not None else list(PLAN_GROUPS.keys())
    for group in group_pool:
        if group and text_matches_plan_tag(str(group), text):
            matched.append(str(group))
            continue
        for tag in ALL_PLAN_GROUPS.get(str(group), []):
            if text_matches_plan_tag(tag, text):
                matched.append(str(group))
                break
    return list(dict.fromkeys(matched))


def infer_plan_groups_from_tags(tags: Iterable[str]) -> list[str]:
    groups = [SUBTAG_TO_GROUP.get(str(tag), str(tag)) for tag in tags if str(tag)]
    return list(dict.fromkeys(groups))


def expand_plan_groups(selected_plan_groups: Iterable[str] | None) -> list[str]:
    expanded: list[str] = []
    for group in selected_plan_groups or []:
        group_name = str(group)
        if not group_name:
            continue
        if group_name in ALL_PLAN_GROUPS:
            expanded.extend(ALL_PLAN_GROUPS[group_name])
            continue
        expanded.append(group_name)
    return list(dict.fromkeys(expanded))


@lru_cache(maxsize=4)
def load_policy_plan_catalog(path: str = str(POLICY_RULES_PATH)) -> list[dict[str, str | dict]]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    plans: list[dict[str, str | dict]] = []
    for plan in data.get("plans", []):
        source_section = str(plan.get("source_section") or "").strip()
        if source_section.startswith("17"):
            continue
        tag = str(plan.get("plan_tag") or "").strip()
        if not tag:
            continue
        plans.append(
            {
                "plan_tag": tag,
                "batch_code": str(plan.get("batch_code") or "").strip(),
                "source_section": source_section,
                "rules": plan.get("rules") or {},
            }
        )

    def sort_key(item: dict[str, str | dict]) -> tuple[int, str]:
        raw = str(item.get("source_section") or "")
        head = raw.split(".", 1)[0]
        try:
            return (int(head), raw)
        except ValueError:
            return (999, raw)

    return sorted(plans, key=sort_key)


PLAN_CATALOG = load_policy_plan_catalog()
PLAN_BY_TAG = {str(plan["plan_tag"]): plan for plan in PLAN_CATALOG}
PLAN_BATCH = {str(plan["plan_tag"]): str(plan.get("batch_code") or "") for plan in PLAN_CATALOG}


def build_group_batch(tags: Iterable[str]) -> str:
    seen: set[str] = set()
    batches: list[str] = []
    for tag in tags:
        batch = PLAN_BATCH.get(str(tag), "")
        if batch and batch not in seen:
            batches.append(batch)
            seen.add(batch)
    return " / ".join(batches)


PLAN_GROUP_BATCH = {group: build_group_batch(tags) for group, tags in PLAN_GROUPS.items()}
ALL_PLAN_GROUP_BATCH = {group: build_group_batch(tags) for group, tags in ALL_PLAN_GROUPS.items()}
