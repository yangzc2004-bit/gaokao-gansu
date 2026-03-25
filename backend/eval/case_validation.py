from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.models.schemas import UserProfile
from backend.recommend.engine import recommend_for_frontend


ROOT = Path(__file__).resolve().parents[2]
RECORDS_PATH = ROOT / "data/processed/admission_records.csv"
METRICS_PATH = ROOT / "data/processed/admission_metrics_long.csv"
RULES_PATH = ROOT / "configs/policy_rules.gansu.json"
REGION_PATH = ROOT / "configs/region_dict.gansu.json"
REPORT_JSON_PATH = ROOT / "data/processed/case_validation_report.json"
REPORT_MD_PATH = ROOT / "docs/case-validation-report.md"


CASES = [
    {
        "name": "历史-5000",
        "goal": "冲刺型考生",
        "profile": UserProfile(track="历史", selected_subjects=["政治", "地理"], score=560, rank=5000, region="会宁县"),
    },
    {
        "name": "物理-15000",
        "goal": "中间稳妥型考生",
        "profile": UserProfile(track="物理", selected_subjects=["化学", "生物"], score=500, rank=15000, region="兰州市"),
    },
    {
        "name": "历史-12000",
        "goal": "保底敏感型考生",
        "profile": UserProfile(track="历史", selected_subjects=["政治", "地理"], score=500, rank=12000, region="天水市"),
    },
]


def summarize_top_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None

    score = item.get("score", {})
    history = item.get("history", {})
    return {
        "school_name": item.get("school_name"),
        "major_name": item.get("major_name"),
        "risk_level": item.get("risk_level"),
        "admission_probability": score.get("admission_probability"),
        "rank_cv": score.get("rank_cv"),
        "years_available": history.get("years_available"),
        "history_penalty": history.get("history_penalty"),
        "recommend_reason": item.get("recommend_reason"),
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    result = recommend_for_frontend(
        str(RECORDS_PATH),
        str(METRICS_PATH),
        str(RULES_PATH),
        str(REGION_PATH),
        case["profile"],
    )
    return {
        "name": case["name"],
        "goal": case["goal"],
        "query": result.get("query", {}),
        "counts": result.get("summary", {}).get("counts", {}),
        "top_recommendations": {
            bucket: summarize_top_item((result.get("results", {}).get(bucket) or [None])[0])
            for bucket in ["冲", "稳", "保", "政策红利"]
        },
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# 典型案例联调报告", "", "本报告由 `backend/eval/case_validation.py` 自动生成。", ""]
    for result in results:
        lines.append(f"## {result['name']}（{result['goal']}）")
        query = result["query"]
        lines.append(
            f"- 输入：{query.get('track')} / {'、'.join(query.get('selected_subjects', []))} / 分数 {query.get('score')} / 位次 {query.get('rank')} / 地区 {query.get('region')}"
        )
        counts = result["counts"]
        lines.append(
            f"- 结果数量：冲 {counts.get('冲', 0)} / 稳 {counts.get('稳', 0)} / 保 {counts.get('保', 0)} / 政策红利 {counts.get('政策红利', 0)}"
        )
        for bucket in ["冲", "稳", "保"]:
            item = result["top_recommendations"].get(bucket)
            if not item:
                lines.append(f"- {bucket}：无结果")
                continue
            lines.append(
                f"- {bucket} Top1：{item.get('school_name')} · {item.get('major_name')}｜概率 {item.get('admission_probability', 0):.2%}｜CV {item.get('rank_cv', 0):.4f}｜历史年数 {item.get('years_available')}｜惩罚 {item.get('history_penalty')}"
            )
            lines.append(f"- {bucket} 理由：{item.get('recommend_reason')}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    results = [run_case(case) for case in CASES]
    REPORT_JSON_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(results), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON_PATH), "markdown": str(REPORT_MD_PATH)}, ensure_ascii=False))
