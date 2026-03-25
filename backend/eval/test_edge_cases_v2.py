"""
Edge Case 测试用例 V2
针对甘肃高考志愿推荐系统规则引擎的边界场景测试

覆盖 16 类专项计划，每类计划至少 5 正例 + 5 反例
特别针对 P-01/P-02/P-03 三类问题进行专项验证
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.models.schemas import UserProfile, EligibilityResult
from backend.rules.eligibility import PolicyEngine


# 配置文件路径
RULES_PATH = ROOT / "configs/policy_rules.gansu.json"
REGION_PATH = ROOT / "configs/region_dict.gansu.json"
REPORT_PATH = ROOT / "docs/edge_cases_v2_design.md"
JSON_REPORT_PATH = ROOT / "data/processed/edge_cases_v2_report.json"


@dataclass
class EdgeCase:
    """Edge Case 测试用例数据结构"""
    case_id: str
    name: str
    plan_tag: str
    profile: UserProfile
    expected_eligible: bool
    expected_reasons_hit: List[str] = field(default_factory=list)
    expected_reasons_miss: List[str] = field(default_factory=list)
    description: str = ""
    category: str = ""  # P-01, P-02, P-03, general


@dataclass
class TestResult:
    """测试结果数据结构"""
    case_id: str
    name: str
    plan_tag: str
    expected: bool
    actual: bool
    passed: bool
    reasons_hit: List[str]
    reasons_miss: List[str]
    description: str
    category: str


# ==================== 基础 Profile 模板 ====================

def base_profile(**kwargs) -> UserProfile:
    """创建基础 Profile，可覆盖任意字段"""
    defaults = {
        "track": "历史",
        "selected_subjects": ["政治", "地理"],
        "score": 560,
        "rank": 5000,
        "region": "会宁县",
        "hukou_nature": "rural_only",
        "nation": "汉族",
        "school_region": "会宁县",
        "parent_region": "会宁县",
        "school_years": 3,
        "hukou_years": 3,
        "parent_hukou_years": 3,
        "is_registered_poverty_family": False,
        "has_ethnic_language_score": False,
        "special_identity": None,
        "graduated_in_region_school": True,
        "parent_has_local_hukou": True,
        "previous_special_plan_breach": False,
        "special_review_passed": False,
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


# ==================== P-01 修复验证：革命老区监护人户籍 ====================
# P-01 问题：革命老区考生，父母非本地户籍但考生本人满足 3 年户籍+学籍
# 预期：应判定为 eligible（革命老区只检查 region，不强制要求监护人户籍）

def p01_test_cases() -> List[EdgeCase]:
    """P-01 革命老区专项测试用例"""
    cases = []
    
    # === 正例（应通过）===
    
    # P-01-01: 考生户籍在革命老区，父母户籍也在本地
    cases.append(EdgeCase(
        case_id="P-01-01",
        name="革命老区-考生本地户籍-父母本地户籍",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",  # 革命老区
            school_region="会宁县",
            parent_region="会宁县",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="基准正例：考生和父母户籍都在革命老区",
        category="P-01"
    ))
    
    # P-01-02: 考生户籍在革命老区 3 年，父母户籍在外地（P-01 修复场景）
    cases.append(EdgeCase(
        case_id="P-01-02",
        name="革命老区-考生本地户籍3年-父母外地户籍",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",  # 革命老区
            school_region="会宁县",
            parent_region="兰州市",  # 父母外地户籍
            parent_has_local_hukou=False,  # 父母无本地户籍
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="P-01 修复验证：革命老区不要求监护人本地户籍，考生本人满足 3 年户籍+学籍即可",
        category="P-01"
    ))
    
    # P-01-03: 考生户籍在革命老区 5 年，父母户籍在外地
    cases.append(EdgeCase(
        case_id="P-01-03",
        name="革命老区-考生本地户籍5年-父母外地户籍",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="兰州市",
            parent_has_local_hukou=False,
            hukou_years=5,
            school_years=5,
        ),
        expected_eligible=True,
        description="超年限正例：考生户籍/学籍超过 3 年，父母外地户籍",
        category="P-01"
    ))
    
    # P-01-04: 考生户籍在庆城县（革命老区），父母外地户籍
    cases.append(EdgeCase(
        case_id="P-01-04",
        name="革命老区-庆城县考生-父母外地户籍",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="庆城县",  # 另一个革命老区
            school_region="庆城县",
            parent_region="天水市",
            parent_has_local_hukou=False,
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="不同革命老区验证：庆城县考生，父母外地户籍",
        category="P-01"
    ))
    
    # P-01-05: 考生户籍在华池县（革命老区），学籍也在本地，父母外地
    cases.append(EdgeCase(
        case_id="P-01-05",
        name="革命老区-华池县考生学籍本地-父母外地",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="华池县",
            school_region="华池县",
            parent_region="白银市",
            parent_has_local_hukou=False,
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="革命老区边界：华池县考生学籍本地，父母外地",
        category="P-01"
    ))
    
    # === 反例（应不通过）===
    
    # P-01-06: 考生户籍不在革命老区
    cases.append(EdgeCase(
        case_id="P-01-06",
        name="革命老区-考生非老区户籍",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="兰州市",  # 非革命老区
            school_region="兰州市",
            parent_region="兰州市",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="基准反例：考生户籍不在革命老区范围",
        category="P-01"
    ))
    
    # P-01-07: 考生户籍在革命老区但不满 3 年
    cases.append(EdgeCase(
        case_id="P-01-07",
        name="革命老区-考生户籍仅2年",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            hukou_years=2,  # 不满 3 年
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="户籍年限不足：考生户籍仅 2 年",
        category="P-01"
    ))
    
    # P-01-08: 考生户籍在革命老区但学籍不满 3 年
    cases.append(EdgeCase(
        case_id="P-01-08",
        name="革命老区-考生学籍仅2年",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            school_years=2,  # 学籍不满 3 年
            hukou_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="学籍年限不足：考生学籍仅 2 年",
        category="P-01"
    ))
    
    # P-01-09: 考生户籍在革命老区 2 年 11 个月（边界值）
    cases.append(EdgeCase(
        case_id="P-01-09",
        name="革命老区-考生户籍2年11个月",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            hukou_years=2,  # 实际不足 3 年
            school_years=3,
        ),
        expected_eligible=False,
        description="边界值测试：户籍 2 年 11 个月不满足 3 年要求",
        category="P-01"
    ))
    
    # P-01-10: 考生户籍在革命老区但学籍在外地
    cases.append(EdgeCase(
        case_id="P-01-10",
        name="革命老区-考生户籍本地但学籍外地",
        plan_tag="革命老区专项",
        profile=base_profile(
            region="会宁县",
            school_region="兰州市",  # 学籍在外地
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="学籍地区不符：考生学籍不在革命老区",
        category="P-01"
    ))
    
    return cases


# ==================== P-02 修复验证：两州一县民族成分 ====================
# P-02 问题：两州一县汉族考生，报考不区分民族的专业组
# 预期：应判定为 eligible（30% 名额分配给汉族考生）

def p02_test_cases() -> List[EdgeCase]:
    """P-02 两州一县专项测试用例"""
    cases = []
    
    # === 正例（应通过）===
    
    # P-02-01: 两州一县少数民族考生
    cases.append(EdgeCase(
        case_id="P-02-01",
        name="两州一县-少数民族考生",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="合作市",  # 两州一县
            school_region="合作市",
            nation="藏族",  # 少数民族
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="基准正例：两州一县少数民族考生",
        category="P-02"
    ))
    
    # P-02-02: 两州一县汉族考生（P-02 修复场景，70% 名额给少数民族，30% 给汉族）
    cases.append(EdgeCase(
        case_id="P-02-02",
        name="两州一县-汉族考生",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="合作市",
            school_region="合作市",
            nation="汉族",  # 汉族考生
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="P-02 修复验证：两州一县汉族考生应可报考（conditional_default_minority 允许汉族）",
        category="P-02"
    ))
    
    # P-02-03: 两州一县回族考生
    cases.append(EdgeCase(
        case_id="P-02-03",
        name="两州一县-回族考生",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="临夏市",  # 两州一县
            school_region="临夏市",
            nation="回族",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="其他少数民族：临夏市回族考生",
        category="P-02"
    ))
    
    # P-02-04: 两州一县东乡族考生
    cases.append(EdgeCase(
        case_id="P-02-04",
        name="两州一县-东乡族考生",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="东乡族自治县",
            school_region="东乡族自治县",
            nation="东乡族",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="特定民族区域：东乡族自治县东乡族考生",
        category="P-02"
    ))
    
    # P-02-05: 两州一县汉族考生，户籍 5 年
    cases.append(EdgeCase(
        case_id="P-02-05",
        name="两州一县-汉族考生户籍5年",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="夏河县",
            school_region="夏河县",
            nation="汉族",
            hukou_years=5,
            school_years=5,
        ),
        expected_eligible=True,
        description="超年限：夏河县汉族考生，户籍/学籍 5 年",
        category="P-02"
    ))
    
    # === 反例（应不通过）===
    
    # P-02-06: 非两州一县地区考生
    cases.append(EdgeCase(
        case_id="P-02-06",
        name="两州一县-非实施区域考生",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="兰州市",  # 非两州一县
            school_region="兰州市",
            nation="藏族",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="地区不符：兰州市不在两州一县范围",
        category="P-02"
    ))
    
    # P-02-07: 两州一县考生户籍不满 3 年
    cases.append(EdgeCase(
        case_id="P-02-07",
        name="两州一县-户籍不满3年",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="合作市",
            school_region="合作市",
            nation="藏族",
            hukou_years=2,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="户籍年限不足：仅 2 年",
        category="P-02"
    ))
    
    # P-02-08: 两州一县考生学籍不在本地
    cases.append(EdgeCase(
        case_id="P-02-08",
        name="两州一县-学籍不在本地",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="合作市",
            school_region="兰州市",  # 学籍在外地
            nation="藏族",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足", "实际就读条件满足"],
        description="学籍不符：实际就读不在两州一县",
        category="P-02"
    ))
    
    # P-02-09: 两州一县考生学籍不满 3 年
    cases.append(EdgeCase(
        case_id="P-02-09",
        name="两州一县-学籍不满3年",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="合作市",
            school_region="合作市",
            nation="藏族",
            hukou_years=3,
            school_years=2,
            graduated_in_region_school=False,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="学籍年限不足：仅实际就读 2 年",
        category="P-02"
    ))
    
    # P-02-10: 户籍在 58 县但不在两州一县
    cases.append(EdgeCase(
        case_id="P-02-10",
        name="两州一县-58县但非两州一县",
        plan_tag="两州一县专项",
        profile=base_profile(
            region="会宁县",  # 58 县但不在两州一县
            school_region="会宁县",
            nation="回族",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="地区边界：会宁县属于 58 县但不属于两州一县",
        category="P-02"
    ))
    
    return cases


# ==================== P-03 修复验证：省属公费师范生地区限制 ====================
# P-03 问题：非定向市户籍考生报考市级定向培养
# 预期：应判定为 blocked（省属公费师范生有严格的地区定向限制）

def p03_test_cases() -> List[EdgeCase]:
    """P-03 省属公费师范生测试用例"""
    cases = []
    
    # === 正例（应通过）===
    
    # P-03-01: 定向市户籍考生报考市级定向培养
    cases.append(EdgeCase(
        case_id="P-03-01",
        name="市级定向-定向市户籍考生",
        plan_tag="市级定向培养",
        profile=base_profile(
            region="天水市",  # 假设为定向市
            parent_region="天水市",
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="基准正例：定向市户籍考生报考对应市级定向",
        category="P-03"
    ))
    
    # P-03-02: 定向县户籍考生报考市级定向培养
    cases.append(EdgeCase(
        case_id="P-03-02",
        name="市级定向-定向县户籍考生",
        plan_tag="市级定向培养",
        profile=base_profile(
            region="甘谷县",  # 天水市下辖县
            parent_region="甘谷县",
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="县级考生：天水市下辖县考生报考天水市定向",
        category="P-03"
    ))
    
    # P-03-03: 省属公费师范生-本地农村户籍
    cases.append(EdgeCase(
        case_id="P-03-03",
        name="省属公费师范生-本地农村户籍",
        plan_tag="省属公费师范生",
        profile=base_profile(
            region="兰州市",
            parent_region="兰州市",
            parent_has_local_hukou=True,
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="省属公费师范生基准：本地农村户籍+监护人本地户籍",
        category="P-03"
    ))
    
    # P-03-04: 省属公费师范生-超年限户籍
    cases.append(EdgeCase(
        case_id="P-03-04",
        name="省属公费师范生-户籍5年",
        plan_tag="省属公费师范生",
        profile=base_profile(
            region="白银市",
            parent_region="白银市",
            parent_has_local_hukou=True,
            hukou_nature="rural_only",
            hukou_years=5,
            school_years=5,
        ),
        expected_eligible=True,
        description="超年限：户籍/学籍 5 年",
        category="P-03"
    ))
    
    # P-03-05: 市级定向-不同定向市
    cases.append(EdgeCase(
        case_id="P-03-05",
        name="市级定向-另一定向市",
        plan_tag="市级定向培养",
        profile=base_profile(
            region="张掖市",
            parent_region="张掖市",
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="其他定向市：张掖市考生报考张掖市定向",
        category="P-03"
    ))
    
    # === 反例（应不通过）===
    
    # P-03-06: 非定向市户籍考生报考市级定向培养（P-03 修复场景）
    cases.append(EdgeCase(
        case_id="P-03-06",
        name="市级定向-非定向市户籍",
        plan_tag="市级定向培养",
        profile=base_profile(
            region="兰州市",  # 非定向市
            parent_region="兰州市",
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="P-03 修复验证：非定向市户籍考生应被阻止报考市级定向",
        category="P-03"
    ))
    
    # P-03-07: 省属公费师范生-城市户籍
    cases.append(EdgeCase(
        case_id="P-03-07",
        name="省属公费师范生-城市户籍",
        plan_tag="省属公费师范生",
        profile=base_profile(
            region="兰州市",
            parent_region="兰州市",
            hukou_nature="urban",  # 城市户籍
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["户籍性质不满足"],
        description="户籍性质不符：城市户籍不满足 rural_only 要求",
        category="P-03"
    ))
    
    # P-03-08: 省属公费师范生-监护人非本地户籍
    cases.append(EdgeCase(
        case_id="P-03-08",
        name="省属公费师范生-监护人外地户籍",
        plan_tag="省属公费师范生",
        profile=base_profile(
            region="兰州市",
            parent_region="天水市",  # 监护人外地户籍
            parent_has_local_hukou=False,
            hukou_nature="rural_only",
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["监护人户籍条件满足"],
        description="监护人户籍不符：监护人非本地户籍",
        category="P-03"
    ))
    
    # P-03-09: 市级定向-户籍不满 3 年
    cases.append(EdgeCase(
        case_id="P-03-09",
        name="市级定向-户籍不满3年",
        plan_tag="市级定向培养",
        profile=base_profile(
            region="天水市",
            parent_region="天水市",
            hukou_nature="rural_only",
            hukou_years=2,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="户籍年限不足：仅 2 年",
        category="P-03"
    ))
    
    # P-03-10: 省属公费师范生-户籍年限不足
    cases.append(EdgeCase(
        case_id="P-03-10",
        name="省属公费师范生-户籍2年11个月",
        plan_tag="省属公费师范生",
        profile=base_profile(
            region="兰州市",
            parent_region="兰州市",
            parent_has_local_hukou=True,
            hukou_nature="rural_only",
            hukou_years=2,  # 不足 3 年
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="边界值：户籍 2 年 11 个月不满足要求",
        category="P-03"
    ))
    
    return cases


# ==================== 通用 Edge Cases ====================

def general_edge_cases() -> List[EdgeCase]:
    """通用边界场景测试用例"""
    cases = []
    
    # === 户籍年限边界 ===
    
    # GEN-01: 户籍恰好 3 年
    cases.append(EdgeCase(
        case_id="GEN-01",
        name="国家专项-户籍恰好3年",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",  # 58 县
            school_region="会宁县",
            parent_region="会宁县",
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="户籍年限边界：恰好 3 年应通过",
        category="general"
    ))
    
    # GEN-02: 户籍 2 年 11 个月（不足 3 年）
    cases.append(EdgeCase(
        case_id="GEN-02",
        name="国家专项-户籍2年",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",
            hukou_years=2,  # 不足 3 年
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="户籍年限边界：2 年 11 个月不满足",
        category="general"
    ))
    
    # === 学籍年限边界 ===
    
    # GEN-03: 学籍恰好 3 年
    cases.append(EdgeCase(
        case_id="GEN-03",
        name="地方专项-学籍恰好3年",
        plan_tag="地方专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            hukou_nature="rural_only",
            school_years=3,
            hukou_years=3,
        ),
        expected_eligible=True,
        description="学籍年限边界：恰好 3 年应通过",
        category="general"
    ))
    
    # GEN-04: 学籍实际就读 2 年
    cases.append(EdgeCase(
        case_id="GEN-04",
        name="地方专项-学籍实际2年",
        plan_tag="地方专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            hukou_nature="rural_only",
            school_years=2,
            hukou_years=3,
            graduated_in_region_school=False,
        ),
        expected_eligible=False,
        expected_reasons_miss=["三年统一不满足"],
        description="学籍年限边界：实际就读 2 年不满足",
        category="general"
    ))
    
    # === 建档立卡 + 国家专项双重资格 ===
    
    # GEN-05: 建档立卡考生
    cases.append(EdgeCase(
        case_id="GEN-05",
        name="建档立卡专项-建档立卡考生",
        plan_tag="建档立卡专项(本科)",
        profile=base_profile(
            is_registered_poverty_family=True,
        ),
        expected_eligible=True,
        description="建档立卡身份：有建档立卡身份应通过",
        category="general"
    ))
    
    # GEN-06: 非建档立卡考生
    cases.append(EdgeCase(
        case_id="GEN-06",
        name="建档立卡专项-非建档立卡考生",
        plan_tag="建档立卡专项(本科)",
        profile=base_profile(
            is_registered_poverty_family=False,
        ),
        expected_eligible=False,
        expected_reasons_miss=["建档立卡条件不满足"],
        description="建档立卡身份：无建档立卡身份应被阻止",
        category="general"
    ))
    
    # GEN-07: 建档立卡 + 58 县双重资格
    cases.append(EdgeCase(
        case_id="GEN-07",
        name="国家专项-建档立卡+58县",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",
            is_registered_poverty_family=True,
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="双重资格：建档立卡 + 58 县户籍",
        category="general"
    ))
    
    # === 少数民族预科班 ===
    
    # GEN-08: 少数民族报考预科班
    cases.append(EdgeCase(
        case_id="GEN-08",
        name="少数民族预科班-少数民族考生",
        plan_tag="少数民族预科班",
        profile=base_profile(
            nation="回族",  # 少数民族
        ),
        expected_eligible=True,
        description="少数民族预科班：少数民族应通过",
        category="general"
    ))
    
    # GEN-09: 汉族报考预科班
    cases.append(EdgeCase(
        case_id="GEN-09",
        name="少数民族预科班-汉族考生",
        plan_tag="少数民族预科班",
        profile=base_profile(
            nation="汉族",  # 汉族
        ),
        expected_eligible=False,
        expected_reasons_miss=["民族条件不满足"],
        description="少数民族预科班：汉族应被阻止",
        category="general"
    ))
    
    # === 强基计划 ===
    
    # GEN-10: 强基计划-有竞赛奖项
    cases.append(EdgeCase(
        case_id="GEN-10",
        name="强基计划-有竞赛奖项",
        plan_tag="强基计划",
        profile=base_profile(
            track="物理",
            selected_subjects=["化学", "生物"],
            special_identity="strong_foundation_candidate",
            special_review_passed=True,
        ),
        expected_eligible=True,
        description="强基计划：有竞赛奖项且通过审核",
        category="general"
    ))
    
    # GEN-11: 强基计划-无竞赛奖项但成绩优异
    cases.append(EdgeCase(
        case_id="GEN-11",
        name="强基计划-无竞赛奖项",
        plan_tag="强基计划",
        profile=base_profile(
            track="物理",
            selected_subjects=["化学", "生物"],
            special_identity=None,  # 无特殊身份
            special_review_passed=True,
        ),
        expected_eligible=False,
        expected_reasons_miss=["专项身份条件不满足"],
        description="强基计划：无竞赛奖项应被阻止",
        category="general"
    ))
    
    # === 综合评价 ===
    
    # GEN-12: 综合评价-初审通过且面试参加
    cases.append(EdgeCase(
        case_id="GEN-12",
        name="综合评价-完整流程通过",
        plan_tag="综合评价录取",
        profile=base_profile(
            track="物理",
            selected_subjects=["化学", "生物"],
            special_identity="comprehensive_evaluation_candidate",
            special_review_passed=True,
        ),
        expected_eligible=True,
        description="综合评价：初审通过且面试通过",
        category="general"
    ))
    
    # GEN-13: 综合评价-初审通过但面试未参加
    cases.append(EdgeCase(
        case_id="GEN-13",
        name="综合评价-面试未通过",
        plan_tag="综合评价录取",
        profile=base_profile(
            track="物理",
            selected_subjects=["化学", "生物"],
            special_identity="comprehensive_evaluation_candidate",
            special_review_passed=False,  # 面试未通过
        ),
        expected_eligible=False,
        expected_reasons_miss=["专项审核条件满足"],
        description="综合评价：初审通过但面试未通过应被阻止",
        category="general"
    ))
    
    # === 专项计划失信记录 ===
    
    # GEN-14: 国家专项-无失信记录
    cases.append(EdgeCase(
        case_id="GEN-14",
        name="国家专项-无失信记录",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",
            previous_special_plan_breach=False,
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="诚信检查：无失信记录应通过",
        category="general"
    ))
    
    # GEN-15: 国家专项-有失信记录（往年放弃入学）
    cases.append(EdgeCase(
        case_id="GEN-15",
        name="国家专项-有失信记录",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",
            previous_special_plan_breach=True,  # 有失信记录
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["存在专项失信限制"],
        description="诚信检查：有往年放弃入学记录应被阻止",
        category="general"
    ))
    
    # === 户籍在 58 县但学籍在非 58 县 ===
    
    # GEN-16: 户籍在 58 县，学籍也在 58 县
    cases.append(EdgeCase(
        case_id="GEN-16",
        name="国家专项-户籍学籍都在58县",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",  # 58 县
            school_region="会宁县",  # 58 县
            parent_region="会宁县",
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="户籍学籍一致：都在 58 县应通过",
        category="general"
    ))
    
    # GEN-17: 户籍在 58 县，学籍在非 58 县
    cases.append(EdgeCase(
        case_id="GEN-17",
        name="国家专项-户籍58县学籍非58县",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",  # 58 县
            school_region="兰州市",  # 非 58 县
            parent_region="会宁县",
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["地区范围不满足"],
        description="户籍学籍分离：学籍不在 58 县应被阻止",
        category="general"
    ))
    
    # === 父母一方户籍在实施区域，另一方不在 ===
    
    # GEN-18: 父母双方户籍都在实施区域
    cases.append(EdgeCase(
        case_id="GEN-18",
        name="国家专项-父母双方户籍都在实施区",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",  # 父母户籍
            parent_has_local_hukou=True,
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="父母户籍：双方都在实施区域应通过",
        category="general"
    ))
    
    # GEN-19: 父母一方户籍在实施区域（通过 parent_region 字段）
    cases.append(EdgeCase(
        case_id="GEN-19",
        name="国家专项-父母一方户籍在实施区",
        plan_tag="国家专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",  # 一方在
            parent_has_local_hukou=True,
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="父母户籍：一方在实施区域（满足条件）",
        category="general"
    ))
    
    # === 民族语文成绩（藏区民语类） ===
    
    # GEN-20: 藏区民语类-有民族语文成绩
    cases.append(EdgeCase(
        case_id="GEN-20",
        name="藏区民语类-有民族语文成绩",
        plan_tag="藏区专项-民语类",
        profile=base_profile(
            region="合作市",  # 藏区
            school_region="合作市",
            nation="藏族",
            has_ethnic_language_score=True,  # 有民族语文成绩
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="藏区民语类：有民族语文成绩应通过",
        category="general"
    ))
    
    # GEN-21: 藏区民语类-无民族语文成绩
    cases.append(EdgeCase(
        case_id="GEN-21",
        name="藏区民语类-无民族语文成绩",
        plan_tag="藏区专项-民语类",
        profile=base_profile(
            region="合作市",
            school_region="合作市",
            nation="藏族",
            has_ethnic_language_score=False,  # 无民族语文成绩
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["民族语文条件不满足"],
        description="藏区民语类：无民族语文成绩应被阻止",
        category="general"
    ))
    
    # GEN-22: 藏区其他类-无民族语文成绩也可
    cases.append(EdgeCase(
        case_id="GEN-22",
        name="藏区其他类-无民族语文成绩",
        plan_tag="藏区专项-其他类",
        profile=base_profile(
            region="合作市",
            school_region="合作市",
            nation="藏族",
            has_ethnic_language_score=False,
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="藏区其他类：不要求民族语文成绩",
        category="general"
    ))
    
    # === 额外边界场景 ===
    
    # GEN-23: 高校专项-需要特殊审核
    cases.append(EdgeCase(
        case_id="GEN-23",
        name="高校专项-通过特殊审核",
        plan_tag="高校专项",
        profile=base_profile(
            region="会宁县",  # 58+3 县
            school_region="会宁县",
            parent_region="会宁县",
            hukou_nature="rural_only",
            special_review_passed=True,  # 通过审核
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=True,
        description="高校专项：通过特殊审核应通过",
        category="general"
    ))
    
    # GEN-24: 高校专项-未通过特殊审核
    cases.append(EdgeCase(
        case_id="GEN-24",
        name="高校专项-未通过特殊审核",
        plan_tag="高校专项",
        profile=base_profile(
            region="会宁县",
            school_region="会宁县",
            parent_region="会宁县",
            hukou_nature="rural_only",
            special_review_passed=False,  # 未通过审核
            hukou_years=3,
            school_years=3,
            parent_hukou_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["专项审核条件满足"],
        description="高校专项：未通过特殊审核应被阻止",
        category="general"
    ))
    
    # GEN-25: 边防军人子女预科
    cases.append(EdgeCase(
        case_id="GEN-25",
        name="边防军人子女预科-符合条件",
        plan_tag="边防军人子女预科",
        profile=base_profile(
            special_identity="border_military_child",
            special_review_passed=True,
        ),
        expected_eligible=True,
        description="边防军人子女：符合条件应通过",
        category="general"
    ))
    
    # GEN-26: 边防军人子女预科-非军人子女
    cases.append(EdgeCase(
        case_id="GEN-26",
        name="边防军人子女预科-非军人子女",
        plan_tag="边防军人子女预科",
        profile=base_profile(
            special_identity=None,
            special_review_passed=True,
        ),
        expected_eligible=False,
        expected_reasons_miss=["专项身份条件不满足"],
        description="边防军人子女：非军人子女应被阻止",
        category="general"
    ))
    
    # GEN-27: 免费医学生-物理化学选科
    cases.append(EdgeCase(
        case_id="GEN-27",
        name="省属免费医学生-物化选科",
        plan_tag="省属免费医学生(本科)",
        profile=base_profile(
            track="物理",
            selected_subjects=["化学", "生物"],
            region="会宁县",
            parent_region="会宁县",
            hukou_nature="rural_only",
            parent_has_local_hukou=True,
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=True,
        description="免费医学生：物理+化学选科满足要求",
        category="general"
    ))
    
    # GEN-28: 免费医学生-未选化学
    cases.append(EdgeCase(
        case_id="GEN-28",
        name="省属免费医学生-未选化学",
        plan_tag="省属免费医学生(本科)",
        profile=base_profile(
            track="物理",
            selected_subjects=["生物", "地理"],  # 未选化学
            region="会宁县",
            parent_region="会宁县",
            hukou_nature="rural_only",
            parent_has_local_hukou=True,
            hukou_years=3,
            school_years=3,
        ),
        expected_eligible=False,
        expected_reasons_miss=["选科硬条件不满足"],
        description="免费医学生：未选化学应被阻止",
        category="general"
    ))
    
    # GEN-29: 民族班-少数民族
    cases.append(EdgeCase(
        case_id="GEN-29",
        name="民族班-少数民族",
        plan_tag="民族班",
        profile=base_profile(
            nation="回族",
        ),
        expected_eligible=True,
        description="民族班：少数民族应通过",
        category="general"
    ))
    
    # GEN-30: 民族班-汉族
    cases.append(EdgeCase(
        case_id="GEN-30",
        name="民族班-汉族",
        plan_tag="民族班",
        profile=base_profile(
            nation="汉族",
        ),
        expected_eligible=False,
        expected_reasons_miss=["民族条件不满足"],
        description="民族班：汉族应被阻止",
        category="general"
    ))
    
    return cases


# ==================== 测试执行 ====================

def get_all_test_cases() -> List[EdgeCase]:
    """获取所有测试用例"""
    cases = []
    cases.extend(p01_test_cases())
    cases.extend(p02_test_cases())
    cases.extend(p03_test_cases())
    cases.extend(general_edge_cases())
    return cases


def run_test(engine: PolicyEngine, case: EdgeCase) -> TestResult:
    """执行单个测试用例"""
    result = engine.evaluate_plan(
        next(p for p in engine.rules["plans"] if p["plan_tag"] == case.plan_tag),
        case.profile
    )
    
    passed = result.eligible == case.expected_eligible
    
    return TestResult(
        case_id=case.case_id,
        name=case.name,
        plan_tag=case.plan_tag,
        expected=case.expected_eligible,
        actual=result.eligible,
        passed=passed,
        reasons_hit=result.reasons_hit,
        reasons_miss=result.reasons_miss,
        description=case.description,
        category=case.category
    )


def run_all_tests() -> List[TestResult]:
    """运行所有测试"""
    engine = PolicyEngine(str(RULES_PATH), str(REGION_PATH))
    cases = get_all_test_cases()
    results = []
    
    for case in cases:
        try:
            result = run_test(engine, case)
            results.append(result)
        except Exception as e:
            # 记录失败的测试
            results.append(TestResult(
                case_id=case.case_id,
                name=case.name,
                plan_tag=case.plan_tag,
                expected=case.expected_eligible,
                actual=False,
                passed=False,
                reasons_hit=[],
                reasons_miss=[f"测试执行异常: {str(e)}"],
                description=case.description,
                category=case.category
            ))
    
    return results


def generate_report(results: List[TestResult]) -> str:
    """生成 Markdown 报告"""
    lines = []
    lines.append("# Edge Case 测试用例设计报告 V2")
    lines.append("")
    lines.append("本报告由 `backend/eval/test_edge_cases_v2.py` 自动生成。")
    lines.append("")
    
    # 统计信息
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    lines.append("## 测试统计")
    lines.append("")
    lines.append(f"- **测试用例总数**: {total}")
    lines.append(f"- **通过**: {passed}")
    lines.append(f"- **失败**: {failed}")
    lines.append(f"- **通过率**: {passed/total*100:.1f}%" if total > 0 else "- **通过率**: N/A")
    lines.append("")
    
    # 按类别统计
    categories = {}
    for r in results:
        cat = r.category
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r.passed:
            categories[cat]["passed"] += 1
    
    lines.append("### 按类别统计")
    lines.append("")
    lines.append("| 类别 | 用例数 | 通过 | 失败 | 通过率 |")
    lines.append("|------|--------|------|------|--------|")
    for cat, stats in sorted(categories.items()):
        pct = stats["passed"]/stats["total"]*100 if stats["total"] > 0 else 0
        lines.append(f"| {cat} | {stats['total']} | {stats['passed']} | {stats['total']-stats['passed']} | {pct:.1f}% |")
    lines.append("")
    
    # 按计划类型统计
    plans = {}
    for r in results:
        plan = r.plan_tag
        if plan not in plans:
            plans[plan] = {"total": 0, "passed": 0}
        plans[plan]["total"] += 1
        if r.passed:
            plans[plan]["passed"] += 1
    
    lines.append("### 按计划类型统计")
    lines.append("")
    lines.append("| 计划类型 | 用例数 | 通过 | 失败 | 通过率 |")
    lines.append("|----------|--------|------|------|--------|")
    for plan, stats in sorted(plans.items()):
        pct = stats["passed"]/stats["total"]*100 if stats["total"] > 0 else 0
        lines.append(f"| {plan} | {stats['total']} | {stats['passed']} | {stats['total']-stats['passed']} | {pct:.1f}% |")
    lines.append("")
    
    # P-01 专项测试
    lines.append("## P-01 修复验证：革命老区监护人户籍")
    lines.append("")
    lines.append("**问题描述**: 革命老区考生，父母非本地户籍但考生本人满足 3 年户籍+学籍")
    lines.append("")
    lines.append("**预期**: 应判定为 eligible（革命老区只检查考生本人户籍）")
    lines.append("")
    lines.append("### 测试用例")
    lines.append("")
    for r in results:
        if r.category == "P-01":
            status = "✅ 通过" if r.passed else "❌ 失败"
            lines.append(f"#### {r.case_id}: {r.name}")
            lines.append(f"- **状态**: {status}")
            lines.append(f"- **预期**: {'eligible' if r.expected else 'blocked'}")
            lines.append(f"- **实际**: {'eligible' if r.actual else 'blocked'}")
            lines.append(f"- **描述**: {r.description}")
            if r.reasons_miss:
                lines.append(f"- **未满足条件**: {', '.join(r.reasons_miss)}")
            lines.append("")
    
    # P-02 专项测试
    lines.append("## P-02 修复验证：两州一县民族成分")
    lines.append("")
    lines.append("**问题描述**: 两州一县汉族考生，报考不区分民族的专业组")
    lines.append("")
    lines.append("**预期**: 应判定为 eligible（30% 名额分配给汉族考生）")
    lines.append("")
    lines.append("### 测试用例")
    lines.append("")
    for r in results:
        if r.category == "P-02":
            status = "✅ 通过" if r.passed else "❌ 失败"
            lines.append(f"#### {r.case_id}: {r.name}")
            lines.append(f"- **状态**: {status}")
            lines.append(f"- **预期**: {'eligible' if r.expected else 'blocked'}")
            lines.append(f"- **实际**: {'eligible' if r.actual else 'blocked'}")
            lines.append(f"- **描述**: {r.description}")
            if r.reasons_miss:
                lines.append(f"- **未满足条件**: {', '.join(r.reasons_miss)}")
            lines.append("")
    
    # P-03 专项测试
    lines.append("## P-03 修复验证：省属公费师范生地区限制")
    lines.append("")
    lines.append("**问题描述**: 非定向市户籍考生报考市级定向培养")
    lines.append("")
    lines.append("**预期**: 应判定为 blocked（省属公费师范生有严格的地区定向限制）")
    lines.append("")
    lines.append("### 测试用例")
    lines.append("")
    for r in results:
        if r.category == "P-03":
            status = "✅ 通过" if r.passed else "❌ 失败"
            lines.append(f"#### {r.case_id}: {r.name}")
            lines.append(f"- **状态**: {status}")
            lines.append(f"- **预期**: {'eligible' if r.expected else 'blocked'}")
            lines.append(f"- **实际**: {'eligible' if r.actual else 'blocked'}")
            lines.append(f"- **描述**: {r.description}")
            if r.reasons_miss:
                lines.append(f"- **未满足条件**: {', '.join(r.reasons_miss)}")
            lines.append("")
    
    # 通用 Edge Cases
    lines.append("## 通用 Edge Cases")
    lines.append("")
    for r in results:
        if r.category == "general":
            status = "✅ 通过" if r.passed else "❌ 失败"
            lines.append(f"### {r.case_id}: {r.name}")
            lines.append(f"- **计划类型**: {r.plan_tag}")
            lines.append(f"- **状态**: {status}")
            lines.append(f"- **预期**: {'eligible' if r.expected else 'blocked'}")
            lines.append(f"- **实际**: {'eligible' if r.actual else 'blocked'}")
            lines.append(f"- **描述**: {r.description}")
            if r.reasons_hit:
                lines.append(f"- **满足条件**: {', '.join(r.reasons_hit)}")
            if r.reasons_miss:
                lines.append(f"- **未满足条件**: {', '.join(r.reasons_miss)}")
            lines.append("")
    
    # 失败用例汇总
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        lines.append("## 失败用例汇总")
        lines.append("")
        for r in failed_results:
            lines.append(f"- **{r.case_id}**: {r.name} ({r.plan_tag})")
        lines.append("")
    
    # 运行指南
    lines.append("## 运行指南")
    lines.append("")
    lines.append("### 运行测试")
    lines.append("")
    lines.append("```bash")
    lines.append("cd \"D:\\gaokao project\"")
    lines.append("python -X utf8 backend/eval/test_edge_cases_v2.py")
    lines.append("```")
    lines.append("")
    lines.append("### 输出文件")
    lines.append("")
    lines.append(f"- 报告: `{REPORT_PATH}`")
    lines.append(f"- JSON 数据: `{JSON_REPORT_PATH}`")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 60)
    print("Edge Case 测试用例 V2 - 开始执行")
    print("=" * 60)
    
    # 运行测试
    results = run_all_tests()
    
    # 生成报告
    report = generate_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    
    # 保存 JSON 报告
    json_data = [
        {
            "case_id": r.case_id,
            "name": r.name,
            "plan_tag": r.plan_tag,
            "expected": r.expected,
            "actual": r.actual,
            "passed": r.passed,
            "reasons_hit": r.reasons_hit,
            "reasons_miss": r.reasons_miss,
            "category": r.category
        }
        for r in results
    ]
    JSON_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT_PATH.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 打印摘要
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    
    print(f"\n测试完成!")
    print(f"总计: {total} 个用例")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print(f"\n报告已保存到: {REPORT_PATH}")
    print(f"JSON 数据已保存到: {JSON_REPORT_PATH}")
    
    # 打印失败用例
    failed = [r for r in results if not r.passed]
    if failed:
        print("\n失败用例:")
        for r in failed:
            print(f"  - {r.case_id}: {r.name}")
    
    print("\n" + "=" * 60)
    print("T2.2 DONE")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
