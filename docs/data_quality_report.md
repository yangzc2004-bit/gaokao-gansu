# 数据质量检查报告

> 生成时间：2026-03-24 21:23:51
> 数据文件：`admission_records.csv`

## 1. 数据总览

- **总行数**：31,818
- **总列数**：78
- **重复行数**：0

## 2. 各列质量统计

| 列名 | 数据类型 | 缺失数 | 缺失率 | 唯一值数 |
|------|---------|--------|--------|---------|
| ID | int64 | 0 | 0.0% | 31,818 |
| year | int64 | 0 | 0.0% | 1 |
| province | object | 0 | 0.0% | 1 |
| batch | object | 0 | 0.0% | 6 |
| track | object | 0 | 0.0% | 2 |
| school_code | int64 | 0 | 0.0% | 1,832 |
| school_name | object | 0 | 0.0% | 1,833 |
| admission_type | object | 16,352 | 51.4% | 196 |
| group_code | int64 | 0 | 0.0% | 7,119 |
| group_sub_code | int64 | 0 | 0.0% | 113 |
| group_name | object | 0 | 0.0% | 113 |
| major_code | object | 0 | 0.0% | 344 |
| major_full_name | object | 0 | 0.0% | 9,264 |
| major_name | object | 0 | 0.0% | 1,252 |
| major_note | object | 19,697 | 61.9% | 4,556 |
| major_level | object | 0 | 0.0% | 3 |
| subject_requirement_raw | object | 0 | 0.0% | 15 |
| plan_count | int64 | 0 | 0.0% | 132 |
| duration_years | int64 | 0 | 0.0% | 8 |
| tuition | object | 0 | 0.0% | 448 |
| group_majors | object | 0 | 0.0% | 7,112 |
| group_plan_count | int64 | 0 | 0.0% | 247 |
| discipline | object | 0 | 0.0% | 36 |
| major_category | object | 0 | 0.0% | 187 |
| predicted_rank_2025 | float64 | 31,818 | 100.0% | 0 |
| is_new_major | object | 29,004 | 91.2% | 1 |
| group_admit_count_1 | float64 | 637 | 2.0% | 242 |
| group_min_score_1 | float64 | 637 | 2.0% | 508 |
| group_min_rank_1 | float64 | 637 | 2.0% | 938 |
| admit_count_1 | float64 | 3,009 | 9.5% | 137 |
| min_score_1 | float64 | 3,011 | 9.5% | 526 |
| min_rank_1 | float64 | 3,011 | 9.5% | 993 |
| avg_score_1 | float64 | 23,801 | 74.8% | 1,584 |
| avg_rank_1 | float64 | 23,801 | 74.8% | 903 |
| max_score_1 | float64 | 23,801 | 74.8% | 495 |
| max_rank_1 | float64 | 23,801 | 74.8% | 904 |
| old_batch_1 | object | 3,009 | 9.5% | 6 |
| admit_count_2 | float64 | 9,344 | 29.4% | 149 |
| min_score_2 | float64 | 9,344 | 29.4% | 506 |
| min_rank_2 | float64 | 9,344 | 29.4% | 941 |
| avg_score_2 | float64 | 9,344 | 29.4% | 10,342 |
| avg_rank_2 | float64 | 9,344 | 29.4% | 869 |
| max_score_2 | float64 | 9,344 | 29.4% | 477 |
| max_rank_2 | float64 | 9,344 | 29.4% | 837 |
| old_batch_2 | object | 9,344 | 29.4% | 5 |
| admit_count_3 | float64 | 12,498 | 39.3% | 149 |
| min_score_3 | float64 | 12,463 | 39.2% | 490 |
| min_rank_3 | float64 | 12,463 | 39.2% | 926 |
| avg_score_3 | float64 | 12,463 | 39.2% | 8,802 |
| avg_rank_3 | float64 | 12,463 | 39.2% | 890 |
| max_score_3 | float64 | 12,463 | 39.2% | 491 |
| max_rank_3 | float64 | 12,463 | 39.2% | 888 |
| old_batch_3 | object | 12,463 | 39.2% | 6 |
| school_province | object | 0 | 0.0% | 32 |
| school_city | object | 0 | 0.0% | 365 |
| school_tags | object | 15,989 | 50.3% | 29 |
| school_level | object | 15,792 | 49.6% | 253 |
| rename_merge_info | object | 17,769 | 55.8% | 620 |
| major_transfer_info | object | 15,456 | 48.6% | 589 |
| city_level_tag | object | 10 | 0.0% | 12 |
| edu_level | object | 0 | 0.0% | 3 |
| affiliation | object | 0 | 0.0% | 40 |
| school_type | object | 153 | 0.5% | 31 |
| public_private | object | 0 | 0.0% | 4 |
| postgrad_rate | object | 4 | 0.0% | 181 |
| school_rank | object | 25 | 0.1% | 497 |
| master_major_count | float64 | 16,179 | 50.8% | 91 |
| master_majors | object | 16,186 | 50.9% | 613 |
| doctor_major_count | float64 | 19,815 | 62.3% | 57 |
| doctor_majors | object | 19,822 | 62.3% | 379 |
| admission_charter_2025 | object | 366 | 1.2% | 1,825 |
| ruanke_rating | object | 19,937 | 62.7% | 4 |
| ruanke_ranking | float64 | 19,937 | 62.7% | 402 |
| discipline_eval | object | 25,973 | 81.6% | 31 |
| major_strength | object | 21,479 | 67.5% | 188 |
| major_master_program | object | 21,510 | 67.6% | 258 |
| major_doctor_program | object | 27,568 | 86.6% | 195 |
| record_id | int64 | 0 | 0.0% | 31,818 |

