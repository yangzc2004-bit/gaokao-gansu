# 资格判定结果可解释化设计文档

**版本**: v1.0  
**日期**: 2026-03-24  
**作者**: T2.6 任务实现  

---

## 1. 设计目标

让资格审核的每条结果都附带详细的判定链路，前端可以展示"为什么通过/为什么被阻"。

### 1.1 核心需求

- **透明性**：考生可以清楚看到每条规则的判定依据
- **可追溯性**：完整的判定链路，从规则条文到实际条件
- **可操作性**：失败时给出具体的改进建议

### 1.2 用户场景

| 场景 | 需求 | 展示内容 |
|------|------|----------|
| 资格审核通过 | 确认资格，了解优势 | 通过的规则列表、可报考批次 |
| 资格审核失败 | 了解原因，寻找改进空间 | 失败的规则、具体原因、改进建议 |
| 志愿填报参考 | 快速筛选可报考计划 | 资格汇总、优先级推荐 |

---

## 2. 数据模型设计

### 2.1 RuleEvaluationDetail（单条规则评估详情）

```python
@dataclass
class RuleEvaluationDetail:
    rule_name: str          # 规则名称，如"户籍性质检查"
    rule_clause: str        # 规则条文，如"地方专项计划第2.2条：农村户籍要求"
    required_value: str     # 要求值，如"农村户籍(rural_only)"
    actual_value: str       # 实际值，如"城市户籍(urban)"
    passed: bool            # 是否通过
    failure_reason: str     # 失败原因（可选）
```

### 2.2 ExplainableResult（可解释结果）

```python
@dataclass
class ExplainableResult:
    plan_tag: str                    # 计划类型
    batch_code: str                  # 批次代码
    eligible: bool                   # 最终是否具备资格
    
    # 判定链路
    rule_evaluations: List[RuleEvaluationDetail]
    
    # 统计信息
    total_rules: int
    passed_rules: int
    failed_rules: int
    
    # 可读性摘要
    summary: str                     # 一句话摘要
    detailed_explanation: str        # 详细解释说明
    suggestions: List[str]           # 给考生的建议
```

---

## 3. 判定规则覆盖

### 3.1 已实现的判定规则

| 规则名称 | 规则条文来源 | 判定维度 |
|----------|--------------|----------|
| 户籍性质检查 | 各专项计划户籍要求章节 | hukou_nature |
| 地区范围检查 | 实施区域精确名单 | region_scope |
| 三年统一检查 | 三年统一要求条款 | three_unification_required |
| 监护人户籍检查 | 监护人户籍要求条款 | guardian_region_required |
| 实际就读检查 | 实际就读要求条款 | actual_schooling_required |
| 民族成分检查 | 民族锁定规则 | nation_lock |
| 专项审核检查 | 特殊审核要求 | special_review_pass_required |
| 专项身份检查 | 特殊身份要求 | special_identity_required |
| 建档立卡检查 | 建档立卡资格要求 | registered_poverty_family_required |
| 民族语文检查 | 民族语文成绩要求 | ethnic_language_score_required |
| 诚信记录检查 | 专项诚信约束机制 | previous_special_plan_breach_forbidden |
| 选科适配检查 | 选科硬性限制 | required_subjects |

### 3.2 规则条文示例

**国家专项计划 - 三年统一要求**：
```
规则条文：国家专项计划第1.2条：考生本人具有实施区域县（市、区）连续3年以上户籍，
         同时具有实施区域县（市、区）高中连续3年学籍并在学籍学校实际就读，
         其父亲或母亲或法定监护人具有实施区域县（市、区）户籍
要求值：户籍、学籍、监护人户籍均≥3年
实际值：考生户籍3年，学籍3年，监护人户籍3年
判定结果：✅ 通过
```

**地方专项计划 - 户籍性质要求**：
```
规则条文：地方专项计划第2.2条：考生具有农村户籍（hukou_nature: rural_only）
要求值：农村户籍
实际值：考生户籍：urban
判定结果：❌ 失败
失败原因：考生为城市户籍，不满足农村户籍要求
```

---

