from __future__ import annotations

from typing import Iterable


HIGH_BONUS_PLANS = {
    "国家专项": 12,
    "高校专项": 16,
    "地方专项": 10,
    "革命老区专项": 10,
    "两州一县专项": 15,
    "省属免费医学生": 11,
    "省属公费师范生": 9,
}


def score_policy_bonus(plan_tags: Iterable[str], rank_cv: float, school_level: str | None) -> float:
    bonus = sum(HIGH_BONUS_PLANS.get(tag, 0) for tag in plan_tags)

    if rank_cv <= 0.03:
        bonus += 6
    elif rank_cv <= 0.06:
        bonus += 3

    level_text = "" if school_level is None else str(school_level)
    if any(token in level_text for token in ["985", "211", "双一流"]):
        bonus += 5
    elif any(token in level_text for token in ["省重点", "保研资格"]):
        bonus += 2

    return float(bonus)
