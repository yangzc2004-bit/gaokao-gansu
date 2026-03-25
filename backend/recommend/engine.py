from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.features.plan_metadata import expand_plan_groups, infer_plan_tags_from_text
from backend.features.policy_bonus import score_policy_bonus
from backend.features.subject_parser import subject_expression_match
from backend.models.schemas import UserProfile
from backend.predict.probability import derive_target_rank, estimate_admission_probability, probability_label
from backend.recommend.ranker import classify_bucket, compute_rank_cv
from backend.rules.eligibility import PolicyEngine


PROBABILITY_THRESHOLDS = {"冲": 0.25, "稳": 0.50, "保": 0.70}
RESULT_BUCKETS = ["冲", "稳", "保", "政策红利"]


def _file_cache_key(path: str) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return (str(resolved), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4)
def _load_records_cached(records_key: tuple[str, int, int]) -> pd.DataFrame:
    records_path, _, _ = records_key
    return pd.read_csv(records_path)


@lru_cache(maxsize=4)
def _load_metrics_cached(metrics_key: tuple[str, int, int]) -> pd.DataFrame:
    metrics_path, _, _ = metrics_key
    return pd.read_csv(metrics_path)


@lru_cache(maxsize=4)
def _build_candidate_features_cached(
    records_key: tuple[str, int, int],
    metrics_key: tuple[str, int, int],
) -> pd.DataFrame:
    records = _load_records_cached(records_key)
    metrics = _load_metrics_cached(metrics_key)
    return build_candidate_features(records, metrics)


def load_records(records_path: str) -> pd.DataFrame:
    return _load_records_cached(_file_cache_key(records_path)).copy()


def load_metrics(metrics_path: str) -> pd.DataFrame:
    return _load_metrics_cached(_file_cache_key(metrics_path)).copy()


def build_candidate_features(records: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    metrics_agg = (
        metrics.groupby("record_id", as_index=False)
        .agg(
            avg_rank_3y=("avg_rank", "mean"),
            min_rank_3y=("min_rank", "mean"),
            max_rank_3y=("max_rank", "mean"),
            years_available=("min_rank", lambda s: int(s.notna().sum())),
            latest_min_rank=("min_rank", "first"),
            latest_avg_rank=("avg_rank", "first"),
            latest_max_rank=("max_rank", "first"),
        )
    )

    cv_df = metrics.groupby("record_id")["min_rank"].apply(compute_rank_cv).reset_index(name="rank_cv")
    return records.merge(metrics_agg, on="record_id", how="left").merge(cv_df, on="record_id", how="left")


def build_recommend_reason(row: pd.Series) -> str:
    reasons: list[str] = []

    years_available = int(row.get("years_available") or 0)
    if years_available >= 3:
        reasons.append("近3年历史数据较完整")
    elif years_available == 2:
        reasons.append("仅有2年历史数据，已保守降权")
    elif years_available == 1:
        reasons.append("仅有1年历史数据，已明显保守处理")

    ratio = row.get("rank_ratio")
    if pd.notna(ratio):
        ratio_value = float(ratio)
        if ratio_value < 1.0:
            reasons.append("当前位次略高于目标位次，存在冲刺空间")
        elif ratio_value <= 1.08:
            reasons.append("当前位次与目标位次接近，匹配度较稳")
        else:
            reasons.append("当前位次优于目标位次，安全边际较大")

    plan_count = float(row.get("plan_count") or 0)
    group_plan_count = float(row.get("group_plan_count") or 0)
    if plan_count > 0 and group_plan_count > 0:
        plan_ratio = plan_count / group_plan_count
        if plan_ratio <= 0.08:
            reasons.append("专业计划名额偏少，系统已从严评估")
        elif plan_ratio >= 0.35:
            reasons.append("专业计划占比较高，录取稳定性略好")

    if str(row.get("is_new_major") or "").strip() == "新增":
        reasons.append("新增专业历史样本不足，系统已保守处理")

    if float(row.get("policy_bonus") or 0) > 0:
        reasons.append("专项政策匹配带来一定加权")

    return "；".join(reasons[:4])


def infer_matched_plan_tags(row: pd.Series, eligible_plan_tags: list[str]) -> list[str]:
    text_parts = [
        row.get("admission_type"),
        row.get("group_name"),
        row.get("major_name"),
        row.get("major_note"),
        row.get("batch"),
        row.get("school_name"),
    ]
    combined = " ".join(str(part) for part in text_parts if pd.notna(part))
    return infer_plan_tags_from_text(combined, eligible_plan_tags)


def format_frontend_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "school_name": item.get("school_name"),
        "major_name": item.get("major_name"),
        "group_name": item.get("group_name"),
        "batch": item.get("batch"),
        "track": item.get("track"),
        "school_level": item.get("school_level"),
        "subject_requirement": item.get("subject_requirement_raw"),
        "risk_level": item.get("bucket"),
        "score": {
            "admission_probability": item.get("admission_probability"),
            "admission_probability_label": item.get("admission_probability_label"),
            "target_rank": item.get("target_rank"),
            "rank_ratio": item.get("rank_ratio"),
            "rank_match_score": item.get("rank_match_score"),
            "rank_cv": item.get("rank_cv"),
        },
        "history": {
            "years_available": item.get("years_available"),
            "history_penalty": item.get("history_penalty"),
            "avg_rank_3y": item.get("avg_rank_3y"),
            "min_rank_3y": item.get("min_rank_3y"),
            "max_rank_3y": item.get("max_rank_3y"),
        },
        "plan": {
            "plan_count": item.get("plan_count"),
            "group_plan_count": item.get("group_plan_count"),
            "is_new_major": item.get("is_new_major"),
        },
        "policy_bonus": item.get("policy_bonus"),
        "effective_policy_bonus": item.get("effective_policy_bonus"),
        "matched_plan_tags": item.get("matched_plan_tags") or [],
        "all_matched_plan_tags": item.get("all_matched_plan_tags") or [],
        "recommend_reason": item.get("recommend_reason"),
    }


