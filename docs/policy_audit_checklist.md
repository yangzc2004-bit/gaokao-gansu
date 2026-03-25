# 政策规则审计报告

**审计日期**: 2026-03-24  
**审计范围**: 甘肃省 2024-2026 年新高考专项计划准入规则引擎  
**审计文件**:
- `rules.txt` — 原始政策规则文档（16类专项计划）
- `configs/policy_rules.gansu.json` — 结构化规则配置（22条计划记录）
- `configs/region_dict.gansu.json` — 地区字典
- `backend/rules/eligibility.py` — 资格判定代码

---

## 审计方法

1. **逐条对照**: 读取 `rules.txt` 全文，逐类计划提取关键规则字段（plan_tag, hukou_nature, region_list, nation_lock, three_unification_required, residence_years, score_logic），与 `policy_rules.gansu.json` 逐字段比对。
2. **地区字典核验**: 将 `region_dict.gansu.json` 中各区域列表与 `rules.txt` 原文名单逐县核对，检查数量和名称一致性。
3. **代码逻辑审计**: 读取 `eligibility.py`，检查每个 `_match_*` 方法的逻辑是否与 JSON 规则字段语义一致。
4. **交叉验证**: 检查 JSON 中额外字段（如 `guardian_region_required`, `actual_schooling_required` 等）是否有 rules.txt 原文依据。

---

## 逐计划审计结果

### 1. 国家专项计划（source_section: 1）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 国家专项计划 | `国家专项` | ✅ | 简称，可接受 |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | 括号全半角差异，无影响 |
| hukou_nature | any（不区分城乡） | `any` | ✅ | |
| region_scope | 58个集中连片贫困县 | `gansu_58_poverty_counties` | ✅ | 引用字典key |
| nation_lock | none（无民族限制） | `none` | ✅ | |
| three_unification_required | true | `true` | ✅ | |
| residence_years | 连续3年以上户籍 | `3` | ✅ | |
| guardian_region_required | 父/母/监护人须有实施区域户籍 | `true` | ✅ | |
| actual_schooling_required | 在学籍学校实际就读 | `true` | ✅ | |
| previous_special_plan_breach_forbidden | 2023年起诚信约束 | `true` | ✅ | |
| score_logic | 一本线下40分以内 | `line_offset:-40` | ✅ | |
| region_compare_fields | 户籍+学籍+监护人户籍 | `["region","school_region","parent_region"]` | ✅ | |

**结论**: ✅ 完全一致

---

### 2. 地方专项计划（source_section: 2）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 地方专项计划 | `地方专项` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| hukou_nature | rural_only（农村户籍） | `rural_only` | ✅ | |
| region_scope | 全省农村区域 | `gansu_rural_all` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | true | `true` | ✅ | |
| residence_years | 连续三年 | `3` | ✅ | |
| guardian_region_required | 原文未明确要求监护人户籍 | `false` | ✅ | 地方专项仅要求考生本人 |
| actual_schooling_required | 实际就读 | `true` | ✅ | |
| previous_special_plan_breach_forbidden | 原文未提及 | `false` | ⚠️ | 原文未明确，保守可设true |
| score_logic | 不低于本科二批线 | `passing_line:二本线` | ✅ | |

**结论**: ✅ 基本一致，`previous_special_plan_breach_forbidden` 需确认是否适用

---

### 3. 高校专项计划（source_section: 3）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 高校专项计划（含自强计划） | `高校专项` | ✅ | |
| batch_code | 本科批（B段），顺序志愿 | `本科批(B段)` | ✅ | |
| hukou_nature | rural_only | `rural_only` | ✅ | |
| region_scope | 58+3县 | `gansu_58_plus_3` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | true | `true` | ✅ | |
| residence_years | 连续三年 | `3` | ✅ | |
| guardian_region_required | 父/母/监护人须在农村 | `true` | ✅ | |
| special_review_pass_required | 三级审核公示 | `true` | ✅ | |
| score_logic | 按高校招生简章 | `by_university_brochure` | ✅ | |

