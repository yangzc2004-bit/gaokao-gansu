from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.features.subject_parser import normalize_subjects, subject_expression_match
from backend.models.schemas import EligibilityResult, ExplainableResult, RuleEvaluationDetail, UserProfile


class PolicyEngine:
    def __init__(self, rules_path: str, region_path: str) -> None:
        self.rules = json.loads(Path(rules_path).read_text(encoding="utf-8"))
        self.region_dict = json.loads(Path(region_path).read_text(encoding="utf-8"))

    def evaluate_all(self, profile: UserProfile) -> List[EligibilityResult]:
        return [self.evaluate_plan(plan, profile) for plan in self.rules["plans"]]
    
    def evaluate_all_explainable(self, profile: UserProfile) -> List[ExplainableResult]:
        """评估所有计划，返回可解释结果"""
        return [self.evaluate_plan_explainable(plan, profile) for plan in self.rules["plans"]]

    def evaluate_plan(self, plan: Dict[str, Any], profile: UserProfile) -> EligibilityResult:
        rules = plan["rules"]
        hit: List[str] = []
        miss: List[str] = []

        checks = [
            (self._match_hukou(rules, profile), "户籍性质满足", "户籍性质不满足"),
            (self._match_region(rules, profile), "地区范围满足", "地区范围不满足"),
            (self._match_three_unification(rules, profile), "三年统一满足", "三年统一不满足"),
            (self._match_guardian_region(rules, profile), "监护人户籍条件满足", "监护人户籍条件不满足"),
            (self._match_schooling(rules, profile), "实际就读条件满足", "实际就读条件不满足"),
            (self._match_nation(rules, profile), "民族条件满足", "民族条件不满足"),
            (self._match_special_review(rules, profile), "专项审核条件满足", "专项审核条件不满足"),
            (self._match_special_identity(rules, profile), "专项身份条件满足", "专项身份条件不满足"),
            (self._match_registered_family(rules, profile), "建档立卡条件满足", "建档立卡条件不满足"),
            (self._match_ethnic_language(rules, profile), "民族语文条件满足", "民族语文条件不满足"),
            (self._match_previous_breach(rules, profile), "专项诚信条件满足", "存在专项失信限制")
        ]

        required_subjects = rules.get("subject_logic", {}).get("required_subjects")
        if self._match_subjects(required_subjects, profile):
            hit.append("选科硬条件满足")
        else:
            miss.append("选科硬条件不满足")

        for ok, hit_text, miss_text in checks:
            if ok:
                hit.append(hit_text)
            else:
                miss.append(miss_text)

        return EligibilityResult(
            plan_tag=plan["plan_tag"],
            eligible=len(miss) == 0,
            reasons_hit=hit,
            reasons_miss=miss,
        )
    
    def evaluate_plan_explainable(self, plan: Dict[str, Any], profile: UserProfile) -> ExplainableResult:
        """评估单个计划，返回详细的可解释结果"""
        rules = plan["rules"]
        rule_evaluations: List[RuleEvaluationDetail] = []
        hit: List[str] = []
        miss: List[str] = []
        
        # 1. 户籍性质检查
        hukou_passed = self._match_hukou(rules, profile)
        hukou_mode = rules.get("hukou_nature", "any")
        hukou_detail = RuleEvaluationDetail(
            rule_name="户籍性质检查",
            rule_clause=f"{plan['plan_tag']}户籍要求：{self._get_hukou_rule_clause(hukou_mode)}",
            required_value=self._format_hukou_required(hukou_mode),
            actual_value=self._format_hukou_actual(profile.hukou_nature),
            passed=hukou_passed,
            failure_reason=None if hukou_passed else f"考生户籍为{profile.hukou_nature or '未填写'}，不满足{self._format_hukou_required(hukou_mode)}要求"
        )
        rule_evaluations.append(hukou_detail)
        if hukou_passed:
            hit.append("户籍性质满足")
        else:
            miss.append("户籍性质不满足")
        
        # 2. 地区范围检查
        region_passed = self._match_region(rules, profile)
        scope = rules.get("region_scope")
        region_detail = RuleEvaluationDetail(
            rule_name="地区范围检查",
            rule_clause=f"{plan['plan_tag']}实施区域要求：{self._get_region_rule_clause(scope)}",
            required_value=self._format_region_required(scope),
            actual_value=self._format_region_actual(profile, rules.get("region_compare_fields", [])),
            passed=region_passed,
            failure_reason=None if region_passed else f"考生户籍/学籍不在实施区域内，当前户籍：{profile.region or '未填写'}，学籍：{profile.school_region or '未填写'}"
        )
        rule_evaluations.append(region_detail)
        if region_passed:
            hit.append("地区范围满足")
        else:
            miss.append("地区范围不满足")
        
        # 3. 三年统一检查
        three_uni_passed = self._match_three_unification(rules, profile)
        need_years = int(rules.get("residence_years", 3))
        three_uni_required = rules.get("three_unification_required", False)
        three_uni_detail = RuleEvaluationDetail(
            rule_name="三年统一检查",
            rule_clause=f"{plan['plan_tag']}三年统一要求：{self._get_three_uni_clause(three_uni_required, need_years)}",
            required_value=f"户籍、学籍、监护人户籍均≥{need_years}年" if three_uni_required else "无要求",
            actual_value=f"考生户籍{profile.hukou_years}年，学籍{profile.school_years}年，监护人户籍{profile.parent_hukou_years}年",
            passed=three_uni_passed,
            failure_reason=None if three_uni_passed else self._get_three_uni_failure_reason(profile, need_years)
        )
        rule_evaluations.append(three_uni_detail)
        if three_uni_passed:
            hit.append("三年统一满足")
        else:
            miss.append("三年统一不满足")
        
        # 4. 监护人户籍检查
        guardian_passed = self._match_guardian_region(rules, profile)
        guardian_required = rules.get("guardian_region_required", False)
        guardian_detail = RuleEvaluationDetail(
            rule_name="监护人户籍检查",
            rule_clause=f"{plan['plan_tag']}监护人户籍要求：{'监护人须具有实施区域户籍' if guardian_required else '无要求'}",
            required_value="监护人具有本地户籍" if guardian_required else "无要求",
            actual_value=f"监护人户籍：{profile.parent_region or '未填写'}，是否有本地户籍：{'是' if profile.parent_has_local_hukou else '否'}",
            passed=guardian_passed,
            failure_reason=None if guardian_passed else "监护人无实施区域户籍"
        )
        rule_evaluations.append(guardian_detail)
        if guardian_passed:
            hit.append("监护人户籍条件满足")
        else:
            miss.append("监护人户籍条件不满足")
        
        # 5. 实际就读检查
        schooling_passed = self._match_schooling(rules, profile)
        schooling_required = rules.get("actual_schooling_required", False)
        schooling_detail = RuleEvaluationDetail(
            rule_name="实际就读检查",
            rule_clause=f"{plan['plan_tag']}实际就读要求：{'须在学籍学校实际就读' if schooling_required else '无要求'}",
            required_value="实际就读满3年" if schooling_required else "无要求",
            actual_value=f"实际就读：{'是' if profile.graduated_in_region_school else '否'}",
            passed=schooling_passed,
            failure_reason=None if schooling_passed else "未在学籍学校实际就读满3年"
        )
        rule_evaluations.append(schooling_detail)
        if schooling_passed:
            hit.append("实际就读条件满足")
        else:
            miss.append("实际就读条件不满足")
        
        # 6. 民族成分检查
        nation_passed = self._match_nation(rules, profile)
        lock = rules.get("nation_lock", "none")
        nation_detail = RuleEvaluationDetail(
            rule_name="民族成分检查",
            rule_clause=f"{plan['plan_tag']}民族要求：{self._get_nation_rule_clause(lock)}",
            required_value=self._format_nation_required(lock),
            actual_value=f"考生民族：{profile.nation or '未填写'}",
            passed=nation_passed,
            failure_reason=None if nation_passed else self._get_nation_failure_reason(lock, profile.nation)
        )
        rule_evaluations.append(nation_detail)
        if nation_passed:
            hit.append("民族条件满足")
        else:
            miss.append("民族条件不满足")
        
        # 7. 专项审核检查
        review_passed = self._match_special_review(rules, profile)
        review_required = rules.get("special_review_pass_required", False)
        review_detail = RuleEvaluationDetail(
            rule_name="专项审核检查",
            rule_clause=f"{plan['plan_tag']}专项审核要求：{'须通过高校/省级审核' if review_required else '无要求'}",
            required_value="通过审核" if review_required else "无要求",
            actual_value=f"审核状态：{'已通过' if profile.special_review_passed else '未通过/未申请'}",
            passed=review_passed,
            failure_reason=None if review_passed else "未通过专项审核或未参加审核"
        )
        rule_evaluations.append(review_detail)
        if review_passed:
            hit.append("专项审核条件满足")
        else:
            miss.append("专项审核条件不满足")
        
        # 8. 专项身份检查
        identity_passed = self._match_special_identity(rules, profile)
        expected_identity = rules.get("special_identity_required")
        identity_detail = RuleEvaluationDetail(
            rule_name="专项身份检查",
            rule_clause=f"{plan['plan_tag']}专项身份要求：{self._get_identity_rule_clause(expected_identity)}",
            required_value=self._format_identity_required(expected_identity),
            actual_value=f"考生身份：{profile.special_identity or '普通考生'}",
            passed=identity_passed,
            failure_reason=None if identity_passed else f"不具备{self._format_identity_required(expected_identity)}身份"
        )
        rule_evaluations.append(identity_detail)
        if identity_passed:
            hit.append("专项身份条件满足")
        else:
            miss.append("专项身份条件不满足")
        
        # 9. 建档立卡检查
        poverty_passed = self._match_registered_family(rules, profile)
        poverty_required = rules.get("registered_poverty_family_required", False)
        poverty_detail = RuleEvaluationDetail(
            rule_name="建档立卡检查",
            rule_clause=f"{plan['plan_tag']}建档立卡要求：{'须为建档立卡贫困户' if poverty_required else '无要求'}",
            required_value="建档立卡贫困户" if poverty_required else "无要求",
            actual_value=f"建档立卡状态：{'是' if profile.is_registered_poverty_family else '否'}",
            passed=poverty_passed,
            failure_reason=None if poverty_passed else "非建档立卡贫困户"
        )
        rule_evaluations.append(poverty_detail)
        if poverty_passed:
            hit.append("建档立卡条件满足")
        else:
            miss.append("建档立卡条件不满足")
        
        # 10. 民族语文检查
        lang_passed = self._match_ethnic_language(rules, profile)
        lang_required = rules.get("ethnic_language_score_required", False)
        lang_detail = RuleEvaluationDetail(
            rule_name="民族语文检查",
            rule_clause=f"{plan['plan_tag']}民族语文要求：{'须具有民族语文科目成绩' if lang_required else '无要求'}",
            required_value="有民族语文成绩" if lang_required else "无要求",
            actual_value=f"民族语文成绩：{'有' if profile.has_ethnic_language_score else '无'}",
            passed=lang_passed,
            failure_reason=None if lang_passed else "无民族语文科目成绩"
        )
        rule_evaluations.append(lang_detail)
        if lang_passed:
            hit.append("民族语文条件满足")
        else:
            miss.append("民族语文条件不满足")
        
        # 11. 诚信记录检查
        breach_passed = self._match_previous_breach(rules, profile)
        breach_forbidden = rules.get("previous_special_plan_breach_forbidden", False)
        breach_detail = RuleEvaluationDetail(
            rule_name="诚信记录检查",
            rule_clause=f"{plan['plan_tag']}诚信要求：{'往年被专项计划录取后放弃入学或退学的考生不得报考' if breach_forbidden else '无要求'}",
            required_value="无失信记录" if breach_forbidden else "无要求",
            actual_value=f"失信记录：{'有' if profile.previous_special_plan_breach else '无'}",
            passed=breach_passed,
            failure_reason=None if breach_passed else "往年被专项计划录取后放弃入学或退学，已被限制报考"
        )
        rule_evaluations.append(breach_detail)
        if breach_passed:
            hit.append("专项诚信条件满足")
        else:
            miss.append("存在专项失信限制")
        
        # 12. 选科检查
        required_subjects = rules.get("subject_logic", {}).get("required_subjects")
        subject_passed = self._match_subjects(required_subjects, profile)
        subject_detail = RuleEvaluationDetail(
            rule_name="选科适配检查",
            rule_clause=f"{plan['plan_tag']}选科要求：{self._get_subject_rule_clause(required_subjects)}",
            required_value=self._format_subject_required(required_subjects),
            actual_value=f"考生选科：{profile.track} + {', '.join(profile.selected_subjects)}",
            passed=subject_passed,
            failure_reason=None if subject_passed else f"选科不满足要求，当前选科：{profile.track} + {', '.join(profile.selected_subjects)}"
        )
        rule_evaluations.append(subject_detail)
        if subject_passed:
            hit.append("选科硬条件满足")
        else:
            miss.append("选科硬条件不满足")
        
        # 计算统计
        total_rules = len(rule_evaluations)
        passed_rules = sum(1 for r in rule_evaluations if r.passed)
        failed_rules = total_rules - passed_rules
        eligible = len(miss) == 0
        
        # 生成摘要和建议
        summary = self._generate_summary(plan["plan_tag"], eligible)
        detailed_explanation = self._generate_detailed_explanation(plan, eligible, rule_evaluations)
        suggestions = self._generate_suggestions(plan, eligible, rule_evaluations)
        
        return ExplainableResult(
            plan_tag=plan["plan_tag"],
            batch_code=plan.get("batch_code", ""),
            eligible=eligible,
            rule_evaluations=rule_evaluations,
            total_rules=total_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            summary=summary,
            detailed_explanation=detailed_explanation,
            suggestions=suggestions,
            reasons_hit=hit,
            reasons_miss=miss
        )
    
    # ============ 可解释性辅助方法 ============
    
    def _get_hukou_rule_clause(self, mode: str) -> str:
        """获取户籍规则条文"""
        clauses = {
            "any": "不区分农村/城市户籍",
            "rural_only": "须为农村户籍",
        }
        return clauses.get(mode, mode)
    
    def _format_hukou_required(self, mode: str) -> str:
        """格式化户籍要求"""
        if mode == "any":
            return "农村或城市户籍均可"
        elif mode == "rural_only":
            return "农村户籍"
        return mode
    
    def _format_hukou_actual(self, nature: Optional[str]) -> str:
        """格式化实际户籍"""
        if nature == "rural_only":
            return "农村户籍"
        elif nature == "urban":
            return "城市户籍"
        return nature or "未填写"
    
    def _get_region_rule_clause(self, scope: Optional[str]) -> str:
        """获取地区规则条文"""
        clauses = {
            None: "无特定区域限制",
            "gansu_rural_all": "甘肃省农村区域",
            "gansu_58_poverty_counties": "甘肃省原58个集中连片贫困县",
            "gansu_58_plus_3": "甘肃省58个贫困县+3个少数民族自治县",
            "gansu_revolutionary_areas": "革命老区（庆阳市、平凉市全境+会宁县）",
            "gansu_two_states_one_county": "两州一县（甘南州、临夏州、天祝县）",
            "gansu_tibetan_area": "藏区（甘南州、天祝县）",
            "gansu_other_ethnic_areas": "其他民族地区",
            "gansu_local_target_area": "省属定向培养指定区域",
            "gansu_city_target_area": "市级定向培养指定区域",
        }
        return clauses.get(scope, scope or "无限制")
    
    def _format_region_required(self, scope: Optional[str]) -> str:
        """格式化地区要求"""
        return self._get_region_rule_clause(scope)
    
    def _format_region_actual(self, profile: UserProfile, fields: List[str]) -> str:
        """格式化实际地区"""
        parts = []
        if "region" in fields:
            parts.append(f"户籍：{profile.region or '未填写'}")
        if "school_region" in fields:
            parts.append(f"学籍：{profile.school_region or '未填写'}")
        if "parent_region" in fields:
            parts.append(f"监护人户籍：{profile.parent_region or '未填写'}")
        return "，".join(parts) if parts else "未要求"
    
    def _get_three_uni_clause(self, required: bool, years: int) -> str:
        """获取三年统一规则条文"""
        if not required:
            return "无三年统一要求"
        return f"考生本人及监护人须具有实施区域连续{years}年以上户籍，考生具有{years}年学籍并实际就读"
    
    def _get_three_uni_failure_reason(self, profile: UserProfile, need_years: int) -> str:
        """获取三年统一失败原因"""
        reasons = []
        if profile.hukou_years < need_years:
            reasons.append(f"户籍年限不足（需{need_years}年，实际{profile.hukou_years}年）")
        if profile.school_years < need_years:
            reasons.append(f"学籍年限不足（需{need_years}年，实际{profile.school_years}年）")
        if profile.parent_hukou_years < need_years:
            reasons.append(f"监护人户籍年限不足（需{need_years}年，实际{profile.parent_hukou_years}年）")
        return "；".join(reasons) if reasons else "不满足三年统一要求"
    
    def _get_nation_rule_clause(self, lock: str) -> str:
        """获取民族规则条文"""
        clauses = {
            "none": "不限制民族成分",
            "minority_only": "须为少数民族",
            "tibetan_only": "须为藏族",
            "conditional_default_minority": "少数民族优先（70%名额），汉族也可报考（30%名额）",
        }
        return clauses.get(lock, lock)
    
    def _format_nation_required(self, lock: str) -> str:
        """格式化民族要求"""
        return self._get_nation_rule_clause(lock)
    
    def _get_nation_failure_reason(self, lock: str, nation: Optional[str]) -> str:
        """获取民族失败原因"""
        if lock == "minority_only":
            return f"考生为{nation or '未填写'}，非少数民族，不满足少数民族要求"
        elif lock == "tibetan_only":
            return f"考生为{nation or '未填写'}，非藏族，不满足藏族要求"
        return "不满足民族要求"
    
    def _get_identity_rule_clause(self, identity: Optional[str]) -> str:
        """获取身份规则条文"""
        if not identity:
            return "无特殊身份要求"
        clauses = {
            "strong_foundation_candidate": "须为强基计划候选人（综合素质优秀或基础学科拔尖）",
            "comprehensive_evaluation_candidate": "须通过综合评价初审",
            "border_military_child": "须为经中央军委政治工作部审核确认的边防军人子女",
        }
        return clauses.get(identity, f"须为{identity}")
    
    def _format_identity_required(self, identity: Optional[str]) -> str:
        """格式化身份要求"""
        if not identity:
            return "无特殊要求"
        clauses = {
            "strong_foundation_candidate": "强基计划候选人",
            "comprehensive_evaluation_candidate": "综合评价候选人",
            "border_military_child": "边防军人子女",
        }
        return clauses.get(identity, identity)
    
    def _get_subject_rule_clause(self, required: Optional[str]) -> str:
        """获取选科规则条文"""
        if not required:
            return "无硬性选科限制"
        clauses = {
            "PHYSICS & CHEMISTRY": "必须选考物理和化学",
            "PHYSICS & CHEMISTRY | HISTORY": "必须选考物理+化学，或选考历史（分文理科）",
        }
        return clauses.get(required, f"须满足：{required}")
    
    def _format_subject_required(self, required: Optional[str]) -> str:
        """格式化选科要求"""
        return self._get_subject_rule_clause(required)
    
    def _generate_summary(self, plan_tag: str, eligible: bool) -> str:
        """生成一句话摘要"""
        if eligible:
            return f"✅ 具备{plan_tag}报考资格"
        else:
            return f"❌ 不具备{plan_tag}报考资格"
    
    def _generate_detailed_explanation(self, plan: Dict[str, Any], eligible: bool, 
                                       evaluations: List[RuleEvaluationDetail]) -> str:
        """生成详细解释"""
        lines = []
        plan_tag = plan["plan_tag"]
        batch_code = plan.get("batch_code", "")
        
        lines.append(f"【{plan_tag}】资格审核详情")
        if batch_code:
            lines.append(f"录取批次：{batch_code}")
        lines.append("")
        
        if eligible:
            lines.append("✅ 审核结果：具备报考资格")
            lines.append("您满足该专项计划的所有报考条件，可以正常填报志愿。")
        else:
            lines.append("❌ 审核结果：不具备报考资格")
            lines.append("您不满足以下报考条件，无法填报该专项计划：")
            lines.append("")
            for ev in evaluations:
                if not ev.passed:
                    lines.append(f"  • {ev.rule_name}：{ev.failure_reason}")
        
        lines.append("")
        lines.append("详细判定链路：")
        for ev in evaluations:
            status = "✅" if ev.passed else "❌"
            lines.append(f"  {status} {ev.rule_name}")
            lines.append(f"     规则：{ev.rule_clause}")
            lines.append(f"     要求：{ev.required_value}")
            lines.append(f"     实际：{ev.actual_value}")
            if ev.failure_reason:
                lines.append(f"     原因：{ev.failure_reason}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_suggestions(self, plan: Dict[str, Any], eligible: bool,
                              evaluations: List[RuleEvaluationDetail]) -> List[str]:
        """生成建议"""
        suggestions = []
        plan_tag = plan["plan_tag"]
        
        if eligible:
            suggestions.append(f"您具备{plan_tag}报考资格，建议在志愿填报时优先考虑该计划。")
            score_logic = plan.get("rules", {}).get("score_logic", "")
            if "line_offset" in score_logic:
                suggestions.append("该计划有降分录取优惠，可适当冲高填报。")
        else:
            suggestions.append(f"您当前不具备{plan_tag}报考资格，建议关注以下方面：")
            
            for ev in evaluations:
                if not ev.passed:
                    if ev.rule_name == "户籍性质检查":
                        suggestions.append("• 户籍性质不符：如户籍有变更记录，请咨询当地招办。")
                    elif ev.rule_name == "地区范围检查":
                        suggestions.append("• 地区范围不符：请确认您的户籍/学籍是否在实施区域内。")
                    elif ev.rule_name == "三年统一检查":
                        suggestions.append("• 三年统一不满足：请核实户籍、学籍年限是否满3年，截止时间为高考当年8月31日。")
                    elif ev.rule_name == "民族成分检查":
                        suggestions.append("• 民族成分不符：该计划仅限特定民族报考。")
                    elif ev.rule_name == "专项审核检查":
                        suggestions.append("• 未通过专项审核：请关注次年4月的报名审核通知。")
                    elif ev.rule_name == "诚信记录检查":
                        suggestions.append("• 诚信记录限制：往年放弃专项计划录取的考生，不再具有报考资格。")
        
        return suggestions

    def _match_hukou(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        mode = rules.get("hukou_nature", "any")
        if mode == "any":
            return True
        return profile.hukou_nature == mode

    def _match_region(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        scope = rules.get("region_scope")
        fields = rules.get("region_compare_fields", [])
        if not scope or scope == "gansu_rural_all":
            return True
        region_list = set(self.region_dict.get(scope, []))
        values = [getattr(profile, field, None) for field in fields]
        values = [value for value in values if value]
        if not values:
            return False
        return all(value in region_list for value in values)

    def _match_three_unification(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("three_unification_required", False):
            return True
        need_years = int(rules.get("residence_years", 3))
        return (
            profile.school_years >= need_years
            and profile.hukou_years >= need_years
            and profile.parent_hukou_years >= need_years
        )

    def _match_guardian_region(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("guardian_region_required", False):
            return True
        return bool(profile.parent_has_local_hukou and profile.parent_region)

    def _match_schooling(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("actual_schooling_required", False):
            return True
        return bool(profile.graduated_in_region_school)

    def _match_nation(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        lock = rules.get("nation_lock", "none")
        if lock == "none":
            return True
        if lock == "minority_only":
            return profile.nation not in {None, "", "汉族"}
        if lock == "conditional_default_minority":
            # 两州一县等专项：默认少数民族优先（70%名额），但汉族也可报考（30%名额不区分民族）
            # 因此汉族考生也应判定为符合条件，只是优先级较低
            return True
        if lock == "tibetan_only":
            return profile.nation == "藏族"
        return True

    def _match_special_review(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("special_review_pass_required", False):
            return True
        return bool(profile.special_review_passed)

    def _match_special_identity(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        expected = rules.get("special_identity_required")
        if not expected:
            return True
        return profile.special_identity == expected

    def _match_registered_family(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("registered_poverty_family_required", False):
            return True
        return bool(profile.is_registered_poverty_family)

    def _match_ethnic_language(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("ethnic_language_score_required", False):
            return True
        return bool(profile.has_ethnic_language_score)

    def _match_previous_breach(self, rules: Dict[str, Any], profile: UserProfile) -> bool:
        if not rules.get("previous_special_plan_breach_forbidden", False):
            return True
        return not profile.previous_special_plan_breach

    def _match_subjects(self, required_subjects: str | None, profile: UserProfile) -> bool:
        if not required_subjects:
            return True
        normalized = list(normalize_subjects([profile.track, *profile.selected_subjects]))
        if required_subjects == "PHYSICS & CHEMISTRY | HISTORY":
            return subject_expression_match("PHYSICS & CHEMISTRY", normalized) or subject_expression_match("HISTORY", normalized)
        return subject_expression_match(required_subjects, normalized)


def recommend_for_frontend(engine: PolicyEngine, profile: UserProfile) -> Dict[str, Any]:
    """
    为前端推荐系统提供可解释的资格判定结果
    
    返回包含详细判定链路的JSON格式数据，供前端展示"为什么通过/为什么被阻"
    """
    explainable_results = engine.evaluate_all_explainable(profile)
    
    eligible_plans = []
    ineligible_plans = []
    
    for result in explainable_results:
        plan_data = {
            "plan_tag": result.plan_tag,
            "batch_code": result.batch_code,
            "eligible": result.eligible,
            "summary": result.summary,
            "statistics": {
                "total_rules": result.total_rules,
                "passed_rules": result.passed_rules,
                "failed_rules": result.failed_rules,
                "pass_rate": f"{result.passed_rules / result.total_rules * 100:.1f}%" if result.total_rules > 0 else "0%"
            },
            "rule_evaluations": [
                {
                    "rule_name": ev.rule_name,
                    "rule_clause": ev.rule_clause,
                    "required_value": ev.required_value,
                    "actual_value": ev.actual_value,
                    "passed": ev.passed,
                    "failure_reason": ev.failure_reason
                }
                for ev in result.rule_evaluations
            ],
            "suggestions": result.suggestions,
            "detailed_explanation": result.detailed_explanation
        }
        
        if result.eligible:
            eligible_plans.append(plan_data)
        else:
            ineligible_plans.append(plan_data)
    
    return {
        "profile_summary": {
            "region": profile.region,
            "hukou_nature": profile.hukou_nature,
            "nation": profile.nation,
            "school_region": profile.school_region,
            "track": profile.track,
            "selected_subjects": profile.selected_subjects
        },
        "eligibility_summary": {
            "total_plans": len(explainable_results),
            "eligible_count": len(eligible_plans),
            "ineligible_count": len(ineligible_plans)
        },
        "eligible_plans": eligible_plans,
        "ineligible_plans": ineligible_plans,
        "recommendations": _generate_recommendations(eligible_plans, ineligible_plans)
    }


def summarize_policy_eligibility(engine: PolicyEngine, profile: UserProfile) -> Dict[str, Any]:
    """
    汇总考生的专项计划资格情况
    
    提供简洁的汇总视图，适合快速查看
    """
    results = engine.evaluate_all_explainable(profile)
    
    summary = {
        "fully_eligible": [],  # 完全具备资格
        "partially_eligible": [],  # 部分条件满足（可用于提示）
        "not_eligible": []  # 不具备资格
    }
    
    for result in results:
        plan_info = {
            "plan_tag": result.plan_tag,
            "batch_code": result.batch_code,
            "summary": result.summary
        }
        
        if result.eligible:
            summary["fully_eligible"].append(plan_info)
        elif result.passed_rules > 0:
            # 部分规则通过，可能有价值作为提示
            plan_info["passed_rules"] = result.passed_rules
            plan_info["failed_rules"] = result.failed_rules
            plan_info["key_failures"] = [
                ev.rule_name for ev in result.rule_evaluations if not ev.passed
            ]
            summary["partially_eligible"].append(plan_info)
        else:
            summary["not_eligible"].append(plan_info)
    
    return {
        "summary": summary,
        "priority_recommendation": _get_priority_recommendation(summary),
        "action_items": _generate_action_items(results)
    }


def _generate_recommendations(eligible: List[Dict], ineligible: List[Dict]) -> List[str]:
    """生成整体推荐建议"""
    recommendations = []
    
    if eligible:
        recommendations.append(f"您具备 {len(eligible)} 个专项计划的报考资格，建议优先考虑以下计划：")
        for plan in eligible[:3]:  # 最多显示3个
            recommendations.append(f"  • {plan['plan_tag']}（{plan['batch_code']}）")
    
    if ineligible:
        # 检查是否有接近满足条件的
        close_calls = [p for p in ineligible if p["statistics"]["passed_rules"] >= p["statistics"]["total_rules"] - 1]
        if close_calls:
            recommendations.append("\n以下计划您接近满足条件，可关注相关政策变化：")
            for plan in close_calls[:2]:
                failed = [ev for ev in plan["rule_evaluations"] if not ev["passed"]]
                if failed:
                    recommendations.append(f"  • {plan['plan_tag']}：{failed[0]['failure_reason']}")
    
    return recommendations


def _get_priority_recommendation(summary: Dict[str, List]) -> str:
    """获取优先推荐"""
    if summary["fully_eligible"]:
        top = summary["fully_eligible"][0]
        return f"优先推荐：{top['plan_tag']}（{top['batch_code']}）"
    return "暂无可推荐的专项计划"


def _generate_action_items(results: List[ExplainableResult]) -> List[str]:
    """生成行动建议"""
    actions = []
    
    for result in results:
        if not result.eligible:
            for ev in result.rule_evaluations:
                if not ev.passed:
                    if ev.rule_name == "三年统一检查" and "户籍年限不足" in (ev.failure_reason or ""):
                        actions.append(f"{result.plan_tag}：户籍年限不足，如户籍即将满3年，请关注次年报考")
                    elif ev.rule_name == "专项审核检查":
                        actions.append(f"{result.plan_tag}：需提前参加高校审核，请关注4月报名通知")
    
    return actions