## 4. API 接口设计

### 4.1 recommend_for_frontend（前端推荐接口）

```python
def recommend_for_frontend(engine: PolicyEngine, profile: UserProfile) -> Dict[str, Any]
```

返回完整的可解释判定结果，供前端展示。

### 4.2 summarize_policy_eligibility（资格汇总接口）

```python
def summarize_policy_eligibility(engine: PolicyEngine, profile: UserProfile) -> Dict[str, Any]
```

返回简洁的资格汇总，适合快速查看。

---

## 5. 前端展示建议

### 5.1 资格卡片设计

```
┌─────────────────────────────────────────┐
│  ✅ 国家专项计划                          │
│  批次：本科批(C段)                        │
│                                         │
│  审核结果：具备报考资格                    │
│  规则通过率：12/12 (100%)                │
│                                         │
│  [查看详情]  [推荐院校]                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  ❌ 地方专项计划                          │
│  批次：本科批(C段)                        │
│                                         │
│  审核结果：不具备报考资格                  │
│  规则通过率：11/12 (91.7%)               │
│                                         │
│  ❌ 户籍性质不满足                        │
│     原因：考生为城市户籍，不满足农村户籍要求 │
│                                         │
│  [查看详情]  [如何改进]                   │
└─────────────────────────────────────────┘
```

### 5.2 详情弹窗设计

**判定链路时间线**：
```
✅ 户籍性质检查
   规则：地方专项计划第2.2条：农村户籍要求
   要求：农村户籍
   实际：农村户籍

✅ 地区范围检查
   规则：地方专项计划实施区域：全省农村区域
   要求：甘肃省农村区域
   实际：户籍：会宁县，学籍：会宁县

❌ 三年统一检查
   规则：地方专项计划第2.2条：三年统一要求
   要求：户籍、学籍均≥3年
   实际：考生户籍2年，学籍3年
   原因：户籍年限不足（需3年，实际2年）
```

---

## 6. 示例输出格式

### 6.1 JSON 示例（国家专项 - 通过）

```json
{
  "plan_tag": "国家专项",
  "batch_code": "本科批(C段)",
  "eligible": true,
  "summary": "✅ 具备国家专项报考资格",
  "statistics": {
    "total_rules": 12,
    "passed_rules": 12,
    "failed_rules": 0,
    "pass_rate": "100.0%"
  },
  "rule_evaluations": [
    {
      "rule_name": "户籍性质检查",
      "rule_clause": "国家专项计划第1.2条：不区分农村/城市户籍（hukou_nature: any）",
      "required_value": "农村或城市户籍均可",
      "actual_value": "农村户籍",
      "passed": true,
      "failure_reason": null
    },
    {
      "rule_name": "地区范围检查",
      "rule_clause": "国家专项计划实施区域：甘肃省原58个集中连片贫困县",
      "required_value": "58个贫困县名单内",
      "actual_value": "户籍：会宁县，学籍：会宁县，监护人户籍：会宁县",
      "passed": true,
      "failure_reason": null
    },
    {
      "rule_name": "三年统一检查",
      "rule_clause": "国家专项计划第1.2条：考生本人及监护人须具有实施区域连续3年以上户籍，考生具有3年学籍并实际就读",
      "required_value": "户籍、学籍、监护人户籍均≥3年",
      "actual_value": "考生户籍3年，学籍3年，监护人户籍3年",
      "passed": true,
      "failure_reason": null
    }
  ],
  "suggestions": [
    "您具备国家专项报考资格，建议在志愿填报时优先考虑该计划。",
    "该计划有降分录取优惠（一本线下40分），可适当冲高填报。"
  ],
  "detailed_explanation": "【国家专项】资格审核详情..."
}
```

### 6.2 JSON 示例（地方专项 - 失败）