**结论**: ✅ 完全一致

---

### 4. 建档立卡专项-本科（source_section: 4.2）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 精准扶贫专项/建档立卡专项 | `建档立卡专项(本科)` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| hukou_nature | any（不区分） | `any` | ✅ | |
| region_scope | 以扶贫部门数据库为准 | `null` | ✅ | 无固定地区列表 |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | 原文未提及 | `false` | ✅ | |
| registered_poverty_family_required | 建档立卡贫困户家庭 | `true` | ✅ | |
| score_logic | 未明确降分规则 | `as_batch_rule` | ✅ | |

**结论**: ✅ 一致

---

### 5. 建档立卡专项-专科（source_section: 4.3）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 建档立卡专项（专科） | `建档立卡专项(专科)` | ✅ | |
| batch_code | 高职（专科）批（F段） | `高职(专科)批(F段)` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| registered_poverty_family_required | 建档立卡 | `true` | ✅ | |
| score_logic | 按批次规则 | `as_batch_rule` | ✅ | |

**结论**: ✅ 一致

---

### 6. 革命老区专项（source_section: 5）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 革命老区专项 | `革命老区专项` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| hukou_nature | any（不区分城乡） | `any` | ✅ | |
| region_scope | 庆阳8+平凉6+会宁=15县 | `gansu_revolutionary_areas` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | 高中阶段户籍在当地 | `true` | ✅ | |
| residence_years | 至少3年 | `3` | ✅ | |
| actual_schooling_required | 原文仅要求"参加当年高考报名且高中阶段户籍在当地" | `false` | ✅ | 原文未要求实际就读 |
| score_logic | 不低于二本线 | `passing_line:二本线` | ✅ | |
| region_compare_fields | 仅户籍 | `["region"]` | ⚠️ | 原文说"高中阶段户籍在当地"，未要求学籍也在当地，但是否应检查school_region需确认 |

**结论**: ✅ 基本一致，region_compare_fields 可能需要增加 school_region

---

### 7. 两州一县专项（source_section: 6）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 省属"两州一县"专项 | `两州一县专项` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| region_scope | 甘南8+临夏8+天祝=17 | `gansu_two_states_one_county` | ✅ | |
| nation_lock | 分层：70%少数民族/30%不区分 | `conditional_default_minority` | ✅ | 用条件默认值表达分层逻辑 |
| three_unification_required | true | `true` | ✅ | |
| residence_years | 3 | `3` | ✅ | |
| score_logic | 分批次分科类分院校专业组确定 | `by_batch_and_major_group` | ✅ | |

**结论**: ✅ 一致

---

### 8. 藏区专项-民语类（source_section: 7.1.1）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 藏区专项-民语类 | `藏区专项-民语类` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| hukou_nature | 甘南+天祝 | `any` | ⚠️ | 原文隐含户籍在藏区，但JSON用region_scope限制，hukou_nature设any合理 |
| region_scope | 甘南+天祝 | `gansu_tibetan_area` | ✅ | |
| nation_lock | minority_only（默认少数民族） | `minority_only` | ✅ | |
| ethnic_language_score_required | 必须有民族语文成绩 | `true` | ✅ | |
| three_unification_required | 原文未明确 | `true` | ⚠️ | 保守处理，可接受 |
| score_logic | 按批次规则 | `as_batch_rule` | ✅ | |

**结论**: ✅ 基本一致

---

### 9. 藏区专项-其他类（source_section: 7.1.2）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 藏区专项-其他类 | `藏区专项-其他类` | ✅ | |
| region_scope | 甘南+天祝 | `gansu_tibetan_area` | ✅ | |
| nation_lock | 无明确限制，默认minority_only | `conditional_default_minority` | ✅ | |
| ethnic_language_score_required | 不要求 | `false` | ✅ | |
| score_logic | 按批次规则 | `as_batch_rule` | ✅ | |

**结论**: ✅ 一致

---

