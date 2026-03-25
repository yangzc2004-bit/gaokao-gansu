from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


RiskBucket = Literal["冲", "稳", "保"]


@dataclass
class RankThreshold:
    challenge_lower: float = 0.55
    challenge_upper: float = 1.00
    stable_upper: float = 1.20
    safe_upper: float = 1.80


def classify_bucket(candidate_rank: float, user_rank: float, threshold: RankThreshold | None = None) -> RiskBucket | None:
    threshold = threshold or RankThreshold()
    ratio = candidate_rank / user_rank if user_rank else 999

    if ratio < threshold.challenge_lower:
        return None
    if ratio <= threshold.challenge_upper:
        return "冲"
    if ratio <= threshold.stable_upper:
        return "稳"
    if ratio <= threshold.safe_upper:
        return "保"
    return None


def compute_rank_cv(series: pd.Series) -> float:
    valid = series.dropna().astype(float)
    if len(valid) < 2 or valid.mean() == 0:
        return 0.0
    return float(valid.std(ddof=0) / valid.mean())