## 3. 完全为空的列

共 1 列完全为空：

- `predicted_rank_2025`

## 4. 关键列异常值检查

### year

- 非空值数：31,818
- 最小值：2024
- 最大值：2024
- 均值：2024.00
- 负数个数：0
- 超范围（<2000 或 >2030）：0

### school_name

- 非空值数：31,818
- 空值数：0
- 唯一值数：1,833
- Top 5 取值：
  - `西北师范大学`: 340
  - `兰州交通大学`: 245
  - `兰州理工大学`: 226
  - `甘肃农业大学`: 188
  - `甘肃民族师范学院`: 182

### major_name

- 非空值数：31,818
- 空值数：0
- 唯一值数：1,252
- Top 5 取值：
  - `学前教育`: 420
  - `法学`: 417
  - `英语`: 413
  - `计算机科学与技术`: 409
  - `电子商务`: 408

### min_score_1

- 非空值数：28,807
- 最小值：161.0
- 最大值：698.0
- 均值：450.63
- 负数个数：0
- 超范围（<0 或 >750）：0

### min_rank_1

- 非空值数：28,807
- 最小值：35.0
- 最大值：115509.0
- 均值：42974.00
- 负数个数：0
- 负排名数：0

### avg_rank_1

- 非空值数：8,017
- 最小值：35.0
- 最大值：115509.0
- 均值：40768.65
- 负数个数：0
- 负排名数：0

## 5. 年份分布

| 年份 | 记录数 |
|------|--------|
| 2024 | 31,818 |

## 6. track 取值分布

| track | 记录数 | 占比 |
|-------|--------|------|
| 物理 | 21,386 | 67.2% |
| 历史 | 10,432 | 32.8% |

## 7. 总结

- 数据共 **31,818** 行 **78** 列
- 重复行：**0**
- 完全为空的列：**1** 个
- 缺失率 > 50% 的列（20 个）：
  - `predicted_rank_2025`: 100.0%
  - `is_new_major`: 91.2%
  - `major_doctor_program`: 86.6%
  - `discipline_eval`: 81.6%
  - `avg_score_1`: 74.8%
  - `avg_rank_1`: 74.8%
  - `max_score_1`: 74.8%
  - `max_rank_1`: 74.8%
  - `major_master_program`: 67.6%
  - `major_strength`: 67.5%
  - `ruanke_rating`: 62.7%
  - `ruanke_ranking`: 62.7%
  - `doctor_majors`: 62.3%
  - `doctor_major_count`: 62.3%
  - `major_note`: 61.9%
  - `rename_merge_info`: 55.8%
  - `admission_type`: 51.4%
  - `master_majors`: 50.9%
  - `master_major_count`: 50.8%
  - `school_tags`: 50.3%