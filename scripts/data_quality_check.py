import pandas as pd
import numpy as np
from datetime import datetime

# 1. 读取数据
df = pd.read_csv(r"D:\gaokao project\data\processed\admission_records.csv", encoding="utf-8-sig")

lines = []
lines.append("# 数据质量检查报告")
lines.append(f"\n> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"> 数据文件：`admission_records.csv`")

# --- 总览 ---
lines.append(f"\n## 1. 数据总览\n")
lines.append(f"- **总行数**：{len(df):,}")
lines.append(f"- **总列数**：{len(df.columns)}")
lines.append(f"- **重复行数**：{df.duplicated().sum():,}")

# --- 每列统计 ---
lines.append(f"\n## 2. 各列质量统计\n")
lines.append("| 列名 | 数据类型 | 缺失数 | 缺失率 | 唯一值数 |")
lines.append("|------|---------|--------|--------|---------|")
for col in df.columns:
    missing = df[col].isna().sum()
    pct = missing / len(df) * 100
    dtype = str(df[col].dtype)
    nuniq = df[col].nunique()
    lines.append(f"| {col} | {dtype} | {missing:,} | {pct:.1f}% | {nuniq:,} |")

# --- 完全为空的列 ---
empty_cols = [col for col in df.columns if df[col].isna().all()]
lines.append(f"\n## 3. 完全为空的列\n")
if empty_cols:
    lines.append(f"共 {len(empty_cols)} 列完全为空：\n")
    for c in empty_cols:
        lines.append(f"- `{c}`")
else:
    lines.append("无完全为空的列。")

# --- 关键列异常值检查 ---
lines.append(f"\n## 4. 关键列异常值检查\n")

key_cols = ["year", "school_name", "major_name", "min_score_1", "min_rank_1", "avg_rank_1"]
for col in key_cols:
    if col not in df.columns:
        lines.append(f"### {col}\n\n⚠️ 列不存在\n")
        continue
    lines.append(f"### {col}\n")
    if df[col].dtype in [np.float64, np.int64, float, int]:
        valid = df[col].dropna()
        neg = (valid < 0).sum()
        lines.append(f"- 非空值数：{len(valid):,}")
        lines.append(f"- 最小值：{valid.min()}")
        lines.append(f"- 最大值：{valid.max()}")
        lines.append(f"- 均值：{valid.mean():.2f}")
        lines.append(f"- 负数个数：{neg:,}")
        if col == "year":
            out_range = ((valid < 2000) | (valid > 2030)).sum()
            lines.append(f"- 超范围（<2000 或 >2030）：{out_range:,}")
        if col in ["min_score_1", "min_rank_1", "avg_rank_1"]:
            if "score" in col:
                out = ((valid < 0) | (valid > 750)).sum()
                lines.append(f"- 超范围（<0 或 >750）：{out:,}")
            if "rank" in col:
                out = (valid < 0).sum()
                lines.append(f"- 负排名数：{out:,}")
    else:
        lines.append(f"- 非空值数：{df[col].notna().sum():,}")
        lines.append(f"- 空值数：{df[col].isna().sum():,}")
        lines.append(f"- 唯一值数：{df[col].nunique():,}")
        top5 = df[col].value_counts().head(5)
        lines.append(f"- Top 5 取值：")
        for v, c in top5.items():
            lines.append(f"  - `{v}`: {c:,}")
    lines.append("")

# --- year 分布 ---
lines.append(f"## 5. 年份分布\n")
if "year" in df.columns:
    year_dist = df["year"].value_counts().sort_index()
    lines.append("| 年份 | 记录数 |")
    lines.append("|------|--------|")
    for y, cnt in year_dist.items():
        lines.append(f"| {int(y)} | {cnt:,} |")
else:
    lines.append("year 列不存在。")

# --- track 分布 ---
lines.append(f"\n## 6. track 取值分布\n")
if "track" in df.columns:
    track_dist = df["track"].value_counts()
    lines.append("| track | 记录数 | 占比 |")
    lines.append("|-------|--------|------|")
    for t, cnt in track_dist.items():
        pct = cnt / len(df) * 100
        lines.append(f"| {t} | {cnt:,} | {pct:.1f}% |")
else:
    lines.append("track 列不存在。")

# --- 总结 ---
high_missing = [(col, df[col].isna().sum() / len(df) * 100) for col in df.columns if df[col].isna().sum() / len(df) > 0.5]
lines.append(f"\n## 7. 总结\n")
lines.append(f"- 数据共 **{len(df):,}** 行 **{len(df.columns)}** 列")
lines.append(f"- 重复行：**{df.duplicated().sum():,}**")
lines.append(f"- 完全为空的列：**{len(empty_cols)}** 个")
if high_missing:
    lines.append(f"- 缺失率 > 50% 的列（{len(high_missing)} 个）：")
    for col, pct in sorted(high_missing, key=lambda x: -x[1]):
        lines.append(f"  - `{col}`: {pct:.1f}%")
else:
    lines.append(f"- 无缺失率超过 50% 的列")

report = "\n".join(lines)

import os
os.makedirs(r"D:\gaokao project\docs", exist_ok=True)
with open(r"D:\gaokao project\docs\data_quality_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"报告已写入 D:\\gaokao project\\docs\\data_quality_report.md")
print("T1.3 DONE")
