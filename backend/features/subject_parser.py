from __future__ import annotations

import re
from typing import Iterable


SUBJECT_MAP = {
    "物理": "PHYSICS",
    "历史": "HISTORY",
    "化学": "CHEMISTRY",
    "生物": "BIOLOGY",
    "地理": "GEOGRAPHY",
    "政治": "POLITICS",
    "思想政治": "POLITICS",
}


RELAXED_PATTERNS = {"不限", "无", "依招生专业确定", "依专业确定", "详见招生章程", "详见学校要求"}


def normalize_subjects(subjects: Iterable[str]) -> set[str]:
    return {SUBJECT_MAP.get(subject, subject) for subject in subjects if subject}


def _normalize_expression(expression: str) -> str:
    expr = expression.strip()
    expr = expr.replace("（", "(").replace("）", ")")
    expr = expr.replace("思想政治", "政治")
    expr = expr.replace("和", "&")
    expr = expr.replace("且", "&")
    expr = expr.replace("并且", "&")
    expr = expr.replace("或", "|")
    expr = expr.replace("/", "|")
    expr = expr.replace("、", "|")
    expr = expr.replace("，", "|")
    expr = expr.replace(",", "|")
    expr = re.sub(r"\s+", "", expr)
    return expr


def _normalize_token(token: str) -> str:
    return SUBJECT_MAP.get(token, token)


def subject_expression_match(required_expression: str | None, selected_subjects: Iterable[str]) -> bool:
    if not required_expression:
        return True

    normalized = normalize_subjects(selected_subjects)
    expression = _normalize_expression(str(required_expression))

    if not expression or expression in RELAXED_PATTERNS:
        return True

    if expression in {"物理&化学|历史", "PHYSICS&CHEMISTRY|HISTORY"}:
        return ({"PHYSICS", "CHEMISTRY"}.issubset(normalized)) or ("HISTORY" in normalized)

    if "|" in expression:
        optional_groups = [group for group in expression.split("|") if group]
        for group in optional_groups:
            if "&" in group:
                required = {_normalize_token(item) for item in group.split("&") if item}
                if required.issubset(normalized):
                    return True
            else:
                if _normalize_token(group) in normalized:
                    return True
        return False

    if "&" in expression:
        required = {_normalize_token(item) for item in expression.split("&") if item}
        return required.issubset(normalized)

    return _normalize_token(expression) in normalized
