# 数据清洗计划

## 目标表

### 1. admission_records
每行表示一个院校专业组/专业记录。

建议字段：
- record_id
- year
- province
- batch
- track
- school_code
- school_name
- admission_type
- group_code
- group_name
- major_code
- major_name
- major_full_name
- subject_requirement_raw
- subject_requirement_normalized
- plan_count
- group_plan_count
- duration_years
- tuition
- school_tags
- school_level
- school_rank
- major_level
- predicted_rank_2025
- is_new_major
- edu_level
- affiliation
- school_type
- public_private

### 2. admission_metrics_long
每行表示某记录某年的一个聚合指标。

建议字段：
- record_id
- metric_year
- enroll_count
- min_score
- min_rank
- avg_score
- avg_rank
- max_score
- max_rank
- legacy_batch

## 清洗动作

1. 列名标准化
2. 空值处理
3. 文本去空白与全角半角统一
4. 批次、科类、选科要求枚举化
5. 宽表转长表
6. 生成统计特征：
   - avg_rank_3y
   - min_rank_3y_best
   - rank_cv_3y
   - rank_trend_slope
   - rank_volatility_level

## 关键风险

- Excel 字段存在合并单元格遗留与空白列映射问题
- 选科要求是自然语言，需要解析为逻辑表达式
- 专项计划标签未直接入库，需要规则层二次识别

## 输出产物

- `data/processed/admission_records.csv`
- `data/processed/admission_metrics_long.csv`
- `data/processed/admission_features.csv`
- `docs/data-dictionary.md`
