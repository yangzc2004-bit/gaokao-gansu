from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.predict.probability import derive_target_rank, estimate_admission_probability
from backend.recommend.ranker import classify_bucket, compute_rank_cv

USER_RANK_FACTORS = [0.90, 0.95, 1.00, 1.05, 1.10]
PROBABILITY_THRESHOLDS = {"冲": 0.20, "稳": 0.45, "保": 0.70}


def load_records(records_path: str) -> pd.DataFrame:
    return pd.read_csv(records_path)


def load_metrics(metrics_path: str) -> pd.DataFrame:
    return pd.read_csv(metrics_path)


def build_backtest_base(records: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    pivot = metrics.pivot(index="record_id", columns="metric_slot")
    pivot.columns = [f"{column}_{int(slot)}" for column, slot in pivot.columns]
    pivot = pivot.reset_index()

    base = records[[
        "record_id",
        "track",
        "batch",
        "school_name",
        "major_name",
        "plan_count",
        "group_plan_count",
        "is_new_major",
        "school_level",
    ]].merge(pivot, on="record_id", how="left")

    rows: list[dict[str, Any]] = []
    for row in base.to_dict(orient="records"):
        actual_min_rank = row.get("min_rank_1")
        if pd.isna(actual_min_rank):
            continue

        history_slots = []
        for slot in [2, 3]:
            if not pd.isna(row.get(f"min_rank_{slot}")):
                history_slots.append(slot)
        if not history_slots:
            continue

        latest_slot = min(history_slots)
        history_min = [float(row[f"min_rank_{slot}"]) for slot in history_slots if not pd.isna(row.get(f"min_rank_{slot}"))]
        history_avg = [float(row[f"avg_rank_{slot}"]) for slot in history_slots if not pd.isna(row.get(f"avg_rank_{slot}"))]
        history_max = [float(row[f"max_rank_{slot}"]) for slot in history_slots if not pd.isna(row.get(f"max_rank_{slot}"))]

        years_available = len(history_slots)
        latest_min_rank = row.get(f"min_rank_{latest_slot}")
        latest_avg_rank = row.get(f"avg_rank_{latest_slot}")
        latest_max_rank = row.get(f"max_rank_{latest_slot}")
        min_rank_hist = sum(history_min) / len(history_min) if history_min else None
        avg_rank_hist = sum(history_avg) / len(history_avg) if history_avg else None
        max_rank_hist = sum(history_max) / len(history_max) if history_max else None
        rank_cv = compute_rank_cv(pd.Series(history_min))

        target_rank = derive_target_rank(
            years_available,
            latest_min_rank,
            latest_avg_rank,
            latest_max_rank,
            min_rank_hist,
            avg_rank_hist,
            max_rank_hist,
            row.get("plan_count"),
            row.get("group_plan_count"),
            row.get("is_new_major"),
        )
        if target_rank is None:
            continue

        rows.append(
            {
                "record_id": row["record_id"],
                "track": row.get("track"),
                "batch": row.get("batch"),
                "school_name": row.get("school_name"),
                "major_name": row.get("major_name"),
                "school_level": row.get("school_level"),
                "plan_count": row.get("plan_count"),
                "group_plan_count": row.get("group_plan_count"),
                "is_new_major": row.get("is_new_major"),
                "history_years": years_available,
                "latest_min_rank": latest_min_rank,
                "latest_avg_rank": latest_avg_rank,
                "latest_max_rank": latest_max_rank,
                "min_rank_hist": min_rank_hist,
                "avg_rank_hist": avg_rank_hist,
                "max_rank_hist": max_rank_hist,
                "rank_cv": rank_cv,
                "target_rank": target_rank,
                "actual_min_rank": float(actual_min_rank),
            }
        )

    return pd.DataFrame(rows)


def simulate_candidates(base_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in base_df.to_dict(orient="records"):
        actual_cutoff = float(row["actual_min_rank"])
        for factor in USER_RANK_FACTORS:
            user_rank = actual_cutoff * factor
            admitted = int(user_rank <= actual_cutoff)
            probability = estimate_admission_probability(
                user_rank,
                row.get("target_rank"),
                row.get("rank_cv"),
                int(row.get("history_years") or 0),
                row.get("latest_min_rank"),
                row.get("latest_avg_rank"),
                row.get("latest_max_rank"),
            )
            bucket = classify_bucket(float(row["target_rank"]), float(user_rank))
            rows.append(
                {
                    **row,
                    "user_rank": user_rank,
                    "user_rank_factor": factor,
                    "admitted": admitted,
                    "predicted_probability": probability,
                    "bucket": bucket,
                }
            )
    return pd.DataFrame(rows)


def brier_score(samples: pd.DataFrame) -> float:
    if samples.empty:
        return 0.0
    return float(((samples["predicted_probability"] - samples["admitted"]) ** 2).mean())


def summarize(samples: pd.DataFrame) -> dict[str, pd.DataFrame | float | int]:
    summary_all = pd.DataFrame(
        [
            {
                "samples": int(len(samples)),
                "records": int(samples["record_id"].nunique()),
                "brier_score": round(brier_score(samples), 4),
                "avg_probability": round(float(samples["predicted_probability"].mean()), 4),
                "actual_admit_rate": round(float(samples["admitted"].mean()), 4),
            }
        ]
    )

    by_history = (
        samples.groupby("history_years", as_index=False)
        .agg(
            samples=("record_id", "size"),
            avg_probability=("predicted_probability", "mean"),
            actual_admit_rate=("admitted", "mean"),
        )
        .sort_values("history_years")
    )
    by_history["avg_probability"] = by_history["avg_probability"].round(4)
    by_history["actual_admit_rate"] = by_history["actual_admit_rate"].round(4)

    bucket_eval = (
        samples[samples["bucket"].notna()]
        .groupby("bucket", as_index=False)
        .agg(
            samples=("record_id", "size"),
            avg_probability=("predicted_probability", "mean"),
            actual_admit_rate=("admitted", "mean"),
        )
    )
    bucket_eval["avg_probability"] = bucket_eval["avg_probability"].round(4)
    bucket_eval["actual_admit_rate"] = bucket_eval["actual_admit_rate"].round(4)

    threshold_rows = []
    for bucket, threshold in PROBABILITY_THRESHOLDS.items():
        subset = samples[(samples["bucket"] == bucket) & (samples["predicted_probability"] >= threshold)]
        threshold_rows.append(
            {
                "bucket": bucket,
                "threshold": threshold,
                "samples": int(len(subset)),
                "actual_admit_rate": round(float(subset["admitted"].mean()), 4) if len(subset) else None,
                "avg_probability": round(float(subset["predicted_probability"].mean()), 4) if len(subset) else None,
            }
        )
    threshold_eval = pd.DataFrame(threshold_rows)

    bins = pd.cut(
        samples["predicted_probability"],
        bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        include_lowest=True,
        right=True,
    )
    calibration = (
        samples.assign(probability_bin=bins)
        .groupby("probability_bin", as_index=False, observed=False)
        .agg(
            samples=("record_id", "size"),
            avg_probability=("predicted_probability", "mean"),
            actual_admit_rate=("admitted", "mean"),
        )
    )
    calibration["avg_probability"] = calibration["avg_probability"].round(4)
    calibration["actual_admit_rate"] = calibration["actual_admit_rate"].round(4)

    return {
        "summary_all": summary_all,
        "by_history": by_history,
        "bucket_eval": bucket_eval,
        "threshold_eval": threshold_eval,
        "calibration": calibration,
    }


def _frame_to_text(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False) + "\n```"


def format_markdown(report: dict[str, pd.DataFrame | float | int]) -> str:
    sections = ["# V2 回测校准报告", "", "## 总体", _frame_to_text(report["summary_all"]), ""]
    sections += ["## 按历史年数", _frame_to_text(report["by_history"]), ""]
    sections += ["## 按冲稳保桶", _frame_to_text(report["bucket_eval"]), ""]
    sections += ["## 当前阈值命中效果", _frame_to_text(report["threshold_eval"]), ""]
    sections += ["## 概率分箱校准", _frame_to_text(report["calibration"]), ""]
    sections += [
        "## 说明",
        "- 回测口径：使用 `slot1` 作为留出年，只使用 `slot2/slot3` 的真实历史数据生成 `target_rank` 与概率。",
        "- 样本构造：围绕真实录取最低位次，按 `0.90/0.95/1.00/1.05/1.10` 五个倍数模拟考生位次。",
        "- 录取标签：`user_rank <= slot1 最低位次` 记为录取成功，否则记为未录取。",
        "- 该回测用于校准 V2 的概率与阈值，不代表真实全体考生分布。",
    ]
    return "\n".join(sections)


def main() -> None:
    records_path = "data/processed/admission_records.csv"
    metrics_path = "data/processed/admission_metrics_long.csv"
    output_path = Path("docs/backtest-v2-report.md")

    records = load_records(records_path)
    metrics = load_metrics(metrics_path)
    base_df = build_backtest_base(records, metrics)
    samples = simulate_candidates(base_df)
    report = summarize(samples)
    output_path.write_text(format_markdown(report), encoding="utf-8")

    print(report["summary_all"].to_string(index=False))
    print("\n[by_history]")
    print(report["by_history"].to_string(index=False))
    print("\n[bucket_eval]")
    print(report["bucket_eval"].to_string(index=False))
    print("\n[threshold_eval]")
    print(report["threshold_eval"].to_string(index=False))
    print(f"\nreport_written={output_path}")


if __name__ == "__main__":
    main()
