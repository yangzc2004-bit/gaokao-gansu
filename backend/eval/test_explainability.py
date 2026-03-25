"""
可解释性功能测试脚本
验证 ExplainableResult 和 RuleEvaluationDetail 功能
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.models.schemas import UserProfile
from backend.rules.eligibility import PolicyEngine, recommend_for_frontend, summarize_policy_eligibility


# 配置文件路径
RULES_PATH = ROOT / "configs/policy_rules.gansu.json"
REGION_PATH = ROOT / "configs/region_dict.gansu.json"


def test_explainable_result():
    """测试可解释结果功能"""
    print("=" * 60)
    print("可解释性功能测试")
    print("=" * 60)
    
    engine = PolicyEngine(str(RULES_PATH), str(REGION_PATH))
    
    # 测试用例1：完全符合条件的考生（国家专项）
    print("\n【测试用例1】完全符合条件的考生")
    profile1 = UserProfile(
        track="物理",
        selected_subjects=["化学", "生物"],
        region="会宁县",
        hukou_nature="rural_only",
        nation="汉族",
        school_region="会宁县",
        parent_region="会宁县",
        school_years=3,
        hukou_years=3,
        parent_hukou_years=3,
        is_registered_poverty_family=False,
        has_ethnic_language_score=False,
        special_identity=None,
        graduated_in_region_school=True,
        parent_has_local_hukou=True,
        previous_special_plan_breach=False,
        special_review_passed=False,
    )
    
    result1 = engine.evaluate_plan_explainable(
        next(p for p in engine.rules["plans"] if p["plan_tag"] == "国家专项"),
        profile1
    )
    
    print(f"计划：{result1.plan_tag}")
    print(f"资格：{'✅ 具备' if result1.eligible else '❌ 不具备'}")
    print(f"摘要：{result1.summary}")
    print(f"规则统计：通过 {result1.passed_rules}/{result1.total_rules}")
    print("\n判定链路：")
    for ev in result1.rule_evaluations[:3]:  # 只显示前3条
        status = "✅" if ev.passed else "❌"
        print(f"  {status} {ev.rule_name}: {ev.actual_value}")
    
    assert result1.eligible == True, "完全符合条件的考生应该具备资格"
    assert result1.passed_rules == result1.total_rules, "所有规则应该通过"
    print("  ✅ 测试通过")
    
    # 测试用例2：户籍年限不足的考生
    print("\n【测试用例2】户籍年限不足的考生")
    profile2 = UserProfile(
        track="物理",
        selected_subjects=["化学", "生物"],
        region="会宁县",
        hukou_nature="rural_only",
        nation="汉族",
        school_region="会宁县",
        parent_region="会宁县",
        school_years=3,
        hukou_years=2,  # 不足3年
        parent_hukou_years=3,
        is_registered_poverty_family=False,
        has_ethnic_language_score=False,
        special_identity=None,
        graduated_in_region_school=True,
        parent_has_local_hukou=True,
        previous_special_plan_breach=False,
        special_review_passed=False,
    )
    
    result2 = engine.evaluate_plan_explainable(
        next(p for p in engine.rules["plans"] if p["plan_tag"] == "国家专项"),
        profile2
    )
    
    print(f"计划：{result2.plan_tag}")
    print(f"资格：{'✅ 具备' if result2.eligible else '❌ 不具备'}")
    print(f"摘要：{result2.summary}")
    print(f"规则统计：通过 {result2.passed_rules}/{result2.total_rules}")
    print("\n失败规则详情：")
    for ev in result2.rule_evaluations:
        if not ev.passed:
            print(f"  ❌ {ev.rule_name}")
            print(f"     规则：{ev.rule_clause}")
            print(f"     原因：{ev.failure_reason}")
    
    assert result2.eligible == False, "户籍年限不足的考生不应该具备资格"
    assert result2.failed_rules > 0, "应该有失败的规则"
    print("  ✅ 测试通过")
    
    # 测试用例3：城市户籍报考地方专项（户籍性质不符）
    print("\n【测试用例3】城市户籍报考地方专项")
    profile3 = UserProfile(
        track="历史",
        selected_subjects=["政治", "地理"],
        region="会宁县",
        hukou_nature="urban",  # 城市户籍
        nation="汉族",
        school_region="会宁县",
        parent_region="会宁县",
        school_years=3,
        hukou_years=3,
        parent_hukou_years=3,
        is_registered_poverty_family=False,
        has_ethnic_language_score=False,
        special_identity=None,
        graduated_in_region_school=True,
        parent_has_local_hukou=True,
        previous_special_plan_breach=False,
        special_review_passed=False,
    )
    
    result3 = engine.evaluate_plan_explainable(
        next(p for p in engine.rules["plans"] if p["plan_tag"] == "地方专项"),
        profile3
    )
    
    print(f"计划：{result3.plan_tag}")
    print(f"资格：{'✅ 具备' if result3.eligible else '❌ 不具备'}")
    print(f"摘要：{result3.summary}")
    
    hukou_check = next((ev for ev in result3.rule_evaluations if ev.rule_name == "户籍性质检查"), None)
    if hukou_check:
        print(f"\n户籍检查详情：")
        print(f"  要求：{hukou_check.required_value}")
        print(f"  实际：{hukou_check.actual_value}")
        print(f"  原因：{hukou_check.failure_reason}")
    
    assert result3.eligible == False, "城市户籍考生不应该具备地方专项资格"
    print("  ✅ 测试通过")
    
    # 测试用例4：recommend_for_frontend 接口
    print("\n【测试用例4】前端推荐接口")
    recommendation = recommend_for_frontend(engine, profile1)
    
    print(f"考生概况：")
    print(f"  户籍：{recommendation['profile_summary']['region']}")
    print(f"  科类：{recommendation['profile_summary']['track']}")
    print(f"\n资格汇总：")
    print(f"  具备资格：{recommendation['eligibility_summary']['eligible_count']} 个计划")
    print(f"  不具备资格：{recommendation['eligibility_summary']['ineligible_count']} 个计划")
    
    if recommendation['eligible_plans']:
        print(f"\n可报考计划（前3个）：")
        for plan in recommendation['eligible_plans'][:3]:
            print(f"  • {plan['plan_tag']}（{plan['batch_code']}）- {plan['statistics']['pass_rate']}")
    
    assert 'eligible_plans' in recommendation
    assert 'ineligible_plans' in recommendation
    print("  ✅ 测试通过")
    
    # 测试用例5：summarize_policy_eligibility 接口
    print("\n【测试用例5】资格汇总接口")
    summary = summarize_policy_eligibility(engine, profile1)
    
    print(f"资格分类：")
    print(f"  完全具备：{len(summary['summary']['fully_eligible'])} 个")
    print(f"  部分具备：{len(summary['summary']['partially_eligible'])} 个")
    print(f"  不具备：{len(summary['summary']['not_eligible'])} 个")
    print(f"\n优先推荐：{summary['priority_recommendation']}")
    
    if summary['action_items']:
        print(f"\n行动建议：")
        for item in summary['action_items'][:3]:
            print(f"  • {item}")
    
    assert 'summary' in summary
    assert 'priority_recommendation' in summary
    print("  ✅ 测试通过")
    
    print("\n" + "=" * 60)
    print("所有可解释性功能测试通过！")
    print("=" * 60)
    
    return True


def test_json_output():
    """测试JSON输出格式"""
    print("\n" + "=" * 60)
    print("JSON输出格式测试")
    print("=" * 60)
    
    engine = PolicyEngine(str(RULES_PATH), str(REGION_PATH))
    
    profile = UserProfile(
        track="物理",
        selected_subjects=["化学", "生物"],
        region="会宁县",
        hukou_nature="rural_only",
        nation="汉族",
        school_region="会宁县",
        parent_region="会宁县",
        school_years=3,
        hukou_years=3,
        parent_hukou_years=3,
        is_registered_poverty_family=False,
        has_ethnic_language_score=False,
        special_identity=None,
        graduated_in_region_school=True,
        parent_has_local_hukou=True,
        previous_special_plan_breach=False,
        special_review_passed=False,
    )
    
    recommendation = recommend_for_frontend(engine, profile)
    
    # 验证JSON可序列化
    try:
        json_str = json.dumps(recommendation, ensure_ascii=False, indent=2)
        print(f"JSON序列化成功，长度：{len(json_str)} 字符")
        
        # 保存示例输出
        output_path = ROOT / "data/processed/explainability_example.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str, encoding="utf-8")
        print(f"示例输出已保存到：{output_path}")
        
        # 验证JSON结构
        assert "profile_summary" in recommendation
        assert "eligibility_summary" in recommendation
        assert "eligible_plans" in recommendation
        assert "ineligible_plans" in recommendation
        
        # 验证eligible_plans结构
        if recommendation["eligible_plans"]:
            plan = recommendation["eligible_plans"][0]
            assert "plan_tag" in plan
            assert "batch_code" in plan
            assert "eligible" in plan
            assert "summary" in plan
            assert "statistics" in plan
            assert "rule_evaluations" in plan
            assert "suggestions" in plan
            
            # 验证rule_evaluations结构
            if plan["rule_evaluations"]:
                ev = plan["rule_evaluations"][0]
                assert "rule_name" in ev
                assert "rule_clause" in ev
                assert "required_value" in ev
                assert "actual_value" in ev
                assert "passed" in ev
        
        print("  ✅ JSON结构验证通过")
        
    except Exception as e:
        print(f"  ❌ JSON序列化失败：{e}")
        return False
    
    print("\n" + "=" * 60)
    print("JSON输出格式测试通过！")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("资格判定可解释性功能测试套件")
    print("=" * 60)
    
    try:
        test_explainable_result()
        test_json_output()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\nT2.6 可解释化功能验证完成")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试断言失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试执行异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
