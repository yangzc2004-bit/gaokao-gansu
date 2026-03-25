from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ProbabilityConfig:
    min_sigma_ratio: float = 0.06
    base_sigma_ratio: float = 0.10
    cv_sigma_weight: float = 0.90
    one_year_penalty: float = 0.72
    two_year_penalty: float = 0.88
    low_history_cap: float = 0.78


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _safe_float(value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def estimate_admission_probability(
    user_rank: float,
    target_rank: float | None,
    rank_cv: float | None,
    years_available: int,
    min_rank: float | None,
    avg_rank: float | None,
    max_rank: float | None,
) -> float:
    if not user_rank or user_rank <= 0:
        return 0.0

    min_rank = _safe_float(min_rank)
    avg_rank = _safe_float(avg_rank)
    max_rank = _safe_float(max_rank)
    target_rank = _safe_float(target_rank) or avg_rank or min_rank or max_rank
    if not target_rank or target_rank <= 0:
        return 0.0

    cv = 0.0 if rank_cv is None or (isinstance(rank_cv, float) and math.isnan(rank_cv)) else max(0.0, float(rank_cv))
    sigma_ratio = max(0.06, 0.10 + cv * 0.90)

    if years_available >= 3 and min_rank is not None and max_rank is not None:
        spread = abs(max_rank - min_rank)
        sigma = max(target_rank * sigma_ratio, spread / 1.35, 1.0)
    elif years_available == 2:
        known_values = [value for value in [min_rank, avg_rank, max_rank] if value is not None]
        spread = max(known_values) - min(known_values) if len(known_values) >= 2 else target_rank * sigma_ratio
        sigma = max(target_rank * (sigma_ratio * 1.15), spread / 1.2, 1.0)
    else:
        sigma = max(target_rank * max(0.18, sigma_ratio * 1.6), 1.0)

    z_score = (target_rank - user_rank) / sigma
    probability = normal_cdf(z_score)

    config = ProbabilityConfig()
    if years_available == 1:
        probability *= config.one_year_penalty
        probability = min(probability, config.low_history_cap)
    elif years_available == 2:
        probability *= config.two_year_penalty

    return max(0.0, min(1.0, probability))


def derive_target_rank(
    years_available: int,
    latest_min_rank: float | None,
    latest_avg_rank: float | None,
    latest_max_rank: float | None,
    min_rank_3y: float | None,
    avg_rank_3y: float | None,
    max_rank_3y: float | None,
    plan_count: float | None,
    group_plan_count: float | None,
    is_new_major: object | None,
) -> float | None:
    latest_min_rank = _safe_float(latest_min_rank)
    latest_avg_rank = _safe_float(latest_avg_rank)
    latest_max_rank = _safe_float(latest_max_rank)
    min_rank_3y = _safe_float(min_rank_3y)
    avg_rank_3y = _safe_float(avg_rank_3y)
    max_rank_3y = _safe_float(max_rank_3y)

    target: float | None = None

    if years_available >= 3:
        weighted = []
        if latest_min_rank is not None:
            weighted.append(latest_min_rank * 0.20)
        if latest_avg_rank is not None:
            weighted.append(latest_avg_rank * 0.35)
        if avg_rank_3y is not None:
            weighted.append(avg_rank_3y * 0.35)
        if min_rank_3y is not None:
            weighted.append(min_rank_3y * 0.10)
        target = sum(weighted) if weighted else None
    elif years_available == 2:
        weighted = []
        if latest_avg_rank is not None:
            weighted.append(latest_avg_rank * 0.45)
        if avg_rank_3y is not None:
            weighted.append(avg_rank_3y * 0.35)
        if latest_min_rank is not None:
            weighted.append(latest_min_rank * 0.20)
        target = sum(weighted) if weighted else None
    elif years_available == 1:
        target = latest_avg_rank or latest_min_rank or latest_max_rank

    if target is None:
        return None

    plan_count = _safe_float(plan_count)
    group_plan_count = _safe_float(group_plan_count)
    ratio = None
    if plan_count is not None and group_plan_count is not None and group_plan_count > 0:
        ratio = plan_count / group_plan_count

    if ratio is not None and ratio <= 0.08:
        target *= 0.95
    elif ratio is not None and ratio <= 0.15:
        target *= 0.97
    elif ratio is not None and ratio >= 0.35:
        target *= 1.02

    if isinstance(is_new_major, str) and is_new_major.strip() == "新增":
        target *= 0.96

    return target


def probability_label(probability: float) -> str:
    if probability >= 0.8:
        return "高"
    if probability >= 0.5:
        return "中"
    if probability >= 0.2:
        return "低"
    return "极低"
