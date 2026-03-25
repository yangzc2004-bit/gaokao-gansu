"""
Column encoding fix script for gaokao project.
1. Creates column_mapping.json
2. Updates clean_admissions.py with complete mapping
3. Regenerates CSVs
"""
import json
import sys
from pathlib import Path

# Full mapping: Chinese -> English
FULL_COLUMN_MAPPING = {
    "ID": "ID",
    "年份": "year",
    "生源地": "province",
    "批次": "batch",
    "科类": "track",
    "院校代码": "school_code",
    "院校名称": "school_name",
    "招生类型": "admission_type",
    "院校专业组代码": "group_code",
    "专业组代码": "group_sub_code",
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
    "门类": "discipline",
    "专业类": "major_category",
    "25年预估位次": "predicted_rank_2025",
    "是否新增": "is_new_major",
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
    "所在省": "school_province",
    "城市": "school_city",
    "院校标签": "school_tags",
    "院校水平": "school_level",
    "更名合并转设": "rename_merge_info",
    "转专业情况": "major_transfer_info",
    "城市水平标签": "city_level_tag",
    "本科/专科": "edu_level",
    "隶属单位": "affiliation",
    "类型": "school_type",
    "公私性质": "public_private",
    "保研率": "postgrad_rate",
    "院校排名": "school_rank",
    "全校硕士专业数": "master_major_count",
    "全校硕士专业": "master_majors",
    "全校博士专业数": "doctor_major_count",
    "全校博士专业": "doctor_majors",
    "2025招生章程": "admission_charter_2025",
    "软科评级": "ruanke_rating",
    "软科排名": "ruanke_ranking",
    "学科评估": "discipline_eval",
    "专业水平": "major_strength",
    "本专业硕士点": "major_master_program",
    "本专业博士点": "major_doctor_program",
}

def main():
    # Step 1: Create column_mapping.json
    configs_dir = Path("configs")
    configs_dir.mkdir(exist_ok=True)
    
    mapping_entries = []
    for chinese, english in FULL_COLUMN_MAPPING.items():
        mapping_entries.append({
            "chinese": chinese,
            "english": english,
        })
    
    mapping_path = configs_dir / "column_mapping.json"
    mapping_path.write_text(
        json.dumps(mapping_entries, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Created {mapping_path}")
    print(f"Total columns mapped: {len(mapping_entries)}")

if __name__ == "__main__":
    main()