### 10. 其他民族地区专项（source_section: 7.2）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 其他民族地区专项 | `其他民族地区专项` | ✅ | |
| region_scope | 临夏8+张家川+肃南+肃北+阿克塞=12 | `gansu_other_ethnic_areas` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| nation_lock | 无明确限制，默认minority_only | `conditional_default_minority` | ✅ | |
| three_unification_required | true | `true` | ✅ | |

**结论**: ✅ 一致

---

### 11. 省属免费医学生-本科（source_section: 8）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 农村免费医学生专项（省属）-本科 | `省属免费医学生(本科)` | ✅ | |
| batch_code | 本科提前批（A段） | `本科提前批(A段)` | ✅ | |
| hukou_nature | rural_only（BUG-03修正） | `rural_only` | ✅ | |
| region_scope | 全省农村 | `gansu_rural_all` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | true | `true` | ✅ | |
| residence_years | 连续3年以上 | `3` | ✅ | |
| guardian_region_required | 父/母/监护人农村户籍 | `true` | ✅ | |
| score_logic | 二本线 | `passing_line:二本线` | ✅ | |
| required_subjects | 临床医学类PHYSICS & CHEMISTRY | `PHYSICS & CHEMISTRY` | ✅ | |

**结论**: ✅ 一致

---

### 12. 省属免费医学生-专科（source_section: 8）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| batch_code | 高职（专科）批特殊类P段 | `高职(专科)批特殊类(P段)` | ✅ | |
| hukou_nature | rural_only | `rural_only` | ✅ | |
| score_logic | 二本线 | `passing_line:二本线` | ⚠️ | 专科层次用二本线作为分数线，原文未单独说明专科分数线，需确认 |
| required_subjects | 原文按专业：中医学类依院校要求 | `null` | ✅ | 专科可能无硬性限制 |

**结论**: ⚠️ score_logic 可能有误，专科层次应有独立分数线

---

### 13. 国家免费医学生（source_section: 9）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 国家免费医学生 | `国家免费医学生` | ✅ | |
| batch_code | 本科提前批（A段） | `本科提前批(A段)` | ✅ | |
| hukou_nature | rural_only（参照省属） | `rural_only` | ✅ | |
| region_scope | 58+3县 | `gansu_58_plus_3` | ✅ | |
| score_logic | 参照省属 | `refer_provincial_free_medical` | ✅ | |

**结论**: ✅ 一致

---

### 14. 国家公费师范生（source_section: 10.1）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 国家公费师范生 | `国家公费师范生` | ✅ | |
| batch_code | 本科提前批（A段） | `本科提前批(A段)` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| three_unification_required | 未要求 | `false` | ✅ | |
| score_logic | 一本线上择优 | `above_first_line` | ✅ | |

**结论**: ✅ 一致

---

### 15. 省属公费师范生（source_section: 10.2）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 省属公费师范生 | `省属公费师范生` | ✅ | |
| hukou_nature | rural_only（BUG-03修正） | `rural_only` | ✅ | |
| residence_years | 连续3年以上 | `3` | ✅ | |
| guardian_region_required | 父/母/监护人 | `true` | ✅ | |
| score_logic | 二本线 | `passing_line:二本线` | ✅ | |
| region_scope | 定向区域 | `gansu_local_target_area` | ✅ | |

**结论**: ✅ 一致

---

### 16. 市级定向培养（source_section: 11）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 市级定向培养 | `市级定向培养` | ✅ | |
| batch_code | 本科提前批(A段)/P段 | `本科提前批(A段)/高职(专科)批特殊类(P段)` | ✅ | |
| hukou_nature | rural_only | `rural_only` | ✅ | |
| residence_years | 连续3年以上 | `3` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| score_logic | 由市州确定 | `by_city_program` | ✅ | |

**结论**: ✅ 一致

---

### 17. 少数民族预科班（source_section: 12）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 少数民族预科班 | `少数民族预科班` | ✅ | |
| batch_code | 本科批（C段） | `本科批(C段)` | ✅ | |
| nation_lock | minority_only | `minority_only` | ✅ | |
| hukou_nature | 无特定要求 | `any` | ✅ | |
| score_logic | 二本线下80分 | `line_offset:-80_from_second_line` | ✅ | |

