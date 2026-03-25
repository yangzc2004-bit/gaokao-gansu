from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.features.plan_metadata import infer_plan_tags_from_text
from backend.models.schemas import UserProfile
from backend.recommend.engine import recommend_for_frontend


RECORDS_PATH = ROOT / "data/processed/admission_records.csv"
METRICS_PATH = ROOT / "data/processed/admission_metrics_long.csv"
RULES_PATH = ROOT / "configs/policy_rules.gansu.json"
REGION_PATH = ROOT / "configs/region_dict.gansu.json"
REPORT_JSON_PATH = ROOT / "data/processed/edge_validation_report.json"
REPORT_MD_PATH = ROOT / "docs/edge-validation-report.md"

BASE_PROFILES = [
    UserProfile(track="历史", selected_subjects=["政治", "地理"], score=580, rank=3000, region="兰州市"),
    UserProfile(track="历史", selected_subjects=["政治", "地理"], score=560, rank=5000, region="会宁县"),
    UserProfile(track="物理", selected_subjects=["化学", "生物"], score=500, rank=15000, region="兰州市"),
    UserProfile(track="历史", selected_subjects=["政治", "地理"], score=500, rank=12000, region="天水市"),
]

STRICT_LOCAL_PROFILE = UserProfile(
    track="历史",
    selected_subjects=["政治", "地理"],
    score=560,
    rank=5000,
    region="会宁县",
    hukou_nature="rural_only",
    nation="汉族",
    school_years=3,
    hukou_years=3,
    parent_hukou_years=3,
)

STRICT_MINORITY_PROFILE = UserProfile(
    track="历史",
    selected_subjects=["政治", "地理"],
    score=520,
    rank=8000,
    region="东乡族自治县",
    hukou_nature="rural_only",
    nation="回族",
    school_years=3,
    hukou_years=3,
    parent_hukou_years=3,
)


def run_profile(profile: UserProfile, selected_plan_groups: list[str] | None = None) -> dict[str, Any]:
    return recommend_for_frontend(
        str(RECORDS_PATH),
        str(METRICS_PATH),
        str(RULES_PATH),
        str(REGION_PATH),
        profile,
        selected_plan_groups=selected_plan_groups,
    )


def iter_items(results: list[dict[str, Any]]):
    for result in results:
        for bucket in ["冲", "稳", "保", "政策红利"]:
            for item in result.get("results", {}).get(bucket, []):
                yield bucket, item


def find_first(results: list[dict[str, Any]], predicate):
    for bucket, item in iter_items(results):
        if predicate(bucket, item):
            return bucket, item
    return None, None