def build_frontend_response(result: dict[str, list[dict[str, Any]]], profile: UserProfile) -> dict[str, Any]:
    return {
        "query": {
            "track": profile.track,
            "selected_subjects": profile.selected_subjects,
            "score": profile.score,
            "rank": profile.rank,
            "region": profile.region,
            "selected_plan_groups": profile.selected_plan_groups or [],
        },
        "summary": {
            "thresholds": PROBABILITY_THRESHOLDS,
            "counts": {bucket: len(result.get(bucket, [])) for bucket in RESULT_BUCKETS},
        },
        "results": {
            bucket: [format_frontend_item(item) for item in result.get(bucket, [])]
            for bucket in RESULT_BUCKETS
        },
    }


def recommend(
    records_path: str,
    metrics_path: str,
    rules_path: str,
    region_path: str,
    profile: UserProfile,
    selected_plan_groups: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    candidate_key = (_file_cache_key(records_path), _file_cache_key(metrics_path))
    candidate_features = _build_candidate_features_cached(*candidate_key)

    engine = PolicyEngine(rules_path, region_path)
    eligible_results = engine.evaluate_all(profile)
    eligible_plan_tags = [item.plan_tag for item in eligible_results if item.eligible]
    selected_groups = selected_plan_groups if selected_plan_groups is not None else (profile.selected_plan_groups or [])
    selected_tag_whitelist = set(expand_plan_groups(selected_groups))
    selected_filter_enabled = bool(selected_tag_whitelist)

    candidates = candidate_features[candidate_features["track"] == profile.track].copy()
    candidates = candidates[
        candidates["subject_requirement_raw"].fillna("不限").map(
            lambda x: subject_expression_match(str(x), [profile.track, *profile.selected_subjects])
        )
    ]

    candidates["target_rank"] = [
        derive_target_rank(
            int(row.get("years_available") or 0),
            row.get("latest_min_rank"),
            row.get("latest_avg_rank"),
            row.get("latest_max_rank"),
            row.get("min_rank_3y"),
            row.get("avg_rank_3y"),
            row.get("max_rank_3y"),
            row.get("plan_count"),
            row.get("group_plan_count"),
            row.get("is_new_major"),
        )
        for _, row in candidates.iterrows()
    ]
    candidates = candidates[candidates["target_rank"].notna()].copy()

    if profile.rank:
        candidates["rank_ratio"] = candidates["target_rank"] / float(profile.rank)
        candidates["bucket"] = candidates["target_rank"].map(lambda x: classify_bucket(float(x), float(profile.rank)))
        candidates = candidates[candidates["bucket"].notna()].copy()
    else:
        candidates["rank_ratio"] = None
        candidates["bucket"] = "稳"

    candidates["all_matched_plan_tags"] = [
        infer_matched_plan_tags(row, eligible_plan_tags)
        for _, row in candidates.iterrows()
    ]
    candidates["matched_plan_tags"] = [
        [tag for tag in tags if (not selected_filter_enabled or tag in selected_tag_whitelist)]
        for tags in candidates["all_matched_plan_tags"]
    ]
    candidates["policy_bonus"] = [
        score_policy_bonus(row.get("all_matched_plan_tags") or [], float(row.get("rank_cv") or 0), row.get("school_level"))
        for _, row in candidates.iterrows()
    ]
    candidates["effective_policy_bonus"] = [
        score_policy_bonus(row.get("matched_plan_tags") or [], float(row.get("rank_cv") or 0), row.get("school_level"))
        for _, row in candidates.iterrows()
    ]
    candidates["rank_match_score"] = candidates["rank_ratio"].map(
        lambda x: None if pd.isna(x) else max(0.0, min(1.0, (x - 0.8) / 0.55))
    )
    candidates["admission_probability"] = [
        estimate_admission_probability(
            float(profile.rank) if profile.rank else 0,
            row.get("target_rank"),
            row.get("rank_cv"),
            int(row.get("years_available") or 0),
            row.get("latest_min_rank"),
            row.get("latest_avg_rank"),
            row.get("latest_max_rank"),
        )
        for _, row in candidates.iterrows()
    ]
    candidates["rank_cv"] = pd.to_numeric(candidates["rank_cv"], errors="coerce")
    candidates["rank_match_score"] = pd.to_numeric(candidates["rank_match_score"], errors="coerce")
    candidates["admission_probability"] = pd.to_numeric(candidates["admission_probability"], errors="coerce")
    candidates["admission_probability_label"] = candidates["admission_probability"].map(probability_label)
    candidates["history_penalty"] = candidates["years_available"].map(lambda x: 0 if x >= 3 else (4 if x == 2 else 8))
    candidates["recommend_reason"] = [build_recommend_reason(row) for _, row in candidates.iterrows()]
    candidates["score_value"] = (
        candidates["policy_bonus"]
        - candidates["rank_cv"].fillna(0) * 100
        + candidates["rank_match_score"].fillna(0) * 10
        + candidates["admission_probability"].fillna(0) * 20
        - candidates["history_penalty"].fillna(0)
    )
    candidates["has_any_plan_match"] = candidates["all_matched_plan_tags"].map(bool)
    candidates["has_effective_plan_match"] = candidates["matched_plan_tags"].map(bool)

    result: dict[str, list[dict[str, Any]]] = {}
    for bucket in ["冲", "稳", "保"]:
        subset = candidates[
            (candidates["bucket"] == bucket)
            & (candidates["admission_probability"] >= PROBABILITY_THRESHOLDS[bucket])
        ].sort_values(["score_value", "avg_rank_3y"], ascending=[False, True])
        result[bucket] = subset.to_dict(orient="records")

    if selected_filter_enabled:
        policy_subset = candidates[
            (candidates["admission_probability"] >= 0.10)
            & (candidates["has_effective_plan_match"])
        ].sort_values(["effective_policy_bonus", "avg_rank_3y"], ascending=[False, True])
    else:
        policy_subset = candidates[
            (candidates["admission_probability"] >= 0.10)
            & (candidates["has_any_plan_match"])
        ].sort_values(["policy_bonus", "avg_rank_3y"], ascending=[False, True])

    result["政策红利"] = policy_subset.to_dict(orient="records")
    return result


def recommend_for_frontend(
    records_path: str,
    metrics_path: str,
    rules_path: str,
    region_path: str,
    profile: UserProfile,
    selected_plan_groups: list[str] | None = None,
) -> dict[str, Any]:
    if selected_plan_groups is not None:
        profile.selected_plan_groups = list(dict.fromkeys(selected_plan_groups))
    result = recommend(
        records_path,
        metrics_path,
        rules_path,
        region_path,
        profile,
        selected_plan_groups=selected_plan_groups,
    )
    return build_frontend_response(result, profile)


if __name__ == "__main__":
    profile = UserProfile(
        track="历史",
        selected_subjects=["政治", "地理"],
        rank=5000,
        region="会宁县",
        hukou_nature="rural_only",
        nation="汉族",
        school_years=3,
        hukou_years=3,
        parent_hukou_years=3,
    )
    data = recommend(
        "data/processed/admission_records.csv",
        "data/processed/admission_metrics_long.csv",
        "configs/policy_rules.gansu.json",
        "configs/region_dict.gansu.json",
        profile,
    )
    print(json.dumps({key: len(value) for key, value in data.items()}, ensure_ascii=False, indent=2))