**结论**: ✅ 一致

---

### 18. 民族班（source_section: 13）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 民族班 | `民族班` | ✅ | |
| nation_lock | minority_only | `minority_only` | ✅ | |
| score_logic | 二本线下40分 | `line_offset:-40_from_second_line` | ✅ | |

**结论**: ✅ 一致

---

### 19. 边防军人子女预科（source_section: 14）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 边防军人子女预科 | `边防军人子女预科` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| special_identity_required | 军委政治工作部审核确认 | `border_military_child` | ✅ | |
| special_review_pass_required | 需审核确认 | `true` | ✅ | |
| score_logic | 二本线下80分 | `line_offset:-80_from_second_line` | ✅ | |

**结论**: ✅ 一致

---

### 20. 强基计划（source_section: 15）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 强基计划 | `强基计划` | ✅ | |
| batch_code | 提前批A段之前单独投档录取 | `提前批A段之前单独投档` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| special_review_pass_required | 需高校审核 | `true` | ✅ | |
| special_identity_required | 综合素质优秀/基础学科拔尖 | `strong_foundation_candidate` | ✅ | |
| score_logic | 高考≥85%+高校考核≤15% | `composite_assessment` | ✅ | |
| required_subjects | 理科PHYSICS&CHEMISTRY / 文科HISTORY | `PHYSICS & CHEMISTRY \| HISTORY` | ✅ | |

**结论**: ✅ 一致

---

### 21. 综合评价录取（source_section: 16）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 综合评价录取 | `综合评价录取` | ✅ | |
| batch_code | 本科提前批(A段)/单独批次 | `本科提前批(A段)/单独批次` | ✅ | |
| hukou_nature | any | `any` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| special_review_pass_required | 通过高校初审 | `true` | ✅ | |
| score_logic | 60%高考+30-40%综合评价 | `college_composite_rule` | ✅ | |

**结论**: ✅ 一致

---

### 22. 农村学生专项（source_section: 17）

| 字段 | rules.txt 原文 | JSON 配置 | 一致性 | 备注 |
|------|---------------|-----------|--------|------|
| plan_tag | 农村学生专项 | `农村学生专项` | ✅ | |
| hukou_nature | rural_only | `rural_only` | ✅ | |
| region_scope | 全省农村或指定农村区域 | `gansu_rural_all` | ✅ | |
| three_unification_required | true | `true` | ✅ | |
| nation_lock | none | `none` | ✅ | |
| score_logic | 按院校方案 | `by_college_rule` | ✅ | |

**结论**: ✅ 一致

---

## 地区字典核验

### 国家专项 58 县

| 检查项 | 结果 |
|--------|------|
| 总数量 | 58 ✅ |
| 兰州市（3）| 永登县、皋兰县、榆中县 ✅ |
| 白银市（3）| 靖远县、会宁县、景泰县 ✅ |
| 天水市（6）| 麦积区、清水县、秦安县、甘谷县、武山县、张家川回族自治县 ✅ |
| 武威市（2）| 古浪县、天祝藏族自治县 ✅ |
| 平凉市（5）| 崆峒区、泾川县、灵台县、庄浪县、静宁县 ✅ |
| 庆阳市（7）| 庆城县、环县、华池县、合水县、正宁县、宁县、镇原县 ✅ |
| 定西市（7）| 安定区、通渭县、陇西县、渭源县、临洮县、漳县、岷县 ✅ |
| 临夏州（8）| 临夏市、临夏县、康乐县、永靖县、广河县、和政县、东乡族自治县、积石山保安族东乡族撒拉族自治县 ✅ |
| 陇南市（9）| 武都区、成县、文县、宕昌县、康县、西和县、礼县、徽县、两当县 ✅ |
| 甘南州（8）| 合作市、临潭县、卓尼县、舟曲县、迭部县、玛曲县、碌曲县、夏河县 ✅ |
| 与rules.txt逐一比对 | 无缺漏、无多余 ✅ |