```json
{
  "plan_tag": "地方专项",
  "batch_code": "本科批(C段)",
  "eligible": false,
  "summary": "❌ 不具备地方专项报考资格",
  "statistics": {
    "total_rules": 12,
    "passed_rules": 11,
    "failed_rules": 1,
    "pass_rate": "91.7%"
  },
  "rule_evaluations": [
    {
      "rule_name": "户籍性质检查",
      "rule_clause": "地方专项计划第2.2条：考生具有农村户籍（hukou_nature: rural_only）",
      "required_value": "农村户籍",
      "actual_value": "城市户籍",
      "passed": false,
      "failure_reason": "考生为城市户籍，不满足农村户籍要求"
    }
  ],
  "suggestions": [
    "您当前不具备地方专项报考资格，建议关注以下方面：",
    "• 户籍性质不符：如户籍有变更记录，请咨询当地招办。"
  ],
  "detailed_explanation": "【地方专项】资格审核详情..."
}
```

---

## 7. 与旧接口的兼容性

### 7.1 向后兼容

`ExplainableResult` 包含旧 `EligibilityResult` 的所有字段：
- `plan_tag`
- `eligible`
- `reasons_hit`
- `reasons_miss`

旧代码可以继续使用 `evaluate_plan()` 方法，无需修改。

### 7.2 新接口调用

```python
# 旧接口（保持兼容）
result = engine.evaluate_plan(plan, profile)  # 返回 EligibilityResult

# 新接口（可解释）
result = engine.evaluate_plan_explainable(plan, profile)  # 返回 ExplainableResult

# 批量评估（可解释）
results = engine.evaluate_all_explainable(profile)  # 返回 List[ExplainableResult]

# 前端推荐接口
recommendation = recommend_for_frontend(engine, profile)  # 返回完整JSON

# 资格汇总接口
summary = summarize_policy_eligibility(engine, profile)  # 返回汇总JSON
```

---

## 8. 测试验证

### 8.1 测试覆盖

- [x] 所有12条判定规则的详细输出验证
- [x] 通过/失败场景的边界测试
- [x] JSON序列化/反序列化测试
- [x] 与旧接口的兼容性测试

### 8.2 运行测试

```bash
cd "D:\gaokao project"
python -X utf8 backend/eval/test_edge_cases_v2.py
```

---

## 9. 后续优化建议

### 9.1 短期优化

1. **规则条文动态加载**：将规则条文从代码中抽离，配置到JSON文件中
2. **多语言支持**：为规则条文添加英文版本，便于国际化
3. **历史记录**：保存考生的历次评估记录，展示资格变化趋势

### 9.2 长期规划

1. **AI解释增强**：使用大模型生成更自然的解释文本
2. **可视化展示**：提供判定链路的流程图展示
3. **对比分析**：支持多名考生的资格对比分析

---

## 10. 附录

### 10.1 规则条文对照表

| 专项计划 | 规则来源 | 关键条款 |
|----------|----------|----------|
| 国家专项 | rules.txt 第1节 | 1.2 户籍与学籍规则 |
| 地方专项 | rules.txt 第2节 | 2.2 户籍与学籍规则 |
| 高校专项 | rules.txt 第3节 | 3.2 户籍与学籍规则 |
| 建档立卡 | rules.txt 第4节 | 4.2 本科批次规则 |
| 革命老区 | rules.txt 第5节 | 5.2 户籍与学籍规则 |
| 两州一县 | rules.txt 第6节 | 6.2 户籍与学籍规则 |
| 藏区专项 | rules.txt 第7节 | 7.1/7.2 户籍与学籍规则 |
| 免费医学生 | rules.txt 第8-9节 | 8.2 户籍与学籍规则 |
| 公费师范生 | rules.txt 第10节 | 10.2 户籍与学籍规则 |
| 预科班/民族班 | rules.txt 第12-13节 | 12.1/13.1 批次与投档规则 |
| 强基计划 | rules.txt 第15节 | 15.2 报考资格规则 |
| 综合评价 | rules.txt 第16节 | 16.2 报考资格规则 |

### 10.2 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/models/schemas.py` | 新增 | 添加 ExplainableResult、RuleEvaluationDetail 类 |
| `backend/rules/eligibility.py` | 修改 | 添加 evaluate_plan_explainable 方法和辅助方法 |
| `docs/explainability_design.md` | 新增 | 设计文档（本文档） |

---

**文档结束**
