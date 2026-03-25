from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from backend.predict.probability import derive_target_rank, estimate_admission_probability
from backend.recommend.ranker import classify_bucket, compute_rank_cv


PROBABILITY_THRESHOLDS = {"冲": 0.25, "稳": 0.50, "保": 0.70}
SIMULATION_FACTORS = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]


def load_records(records_path: str) -> pd.DataFrame:
    return pd.read_csv(records_path)


def load_metrics(metrics_path: str) -> pd.DataFrame:
    return pd.read_csv(metrics_path)


def build_backtest_samples(records: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    record_fields = records[["record_id", "track", "school_name", "major_name", "plan_count", "group_plan_count", "is_new_major"]].copy()
    metric_groups = metrics.groupby("record_id")

    rows: list[dict[str, Any]] = []
    for record_id, group in metric_groups:
        actual_row = group[group["metric_slot"] == 1]
        if actual_row.empty:
            continue

        actual_row = actual_row.iloc[0]
        actual_min_rank = actual_row.get("min_rank")
        if pd.isna(actual_min_rank):
            continue

        history = group[group["metric_slot"].isin([2, 3])].copy().sort_values("metric_slot")
        history = history[history[["min_rank", "avg_rank", "max_rank"]].notna().any(axis=1)]
        if history.empty:
            continue

        years_available = int(history["min_rank"].notna().sum())
        if years_available <= 0:
            continue

        latest_history = history.iloc[0]
        latest_min_rank = latest_history.get("min_rank")
        latest_avg_rank = latest_history.get("avg_rank")
        latest_max_rank = latest_history.get("max_rank")
        min_rank_hist = history["min_rank"].mean()
        avg_rank_hist = history["avg_rank"].mean()
        max_rank_hist = history["max_rank"].mean()
        rank_cv = compute_rank_cv(history["min_rank"])

        record_info = record_fields[record_fields["record_id"] == record_id]
        if record_info.empty:
            continue
        record_info = record_info.iloc[0]

        target_rank = derive_target_rank(
            years_available,
            latest_min_rank,
            latest_avg_rank,
            latest_max_rank,
            min_rank_hist,
            avg_rank_hist,
            max_rank_hist,
            record_info.get("plan_count"),
            record_info.get("group_plan_count"),
            record_info.get("is_new_major"),
        )
        if target_rank is None:
            continue

        for factor in SIMULATION_FACTORS:
            user_rank = float(actual_min_rank) * factor
            admission_probability = estimate_admission_probability(
                user_rank,
                target_rank,
                rank_cv,
                years_available,
                latest_min_rank,
                latest_avg_rank,
                latest_max_rank,
            )
            bucket = classify_bucket(float(target_rank), float(user_rank))
            actual_admit = int(user_rank <= float(actual_min_rank))
            threshold = PROBABILITY_THRESHOLDS.get(bucket) if bucket else None
            recommended = bool(bucket and threshold is not None and admission_probability >= threshold)

            rows.append(
                {
                    "record_id": record_id,
                    "track": record_info.get("track"),
                    "school_name": record_info.get("school_name"),
                    "major_name": record_info.get("major_name"),
                    "history_years": years_available,
                    "actual_min_rank": float(actual_min_rank),
                    "target_rank": float(target_rank),
                    "user_rank": float(user_rank),
                    "simulation_factor": factor,
                    "rank_cv": float(rank_cv),
                    "predicted_probability": float(admission_probability),
                    "bucket": bucket,
                    "actual_admit": actual_admit,
                    "recommended": recommended,
                }
            )

    return pd.DataFrame(rows)


def summarize_backtest(samples: pd.DataFrame) -> dict[str, Any]:
    if samples.empty:
        return {"sample_count": 0}

    summary: dict[str, Any] = {
        "sample_count": int(len(samples)),
        "record_count": int(samples["record_id"].nunique()),
    }

    by_years = (
        samples.groupby("history_years")
        .agg(
            sample_count=("actual_admit", "size"),
            admit_rate=("actual_admit", "mean"),
            avg_probability=("predicted_probability", "mean"),
            recommend_rate=("recommended", "mean"),
        )
        .reset_index()
    )
    summary["by_history_years"] = by_years.to_dict(orient="records")

    bucket_samples = samples[samples["bucket"].notna()].copy()
    bucket_stats = (
        bucket_samples.groupby("bucket")
        .agg(
            sample_count=("actual_admit", "size"),
            admit_rate=("actual_admit", "mean"),
            avg_probability=("predicted_probability", "mean"),
            recommend_rate=("recommended", "mean"),
        )
        .reset_index()
    )
    summary["by_bucket"] = bucket_stats.to_dict(orient="records")

    recommended = bucket_samples[bucket_samples["recommended"]].copy()
    recommended_stats = (
        recommended.groupby("bucket")
        .agg(
            sample_count=("actual_admit", "size"),
            admit_rate=("actual_admit", "mean"),
            avg_probability=("predicted_probability", "mean"),
        )
        .reset_index()
    )
    summary["recommended_by_bucket"] = recommended_stats.to_dict(orient="records")

    probability_bins = pd.cut(
        samples["predicted_probability"],
        bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        include_lowest=True,
    )
    probability_stats = (
        samples.assign(probability_bin=probability_bins)
        .groupby("probability_bin", observed=False)
        .agg(
            sample_count=("actual_admit", "size"),
            admit_rate=("actual_admit", "mean"),
        )
        .reset_index()
    )
    probability_stats["probability_bin"] = probability_stats["probability_bin"].astype(str)
    summary["by_probability_bin"] = probability_stats.to_dict(orient="records")
    return summary


def write_outputs(samples: pd.DataFrame, summary: dict[str, Any], output_dir: str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    samples.to_csv(output / "backtest_samples.csv", index=False, encoding="utf-8-sig")
    (output / "backtest_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    records = load_records("data/processed/admission_records.csv")
    metrics = load_metrics("data/processed/admission_metrics_long.csv")
    samples = build_backtest_samples(records, metrics)
    summary = summarize_backtest(samples)
    write_outputs(samples, summary, "data/processed")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