**结论**: ✅ 58县完全齐全，与rules.txt原文完全一致

### 高校专项 58+3 县

| 检查项 | 结果 |
|--------|------|
| 总数量 | 61 ✅ |
| 包含完整58县 | ✅ |
| 额外3县：肃北蒙古族自治县 | ✅ |
| 额外3县：阿克塞哈萨克族自治县 | ✅ |
| 额外3县：肃南裕固族自治县 | ✅ |

**结论**: ✅ 58+3=61县完全齐全

### 革命老区 15 县

| 检查项 | 结果 |
|--------|------|
| 总数量 | 15 ✅ |
| 庆阳市全境（8）| 西峰区、庆城县、环县、华池县、合水县、正宁县、宁县、镇原县 ✅ |
| 平凉市全境（6）| 崆峒区、泾川县、灵台县、崇信县、庄浪县、静宁县 ✅ |
| 白银市会宁县（1）| 会宁县 ✅ |
| 与rules.txt逐一比对 | 无缺漏、无多余 ✅ |

**结论**: ✅ 15县完全齐全

### 两州一县 17 县（附带核验）

| 检查项 | 结果 |
|--------|------|
| 总数量 | 17 ✅ |
| 甘南州8县 | ✅ |
| 临夏州8县 | ✅ |
| 天祝藏族自治县 | ✅ |

### 藏区 9 县（附带核验）

| 检查项 | 结果 |
|--------|------|
| 总数量 | 9 ✅ |
| 甘南州8县+天祝 | ✅ |

### 其他民族地区 12 县（附带核验）

| 检查项 | 结果 |
|--------|------|
| 总数量 | 12 ✅ |
| 临夏州8+张家川+肃南+肃北+阿克塞 | ✅ |

---

## 代码逻辑审计（eligibility.py）

### 方法级审计

| 方法 | JSON字段 | 逻辑正确性 | 备注 |
|------|----------|-----------|------|
| `_match_hukou` | hukou_nature | ✅ | any直接通过，否则精确匹配 |
| `_match_region` | region_scope + region_compare_fields | ✅ | 对gansu_rural_all和gansu_local_target_area直接放行，其他查字典 |
| `_match_three_unification` | three_unification_required + residence_years | ⚠️ | 检查school_years, hukou_years, parent_hukou_years均≥need_years。但parent_hukou_years在革命老区等不要求监护人户籍的计划中可能误判（见问题P-01） |
| `_match_guardian_region` | guardian_region_required | ✅ | 检查parent_has_local_hukou和parent_region |
| `_match_schooling` | actual_schooling_required | ✅ | 检查graduated_in_region_school |
| `_match_nation` | nation_lock | ✅ | none放行，minority_only和conditional_default_minority排除汉族，tibetan_only仅藏族 |
| `_match_special_review` | special_review_pass_required | ✅ | |
| `_match_special_identity` | special_identity_required | ✅ | |
| `_match_registered_family` | registered_poverty_family_required | ✅ | |
| `_match_ethnic_language` | ethnic_language_score_required | ✅ | |
| `_match_previous_breach` | previous_special_plan_breach_forbidden | ✅ | |
| `_match_subjects` | subject_logic.required_subjects | ✅ | 特殊处理强基计划的OR逻辑 |

### 代码级问题

| 编号 | 问题 | 严重性 |
|------|------|--------|
| C-01 | `_match_three_unification` 始终检查 parent_hukou_years，但革命老区等计划的 three_unification 含义不同（仅要求考生本人户籍），guardian_region_required=false 时 parent 年限检查可能不合理 | 🟡 中 |
| C-02 | `_match_nation` 将 `conditional_default_minority` 与 `minority_only` 同等处理，直接排除汉族。但原文说两州一县 30% 名额"不区分民族成分"，代码无法区分这30%场景 | 🟡 中 |
| C-03 | `_match_region` 对 `gansu_local_target_area` 直接返回 True，未做任何地区检查。省属公费师范生和市级定向培养的定向区域限制被跳过 | 🟡 中 |
| C-04 | 选科检查在 checks 列表之前单独执行并 append 到 hit/miss，但随后 checks 循环也 append，顺序不影响结果但代码风格不一致 | 🟢 低 |