def get_policy_items(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(result.get("results", {}).get("政策红利", []) or [])


def all_policy_items_within(result: dict[str, Any], allowed_groups: set[str]) -> bool:
    items = get_policy_items(result)
    if not items:
        return False
    for item in items:
        matched = set(item.get("matched_plan_tags") or [])
        if not matched or not matched.issubset(allowed_groups):
            return False
    return True


def first_sample_text(keyword: str) -> str | None:
    df = pd.read_csv(
        RECORDS_PATH,
        usecols=["admission_type", "group_name", "major_name", "batch", "school_name"],
    ).fillna("")
    matched = df[df["admission_type"].astype(str).str.contains(keyword, na=False)]
    if matched.empty:
        return None
    row = matched.iloc[0]
    return " ".join(str(row[column]) for column in ["admission_type", "group_name", "major_name", "batch", "school_name"])


def build_checks(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    bucket, item = find_first(results, lambda bucket, item: item.get("history", {}).get("years_available") == 1)
    checks.append(
        {
            "name": "1年样本保守处理",
            "status": "pass"
            if item and item.get("history", {}).get("history_penalty") == 8 and (item.get("score", {}).get("admission_probability") or 0) <= 0.78
            else "warn",
            "detail": None
            if not item
            else {
                "bucket": bucket,
                "school_name": item.get("school_name"),
                "major_name": item.get("major_name"),
                "history_penalty": item.get("history", {}).get("history_penalty"),
                "admission_probability": item.get("score", {}).get("admission_probability"),
            },
        }
    )

    bucket, item = find_first(results, lambda bucket, item: item.get("history", {}).get("years_available") == 2)
    checks.append(
        {
            "name": "2年样本保守降权",
            "status": "pass" if item and item.get("history", {}).get("history_penalty") == 4 else "warn",
            "detail": None
            if not item
            else {
                "bucket": bucket,
                "school_name": item.get("school_name"),
                "major_name": item.get("major_name"),
                "history_penalty": item.get("history", {}).get("history_penalty"),
            },
        }
    )

    bucket, item = find_first(results, lambda bucket, item: item.get("plan", {}).get("is_new_major") == "新增")
    checks.append(
        {
            "name": "新增专业解释提示",
            "status": "pass" if item and "新增专业历史样本不足" in (item.get("recommend_reason") or "") else "warn",
            "detail": None
            if not item
            else {
                "bucket": bucket,
                "school_name": item.get("school_name"),
                "major_name": item.get("major_name"),
                "recommend_reason": item.get("recommend_reason"),
            },
        }
    )

    bucket, item = find_first(
        results,
        lambda bucket, item: (item.get("plan", {}).get("group_plan_count") or 0) > 0
        and ((item.get("plan", {}).get("plan_count") or 0) / (item.get("plan", {}).get("group_plan_count") or 1)) <= 0.08,
    )
    checks.append(
        {
            "name": "低计划名额从严评估提示",
            "status": "pass" if item and "专业计划名额偏少" in (item.get("recommend_reason") or "") else "warn",
            "detail": None
            if not item
            else {
                "bucket": bucket,
                "school_name": item.get("school_name"),
                "major_name": item.get("major_name"),
                "recommend_reason": item.get("recommend_reason"),
            },
        }
    )

    bucket, item = find_first(results, lambda bucket, item: item.get("risk_level") != bucket and bucket != "政策红利")
    checks.append(
        {
            "name": "风险档与分桶一致性",
            "status": "pass" if item is None else "warn",
            "detail": None
            if not item
            else {
                "bucket": bucket,
                "risk_level": item.get("risk_level"),
                "school_name": item.get("school_name"),
            },
        }
    )

    no_rank_result = run_profile(UserProfile(track="历史", selected_subjects=["政治", "地理"], score=560, rank=None, region="会宁县"))
    no_rank_counts = no_rank_result.get("summary", {}).get("counts", {})
    checks.append(
        {
            "name": "无位次输入处理",
            "status": "pass" if sum(no_rank_counts.values()) == 0 else "warn",
            "detail": {
                "counts": no_rank_counts,
                "note": "前端已要求必须填写位次，不进入正式推荐。",
            },
        }
    )

    local_only_result = run_profile(STRICT_LOCAL_PROFILE, ["地方专项"])
    local_policy_items = get_policy_items(local_only_result)
    checks.append(
        {
            "name": "仅勾地方专项时严格只出地方专项",
            "status": "pass" if all_policy_items_within(local_only_result, {"地方专项"}) else "warn",
            "detail": {
                "policy_count": len(local_policy_items),
                "top_matches": [item.get("matched_plan_tags") for item in local_policy_items[:5]],
            },
        }
    )

    minority_only_result = run_profile(STRICT_MINORITY_PROFILE, ["民族班", "少数民族预科班"])
    minority_policy_items = get_policy_items(minority_only_result)
    minority_ok = bool(minority_policy_items) and all(
        set(item.get("matched_plan_tags") or []).issubset({"民族班", "少数民族预科班"})
        and not set(item.get("matched_plan_tags") or []).intersection({"国家专项", "地方专项"})
        for item in minority_policy_items
    )
    checks.append(
        {
            "name": "民族班和少数民族预科班不会串出国家/地方专项",
            "status": "pass" if minority_ok else "warn",
            "detail": {
                "policy_count": len(minority_policy_items),
                "top_matches": [item.get("matched_plan_tags") for item in minority_policy_items[:8]],
            },
        }
    )

    multi_plan_result = run_profile(STRICT_MINORITY_PROFILE, ["地方专项", "民族班", "少数民族预科班"])
    multi_plan_items = get_policy_items(multi_plan_result)
    checks.append(
        {
            "name": "多计划勾选时结果仅来自勾选集合",
            "status": "pass"
            if multi_plan_items
            and all(
                set(item.get("matched_plan_tags") or []).issubset({"地方专项", "民族班", "少数民族预科班"})
                for item in multi_plan_items
            )
            else "warn",
            "detail": {
                "policy_count": len(multi_plan_items),
                "top_matches": [item.get("matched_plan_tags") for item in multi_plan_items[:8]],
            },
        }
    )

    no_selection_result = run_profile(STRICT_MINORITY_PROFILE)
    checks.append(
        {
            "name": "未勾选计划时政策红利仍可正常展示",
            "status": "pass" if len(get_policy_items(no_selection_result)) > 0 else "warn",
            "detail": {
                "policy_count": len(get_policy_items(no_selection_result)),
                "top_matches": [item.get("matched_plan_tags") for item in get_policy_items(no_selection_result)[:5]],
            },
        }
    )

    minority_sample = first_sample_text("少数民族预科")
    minority_sample_match = infer_plan_tags_from_text(minority_sample, ["少数民族预科班"]) if minority_sample else []
    checks.append(
        {
            "name": "少数民族预科文本可识别为少数民族预科班",
            "status": "pass" if minority_sample and minority_sample_match == ["少数民族预科班"] else "warn",
            "detail": {"sample_text": minority_sample, "matched_tags": minority_sample_match},
        }
    )

    national_sample = first_sample_text("国家专项")
    local_sample = first_sample_text("地方专项")
    ethnic_sample = first_sample_text("民族班")
    national_match = infer_plan_tags_from_text(national_sample, ["国家专项", "地方专项", "民族班"]) if national_sample else []
    local_match = infer_plan_tags_from_text(local_sample, ["国家专项", "地方专项", "民族班"]) if local_sample else []
    ethnic_match = infer_plan_tags_from_text(ethnic_sample, ["国家专项", "地方专项", "民族班"]) if ethnic_sample else []
    checks.append(
        {
            "name": "国家专项/地方专项/民族班标签互不串组",
            "status": "pass"
            if national_match == ["国家专项"] and local_match == ["地方专项"] and ethnic_match == ["民族班"]
            else "warn",
            "detail": {
                "national_match": national_match,
                "local_match": local_match,
                "ethnic_match": ethnic_match,
            },
        }
    )

    return checks


def render_markdown(checks: list[dict[str, Any]]) -> str:
    lines = ["# 边界场景验证报告", "", "本报告由 `backend/eval/edge_validation.py` 自动生成。", ""]
    for check in checks:
        status = "通过" if check["status"] == "pass" else "关注"
        lines.append(f"## {check['name']}：{status}")
        detail = check.get("detail")
        if detail is None:
            lines.append("- 未找到对应样本，建议后续补专项样本继续复核。")
        else:
            lines.append(f"- 详情：`{json.dumps(detail, ensure_ascii=False)}`")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    results = [run_profile(profile) for profile in BASE_PROFILES]
    checks = build_checks(results)
    REPORT_JSON_PATH.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(checks), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON_PATH), "markdown": str(REPORT_MD_PATH)}, ensure_ascii=False))
