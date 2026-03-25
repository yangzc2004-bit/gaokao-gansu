# 甘肃高考志愿推荐系统规则引擎修复报告

**修复日期**: 2026-03-24  
**修复人员**: Python 后端开发专家  
**修复问题**: P-02 / P-01 / P-03

---

## 修复概览

| 问题编号 | 优先级 | 问题描述 | 修复状态 |
|---------|--------|---------|---------|
| P-02 | 高 | 两州一县汉族考生被错误阻止 | ✅ 已修复 |
| P-01 | 中 | 革命老区没检查学籍地区 | ✅ 已修复 |
| P-03 | 中 | 市级定向培养地区限制未生效 | ✅ 已修复 |

**测试通过率**: 60/60 (100%)

---

## P-02 修复详情：两州一县汉族考生被错误阻止

### 问题描述
两州一县专项有 30% 名额不区分民族，但代码 `conditional_default_minority` 把汉族全拦了。

### 失败测试用例
- P-02-02: 两州一县-汉族考生
- P-02-05: 两州一县-汉族考生户籍5年

### 修复方案
修改 `backend/rules/eligibility.py` 中的 `_match_nation` 方法：

```python
# 修复前
if lock in {"minority_only", "conditional_default_minority"}:
    return profile.nation not in {None, "", "汉族"}

# 修复后
if lock == "minority_only":
    return profile.nation not in {None, "", "汉族"}
if lock == "conditional_default_minority":
    # 两州一县等专项：默认少数民族优先（70%名额），但汉族也可报考（30%名额不区分民族）
    # 因此汉族考生也应判定为符合条件，只是优先级较低
    return True
```

### 修复原理
- `minority_only`: 严格限制为少数民族（如少数民族预科班、民族班）
- `conditional_default_minority`: 默认少数民族优先，但允许汉族通过（如两州一县、藏区专项-其他类、其他民族地区专项）

---

## P-01 修复详情：革命老区没检查学籍地区

### 问题描述
革命老区专项要求"高中阶段户籍在当地"，但代码 `region_compare_fields` 只检查 `["region"]`，没有检查 `school_region`。

### 失败测试用例
- P-01-10: 革命老区-考生户籍本地但学籍外地

### 修复方案
修改 `configs/policy_rules.gansu.json` 中革命老区专项的配置：

```json
// 修复前
"region_compare_fields": ["region"]

// 修复后
"region_compare_fields": ["region", "school_region"]
```

### 修复原理
革命老区专项要求考生户籍和学籍都必须在革命老区范围内。原配置只检查户籍地区，不检查学籍地区，导致学籍在外地的考生也能通过，这是错误的。

---

## P-03 修复详情：市级定向培养地区限制未生效

### 问题描述
市级定向培养要求定向市户籍，但代码中 `gansu_local_target_area` 被直接放行（`if not scope or scope in {...}`）。

### 失败测试用例
- P-03-06: 市级定向-非定向市户籍（兰州市考生应被阻止）

### 修复方案

#### 1. 修改 `backend/rules/eligibility.py`
移除 `gansu_local_target_area` 的直接放行逻辑：

```python
# 修复前
if not scope or scope in {"gansu_rural_all", "gansu_local_target_area"}:
    return True

// 修复后
if not scope or scope == "gansu_rural_all":
    return True
```

#### 2. 修改 `configs/region_dict.gansu.json`
添加新的地区范围 `gansu_city_target_area`，只包含市级定向的实施区域：

```json
"gansu_city_target_area": [
  "天水市", "秦州区", "麦积区", "清水县", "秦安县", "甘谷县", "武山县", "张家川回族自治县",
  "张掖市", "甘州区", "肃南裕固族自治县", "民乐县", "临泽县", "高台县", "山丹县",
  "白银市", "白银区", "平川区", "靖远县", "会宁县", "景泰县",
  ...
]
```

#### 3. 修改 `configs/policy_rules.gansu.json`
市级定向培养使用新的地区范围：

```json
// 市级定向培养
"region_scope": "gansu_city_target_area"

// 省属公费师范生（保持不变）
"region_scope": "gansu_local_target_area"
```

### 修复原理
- `gansu_local_target_area`: 包含全省所有市州，用于省属公费师范生等面向全省的计划
- `gansu_city_target_area`: 只包含特定的定向市（如天水市、张掖市等），用于市级定向培养

这样，兰州市考生可以报考省属公费师范生（使用 `gansu_local_target_area`），但不能报考市级定向培养（使用 `gansu_city_target_area`，不包含兰州市）。

---

## 测试验证

运行 `backend/eval/test_edge_cases_v2.py` 验证修复：

```bash
cd "D:\gaokao project"
python -X utf8 backend/eval/test_edge_cases_v2.py
```

### 测试结果
- **总计**: 60 个用例
- **通过**: 60
- **失败**: 0
- **通过率**: 100%

### 关键测试用例验证

| 用例编号 | 计划类型 | 测试场景 | 预期 | 实际 | 状态 |
|---------|---------|---------|------|------|------|
| P-02-02 | 两州一县专项 | 汉族考生 | eligible | eligible | ✅ |
| P-02-05 | 两州一县专项 | 汉族考生户籍5年 | eligible | eligible | ✅ |
| P-01-10 | 革命老区专项 | 户籍本地但学籍外地 | blocked | blocked | ✅ |
| P-03-06 | 市级定向培养 | 非定向市户籍（兰州市） | blocked | blocked | ✅ |

---

## 修改文件清单

1. `backend/rules/eligibility.py` - 修复 P-02 民族判定逻辑、修复 P-03 地区匹配逻辑
2. `configs/policy_rules.gansu.json` - 修复 P-01 革命老区地区字段、修复 P-03 市级定向地区范围
3. `configs/region_dict.gansu.json` - 修复 P-03 添加市级定向地区字典

---

## 备份信息

原文件已备份在 `D:\gaokao_project_backup_20260324`

---

## 修复完成确认

```
FIX DONE
```