---

## 发现的问题清单

| 编号 | 严重性 | 计划类型 | 问题描述 | 修复建议 |
|------|--------|---------|---------|---------|
| P-01 | 🟡 中 | 革命老区专项 | `_match_three_unification` 检查 `parent_hukou_years`，但革命老区仅要求"高中阶段户籍在当地"，不要求监护人户籍年限。当 `guardian_region_required=false` 但 `three_unification_required=true` 时，代码仍检查监护人年限，可能错误拒绝合格考生 | 在 `_match_three_unification` 中增加判断：若 `guardian_region_required=false`，则不检查 `parent_hukou_years` |
| P-02 | 🟡 中 | 两州一县/藏区其他类/其他民族地区 | `conditional_default_minority` 在代码中等同于 `minority_only`，一刀切排除汉族。但原文明确两州一县有30%"不区分民族成分"名额 | 建议在 `_match_nation` 中对 `conditional_default_minority` 返回"建议少数民族但汉族不强制排除"的soft判定，或在结果中标注为"推荐但不排除" |
| P-03 | 🟡 中 | 省属公费师范生/市级定向培养 | `gansu_local_target_area` 在代码中直接放行，无实际地区校验。定向区域限制未生效 | 需在 region_dict 中补充 `gansu_local_target_area` 的具体县区列表，或根据考生的定向市州动态匹配 |
| P-04 | 🟢 低 | 省属免费医学生(专科) | score_logic 设为 `passing_line:二本线`，但专科层次通常有独立的分数线，原文未明确专科分数控制规则 | 确认专科层次分数线是否应为专科批次控制线而非二本线 |
| P-05 | 🟢 低 | 地方专项 | `previous_special_plan_breach_forbidden` 设为 false，但2023年起的诚信约束机制是否也适用于地方专项，原文未明确 | 与教育考试院确认诚信约束是否仅限国家专项，还是全部专项计划通用 |
| P-06 | 🟢 低 | 革命老区专项 | `region_compare_fields` 仅包含 `["region"]`（户籍），原文说"参加当年高考报名且高中阶段户籍在当地"，是否也隐含学籍要求不明确 | 建议确认是否需增加 `school_region` 到比对字段 |
| P-07 | 🟢 低 | 全局 | JSON 中 `batch_code` 使用半角括号如 `本科批(C段)`，与 rules.txt 原文的全角括号 `本科批（C段）` 不完全一致 | 统一为全角或半角，或在比对时做标准化处理 |

---

## 总结

### 审计结论

本次审计覆盖 **22 条计划记录**（对应 rules.txt 中的 16 大类，部分拆分为本科/专科子项），共核验 **6 个地区字典**、**11 个规则检查方法**。

**总体评价**: 规则引擎的 JSON 配置与 rules.txt 原文 **高度一致**，主要规则字段（hukou_nature, nation_lock, three_unification_required, residence_years, score_logic）均正确映射。地区字典的 58 县、61 县、15 县等关键名单 **完全齐全，无遗漏**。

### 统计

| 指标 | 数量 |
|------|------|
| 审计计划数 | 22 |
| 完全一致 | 18 |
| 基本一致（有小问题） | 4 |
| 严重不一致 | 0 |
| 地区字典全部通过 | 6/6 |
| 代码问题 | 4（0高/3中/1低） |
| 总问题数 | 7（0高/3中/4低） |

### 优先修复建议

1. **P-01（中）**: 修改 `_match_three_unification`，当 `guardian_region_required=false` 时跳过 parent_hukou_years 检查
2. **P-02（中）**: 重新设计 `conditional_default_minority` 的处理逻辑，区分硬排除和软建议
3. **P-03（中）**: 补充 `gansu_local_target_area` 的实际地区数据或动态匹配机制

### 无需修复

- 所有地区字典数据正确
- 核心规则字段映射正确
- 代码整体架构合理，检查方法覆盖完整
