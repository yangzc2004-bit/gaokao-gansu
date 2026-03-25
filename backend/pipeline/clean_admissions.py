from __future__ import annotations

from pathlib import Path

import pandas as pd


COLUMN_MAPPING = {
    "年份": "year",
    "生源地": "province",
    "批次": "batch",
    "科类": "track",
    "院校代码": "school_code",
    "院校名称": "school_name",
    "招生类型": "admission_type",
    "院校专业组代码": "group_code",
    "专业组名称": "group_name",
    "专业代码": "major_code",
    "专业全称": "major_full_name",
    "专业名称": "major_name",
    "专业备注": "major_note",
    "专业层次": "major_level",
    "选科要求": "subject_requirement_raw",
    "计划人数": "plan_count",
    "学制": "duration_years",
    "学费": "tuition",
    "组内专业": "group_majors",
    "专业组计划人数": "group_plan_count",
    "25年预估位次": "predicted_rank_2025",
    "是否新增": "is_new_major",
    "所在省": "school_province",
    "城市": "school_city",
    "院校标签": "school_tags",
    "院校水平": "school_level",
    "本科/专科": "edu_level",
    "隶属单位": "affiliation",
    "类型": "school_type",
    "公私性质": "public_private",
    "院校排名": "school_rank",
    "专业水平": "major_strength",
}


def normalize_text(value: object) -> object:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value.strip().replace("（", "(").replace("）", ")")
    return value


def build_long_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metric_slots = [1, 2, 3]
    rows = []
    for _, row in df.iterrows():
        for idx in metric_slots:
            rows.append(
                {
                    "record_id": row.get("record_id"),
                    "metric_slot": idx,
                    "enroll_count": row.get(f"录取人数{idx}"),
                    "min_score": row.get(f"最低分{idx}"),
                    "min_rank": row.get(f"最低位次{idx}"),
                    "avg_score": row.get(f"平均分{idx}"),
                    "avg_rank": row.get(f"平均位次{idx}"),
                    "max_score": row.get(f"最高分{idx}"),
                    "max_rank": row.get(f"最高位次{idx}"),
                    "legacy_batch": row.get(f"老批次{idx}"),
                }
            )
    return pd.DataFrame(rows)


def clean_excel(input_path: str, output_dir: str) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_excel(input_path, sheet_name="Sheet1", header=1)
    df = raw_df.rename(columns=COLUMN_MAPPING)
    df = df.apply(lambda column: column.map(normalize_text))
    df = df.reset_index(drop=True)
    df["record_id"] = df.index + 1

    records_path = output / "admission_records.csv"
    df.to_csv(records_path, index=False, encoding="utf-8-sig")

    metrics = build_long_metrics(df)
    metrics_path = output / "admission_metrics_long.csv"
    metrics.to_csv(metrics_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    clean_excel("data.xlsx", "data/processed")
