"""
T1.1 Fix: Rename remaining Chinese columns to English in admission_records.csv
and update all backend/frontend references.
"""
import pandas as pd
import json
import re
import os

PROJECT = r"D:\gaokao project"

# === Step 1: Column mapping (Chinese → English) ===
RENAME_MAP = {
    "专业组代码": "group_sub_code",
    "门类": "discipline",
    "专业类": "major_category",
    "专业组录取人数1": "group_admit_count_1",
    "专业组最低分1": "group_min_score_1",
    "专业组最低位次1": "group_min_rank_1",
    "录取人数1": "admit_count_1",
    "最低分1": "min_score_1",
    "最低位次1": "min_rank_1",
    "平均分1": "avg_score_1",
    "平均位次1": "avg_rank_1",
    "最高分1": "max_score_1",
    "最高位次1": "max_rank_1",
    "老批次1": "old_batch_1",
    "录取人数2": "admit_count_2",
    "最低分2": "min_score_2",
    "最低位次2": "min_rank_2",
    "平均分2": "avg_score_2",
    "平均位次2": "avg_rank_2",
    "最高分2": "max_score_2",
    "最高位次2": "max_rank_2",
    "老批次2": "old_batch_2",
    "录取人数3": "admit_count_3",
    "最低分3": "min_score_3",
    "最低位次3": "min_rank_3",
    "平均分3": "avg_score_3",
    "平均位次3": "avg_rank_3",
    "最高分3": "max_score_3",
    "最高位次3": "max_rank_3",
    "老批次3": "old_batch_3",
    "更名合并转设": "rename_merge_info",
    "转专业情况": "major_transfer_info",
    "城市水平标签": "city_level_tag",
    "保研率": "postgrad_rate",
    "全校硕士专业数": "master_major_count",
    "全校硕士专业": "master_majors",
    "全校博士专业数": "doctor_major_count",
    "全校博士专业": "doctor_majors",
    "2025招生章程": "admission_charter_2025",
    "软科评级": "ruanke_rating",
    "软科排名": "ruanke_ranking",
    "学科评估": "discipline_eval",
    "本专业硕士点": "major_master_program",
    "本专业博士点": "major_doctor_program",
}

# === Step 2: Fix admission_records.csv ===
print("[1/5] Fixing admission_records.csv ...")
records_path = os.path.join(PROJECT, "data", "processed", "admission_records.csv")
df = pd.read_csv(records_path)
df.rename(columns=RENAME_MAP, inplace=True)
df.to_csv(records_path, index=False, encoding="utf-8-sig")
print(f"  Done. {len(df)} rows, {len(df.columns)} columns.")

# === Step 3: Fix admission_metrics_long.csv ===
print("[2/5] Fixing admission_metrics_long.csv ...")
metrics_path = os.path.join(PROJECT, "data", "processed", "admission_metrics_long.csv")
dfm = pd.read_csv(metrics_path)
dfm.rename(columns=RENAME_MAP, inplace=True)
dfm.to_csv(metrics_path, index=False, encoding="utf-8-sig")
print(f"  Done. {len(dfm)} rows, {len(dfm.columns)} columns.")

# === Step 4: Save column mapping JSON ===
print("[3/5] Saving column_mapping.json ...")
# Build full mapping including already-English columns
full_map = {}
for col in df.columns:
    # Find Chinese name from reverse map or use col itself
    cn_name = None
    for cn, en in RENAME_MAP.items():
        if en == col:
            cn_name = cn
            break
    full_map[col] = {"english": col, "chinese": cn_name or col}

mapping_path = os.path.join(PROJECT, "configs", "column_mapping.json")
with open(mapping_path, "w", encoding="utf-8") as f:
    json.dump({"rename_map": RENAME_MAP, "all_columns": full_map}, f, ensure_ascii=False, indent=2)
print(f"  Saved to {mapping_path}")

# === Step 5: Update Python source files ===
print("[4/5] Updating Python source references ...")

def replace_in_file(filepath, replacements):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for old, new in replacements.items():
        # Replace string literals: "old" -> "new" and 'old' -> 'new'
        content = content.replace(f'"{old}"', f'"{new}"')
        content = content.replace(f"'{old}'", f"'{new}'")
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

py_dirs = [
    os.path.join(PROJECT, "backend"),
    os.path.join(PROJECT, "frontend"),
]

changed_files = []
for d in py_dirs:
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                if replace_in_file(fpath, RENAME_MAP):
                    changed_files.append(fpath)

for f in changed_files:
    print(f"  Updated: {f}")
if not changed_files:
    print("  No Python files needed column name updates.")

# === Step 6: Verify ===
print("[5/5] Verifying CSV columns ...")
df_check = pd.read_csv(records_path, nrows=0)
remaining_chinese = [c for c in df_check.columns if any('\u4e00' <= ch <= '\u9fff' for ch in c)]
if remaining_chinese:
    print(f"  WARNING: Still have Chinese columns: {remaining_chinese}")
else:
    print("  All columns are now English. Zero Chinese column names remaining.")

print("\n=== T1.1 COMPLETE ===")
