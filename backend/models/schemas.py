from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserProfile:
    track: str
    selected_subjects: List[str]
    selected_plan_groups: Optional[List[str]] = None
    score: Optional[int] = None
    rank: Optional[int] = None
    region: Optional[str] = None
    hukou_nature: Optional[str] = None
    nation: Optional[str] = None
    school_region: Optional[str] = None
    parent_region: Optional[str] = None
    school_years: int = 0
    hukou_years: int = 0
    parent_hukou_years: int = 0
    is_registered_poverty_family: bool = False
    has_ethnic_language_score: bool = False
    special_identity: Optional[str] = None
    graduated_in_region_school: bool = True
    parent_has_local_hukou: bool = True
    previous_special_plan_breach: bool = False
    special_review_passed: bool = False


@dataclass
class EligibilityResult:
    plan_tag: str
    eligible: bool
    reasons_hit: List[str] = field(default_factory=list)
    reasons_miss: List[str] = field(default_factory=list)


@dataclass
class RuleEvaluationDetail:
    """单条规则的评估详情"""
    rule_name: str  # 规则名称，如"户籍性质检查"
    rule_clause: str  # 规则条文，如"地方专项计划第2.2条：农村户籍要求"
    required_value: str  # 要求值，如"农村户籍(rural_only)"
    actual_value: str  # 实际值，如"城市户籍(urban)"
    passed: bool  # 是否通过
    failure_reason: Optional[str] = None  # 失败原因，如"考生为城市户籍，不满足农村户籍要求"


@dataclass
class ExplainableResult:
    """可解释的资格判定结果"""
    plan_tag: str  # 计划类型，如"国家专项"
    batch_code: str  # 批次代码，如"本科批(C段)"
    eligible: bool  # 最终是否具备资格
    
    # 判定链路
    rule_evaluations: List[RuleEvaluationDetail] = field(default_factory=list)
    
    # 汇总信息
    total_rules: int = 0  # 总规则数
    passed_rules: int = 0  # 通过规则数
    failed_rules: int = 0  # 失败规则数
    
    # 可读性摘要
    summary: str = ""  # 一句话摘要，如"具备国家专项报考资格"
    detailed_explanation: str = ""  # 详细解释说明
    suggestions: List[str] = field(default_factory=list)  # 给考生的建议
    
    # 原始结果（兼容旧接口）
    reasons_hit: List[str] = field(default_factory=list)
    reasons_miss: List[str] = field(default_factory=list)
