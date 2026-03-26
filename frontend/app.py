import html
import json
import math
import re
import sys
import textwrap
from dataclasses import asdict
from pathlib import Path

# Ensure project root is in sys.path (needed for Streamlit Cloud)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from backend.features.plan_metadata import (
    PLAN_BY_TAG,
    PLAN_GROUP_BATCH,
    PLAN_GROUP_ORDER,
    PLAN_GROUPS,
    SUBTAG_TO_GROUP,
    infer_plan_groups_from_text,
    normalize_plan_text,
)
from backend.models.schemas import UserProfile
from backend.features.subject_parser import normalize_subjects, subject_expression_match
from backend.recommend.engine import recommend_for_frontend
from backend.rules.eligibility import PolicyEngine


st.set_page_config(page_title="甘肃高考志愿推荐系统", layout="wide")

RISK_META = {
    "冲": {
        "emoji": "🔥",
        "label": "冲刺",
        "hint": "有机会，但波动更大，适合少量布局",
        "main": "#F3A04C",
        "soft": "rgba(243,160,76,0.14)",
        "surface": "#FFF4E8",
    },
    "稳": {
        "emoji": "🧭",
        "label": "稳妥",
        "hint": "匹配度较高，适合作为主力志愿",
        "main": "#7C3BFF",
        "soft": "rgba(124,59,255,0.12)",
        "surface": "#F6F0FF",
    },
    "保": {
        "emoji": "🛡️",
        "label": "保底",
        "hint": "安全边际更大，适合兜底",
        "main": "#10B981",
        "soft": "rgba(16,185,129,0.12)",
        "surface": "#EBFBF5",
    },
    "政策红利": {
        "emoji": "🎯",
        "label": "政策红利",
        "hint": "优先看专项计划与政策加成",
        "main": "#B6681D",
        "soft": "rgba(243,160,76,0.12)",
        "surface": "#FFF7EF",
    },
}
DISPLAY_BUCKETS = ["冲", "稳", "保", "政策红利"]
PREVIEW_LIMIT = 20

RECORDS_PATH = Path("data/processed/admission_records.csv")
METRICS_PATH = Path("data/processed/admission_metrics_long.csv")
POLICY_RULES_PATH = Path("configs/policy_rules.gansu.json")
REGION_DICT_PATH = Path("configs/region_dict.gansu.json")
try:
    REGION_DICT = json.loads(REGION_DICT_PATH.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    REGION_DICT = {}

PLAN_GROUP_INTRO = {
    "国家专项": "面向贫困县考生，优先在本科批（C段）投档。",
    "地方专项": "省属高校面向农村考生，本科批（C段）。",
    "高校专项": "重点高校农村专项，本科批（B段）顺序志愿。",
    "建档立卡专项": "建档立卡家庭专项，本科C段/专科F段。",
    "革命老区专项": "革命老区考生专项，本科批（C段）。",
    "两州一县专项": "民族地区紧缺人才专项，本科批（C段）。",
    "少数民族专项": "藏区及其他民族地区专项，本科批（C段）。",
    "农村免费医学生（省属）": "省属免费医学生，本科A段/专科P段。",
    "农村免费医学生（国家）": "国家免费医学生，本科提前批（A段）。",
    "公费师范生": "国家/省属公费师范，本科提前批（A段）。",
    "市级定向培养": "市级定向培养，本科A段或专科P段。",
    "少数民族预科班": "少数民族预科班，本科批（C段）。",
    "民族班": "民族班，本科批（C段）。",
    "边防军人子女预科": "边防军人子女预科，本科批（C段）。",
    "强基计划": "强基计划，A段之前单独投档录取。",
    "综合评价录取": "综合评价录取，A段或单独批次。",
}

GANSU_CITY_COUNTIES = {
    "兰州市": ["城关区", "七里河区", "西固区", "安宁区", "红古区", "永登县", "皋兰县", "榆中县"],
    "嘉峪关市": ["嘉峪关市"],
    "金昌市": ["金川区", "永昌县"],
    "白银市": ["白银区", "平川区", "靖远县", "会宁县", "景泰县"],
    "天水市": ["秦州区", "麦积区", "清水县", "秦安县", "甘谷县", "武山县", "张家川回族自治县"],
    "武威市": ["凉州区", "民勤县", "古浪县", "天祝藏族自治县"],
    "张掖市": ["甘州区", "肃南裕固族自治县", "民乐县", "临泽县", "高台县", "山丹县"],
    "平凉市": ["崆峒区", "泾川县", "灵台县", "崇信县", "庄浪县", "静宁县", "华亭市"],
    "酒泉市": ["肃州区", "金塔县", "瓜州县", "肃北蒙古族自治县", "阿克塞哈萨克族自治县", "玉门市", "敦煌市"],
    "庆阳市": ["西峰区", "庆城县", "环县", "华池县", "合水县", "正宁县", "宁县", "镇原县"],
    "定西市": ["安定区", "通渭县", "陇西县", "渭源县", "临洮县", "漳县", "岷县"],
    "陇南市": ["武都区", "成县", "文县", "宕昌县", "康县", "西和县", "礼县", "徽县", "两当县"],
    "临夏州": ["临夏市", "临夏县", "康乐县", "永靖县", "广河县", "和政县", "东乡族自治县", "积石山保安族东乡族撒拉族自治县"],
    "甘南州": ["合作市", "临潭县", "卓尼县", "舟曲县", "迭部县", "玛曲县", "碌曲县", "夏河县"],
}

NATION_OPTIONS = [
    "汉族",
    "藏族",
    "回族",
    "蒙古族",
    "东乡族",
    "土族",
    "裕固族",
    "保安族",
    "撒拉族",
    "其他少数民族",
    "其他（自填）",
]
NATION_OTHER_LABEL = "其他（自填）"

BOOL_REVIEW_OPTIONS = ["未确认", "是", "否"]
SPECIAL_IDENTITY_OPTIONS = {
    "未确认": None,
    "边防军人子女": "border_military_child",
    "强基计划候选": "strong_foundation_candidate",
    "综合评价候选": "comprehensive_evaluation_candidate",
    "无": "none",
}
BATCH_FILTER_OPTIONS = [
    "全部",
    "本科提前批(A段)",
    "本科批(B段)",
    "本科批(C段)",
    "高职(专科)批(F段)",
    "高职(专科)提前批(D段)",
    "高职(专科)提前批(E段)",
]
RECOMMENDABLE_BATCH_OPTIONS = BATCH_FILTER_OPTIONS[1:]
REVIEW_FIELD_LABELS = {
    "parent_has_local_hukou": "父母是否本地户籍",
    "parent_region": "父母户籍区县",
    "school_region": "学籍区县",
    "graduated_in_region_school": "是否在本地学校就读",
    "special_review_passed": "专项资格审核是否通过",
    "special_identity": "专项身份",
    "has_ethnic_language_score": "是否有民族语成绩",
    "previous_special_plan_breach": "是否存在专项计划失信",
}


def format_probability(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def format_decimal(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def format_int(value: int | float | None) -> str:
    if value is None:
        return "-"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "-"
    if math.isnan(numeric):
        return "-"
    return f"{int(numeric):,}"


def format_hukou(value: str) -> str:
    if value == "rural_only":
        return "农村"
    if value == "urban":
        return "城市"
    return "不限"


def format_subjects(subjects: list[str]) -> str:
    return "、".join(subjects) if subjects else "待选择"


def validate_form(subjects: list[str], rank: int, score: int) -> list[str]:
    errors: list[str] = []
    if len(subjects) != 2:
        errors.append("请先选择两门再选科目。")
    if not rank:
        errors.append("当前系统以位次优先，生成推荐前必须填写全省位次。")
    if not score:
        errors.append("建议同时填写高考分数，便于前端展示更完整的用户画像。")
    return errors


def sparkline_svg(values: list[float], color: str, width: int = 240, height: int = 84) -> str:
    safe_values = values if values else [1.0, 1.0, 1.0]
    minimum = min(safe_values)
    maximum = max(safe_values)
    span = maximum - minimum or 1
    step_x = width / max(len(safe_values) - 1, 1)
    points: list[str] = []
    base_points = [f"0,{height}"]
    for index, value in enumerate(safe_values):
        x = index * step_x
        y = height - (((value - minimum) / span) * (height - 24) + 10)
        points.append(f"{x:.1f},{y:.1f}")
        base_points.append(f"{x:.1f},{y:.1f}")
    base_points.append(f"{width},{height}")
    polyline = " ".join(points)
    polygon = " ".join(base_points)
    dots = "".join(
        f'<circle cx="{pt.split(",")[0]}" cy="{pt.split(",")[1]}" r="3.2" fill="{color}" />'
        for pt in points
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="90" preserveAspectRatio="none">'
        f'<polygon points="{polygon}" fill="{color}" opacity="0.10" />'
        f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{polyline}" />'
        f"{dots}"
        "</svg>"
    )


def smooth_curve_svg(values: list[float], color: str, width: int = 240, height: int = 84) -> str:
    safe_values = values if values else [0.02, 0.02, 0.02]
    average = sum(safe_values) / len(safe_values)
    spread = (max(safe_values) - min(safe_values)) if len(safe_values) > 1 else 0.0
    normalized = max(0.0, min(1.0, (average - 0.0205) / 0.0115))
    amplitude = 0.9 + (normalized**2.6) * 26
    baseline = height * 0.58
    periods = 1.15 + normalized * 1.75
    harmonic = (normalized**1.8) * 0.34
    samples = 96
    points: list[tuple[float, float]] = []

    for index in range(samples + 1):
        progress = index / samples
        x = width * progress
        phase = progress * periods * math.pi * 2
        envelope = 0.98 + normalized * 0.18 * math.sin(progress * math.pi)
        wave = math.sin(phase) + harmonic * math.sin(phase * 2.35 + 0.6)
        y = baseline - wave * amplitude * envelope
        points.append((x, y))

    line_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_path = f"{line_path} L {width:.1f},{baseline:.1f} L 0,{baseline:.1f} Z"
    gradient_id = f"wave-{int(average * 1000000)}-{int(spread * 1000000)}"
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="90" preserveAspectRatio="none">'
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.28" />'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.03" />'
        f"</linearGradient></defs>"
        f'<line x1="0" y1="{baseline:.1f}" x2="{width:.1f}" y2="{baseline:.1f}" stroke="{color}" stroke-opacity="0.16" stroke-width="1.4" stroke-dasharray="4 5" />'
        f'<path d="{area_path}" fill="url(#{gradient_id})" />'
        f'<path d="{line_path}" fill="none" stroke="{color}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" />'
        "</svg>"
    )


def metric_block(label: str, value: str) -> str:
    return (
        '<div class="mini-metric">'
        f'<div class="mini-metric-label">{html.escape(label)}</div>'
        f'<div class="mini-metric-value">{html.escape(value)}</div>'
        "</div>"
    )


def detail_chip(text: str, tone: str = "default") -> str:
    return f'<span class="detail-chip detail-chip-{tone}">{html.escape(text)}</span>'


def cv_meta(cv: float | None) -> dict[str, str]:
    cv_value = float(cv or 0)
    if cv_value >= 0.028:
        return {
            "color": "#E74C3C",
            "soft": "#FDEDEC",
            "label": "大小年明显",
            "hint": "波动较大，建议降低排序或搭配更稳志愿。",
        }
    if cv_value <= 0.021:
        return {
            "color": "#10B981",
            "soft": "#ECFBF5",
            "label": "波动平稳",
            "hint": "波动较小，历史稳定性更好，可优先关注。",
        }
    return {
        "color": "#D28B1E",
        "soft": "#FFF6E8",
        "label": "存在波动",
        "hint": "近年有一定起伏，建议结合整体志愿顺序判断。",
    }


def build_profile_snapshot(
    track: str,
    subjects: list[str],
    score: int,
    rank: int,
    region: str,
    hukou: str,
    nation: str,
    school_years: int,
) -> dict[str, str | int | list[str]]:
    return {
        "track": track,
        "subjects": subjects,
        "score": score,
        "rank": rank,
        "region": region,
        "hukou": hukou,
        "nation": nation,
        "school_years": school_years,
    }


def build_profile_tags(snapshot: dict[str, str | int | list[str]]) -> list[str]:
    tags = [
        "位次优先",
        f"{snapshot['track']}类",
        "推荐模式 V2",
    ]
    if snapshot["score"]:
        tags.append(f"{snapshot['score']}分")
    if snapshot["rank"]:
        tags.append(f"位次 {format_int(snapshot['rank'])}")
    if snapshot["hukou"] == "rural_only":
        tags.append("专项可加权")
    if snapshot["region"]:
        tags.append(str(snapshot["region"]))
    return tags[:6]


def render_profile_panel(snapshot: dict[str, str | int | list[str]]) -> str:
    tags_html = "".join(detail_chip(tag, "accent") for tag in build_profile_tags(snapshot))
    score_text = f"{snapshot['score']} 分" if snapshot["score"] else "待填写"
    rank_text = f"全省 {format_int(snapshot['rank'])}" if snapshot["rank"] else "待填写"
    region_text = str(snapshot["region"] or "待填写")
    nation_text = str(snapshot["nation"] or "待填写")
    return f"""
    <div class="glass-base profile-wrap">
        <div class="profile-title">考生画像</div>
        <div class="profile-subtitle">左侧保留画像总览，右侧按板块切换查看推荐结果；筛选与计算逻辑保持原样，只替换视觉呈现。</div>
        <div class="portrait-box">
            <div class="portrait-label">分数 / 位次</div>
            <div class="portrait-value">{html.escape(score_text)} ｜ {html.escape(rank_text)}</div>
        </div>
        <div class="portrait-box">
            <div class="portrait-label">科类 / 选科</div>
            <div class="portrait-value">{html.escape(str(snapshot['track']))} ｜ {html.escape(format_subjects(snapshot['subjects']))}</div>
        </div>
        <div class="portrait-box">
            <div class="portrait-label">地区 / 户籍</div>
            <div class="portrait-value">{html.escape(region_text)} ｜ {html.escape(format_hukou(str(snapshot['hukou'])))}</div>
        </div>
        <div class="portrait-box">
            <div class="portrait-label">民族</div>
            <div class="portrait-value">{html.escape(nation_text)}</div>
        </div>
        <div class="tag-row">{tags_html}</div>
    </div>
    """


def render_hero(profile_snapshot: dict[str, str | int | list[str]], has_result: bool) -> str:
    title = "甘肃高考志愿推荐系统"
    text = (
        "本页重点展示位次预测、风险分层与政策规则结构化挖掘的联动效果，为甘肃考生提供志愿填报参考。"
        if has_result
        else '先在左侧填写考生信息并点击"生成推荐"，右侧将展示冲 / 稳 / 保 / 政策红利结果，并给出推荐依据。'
    )
    badge = "Policy Mining + Rank-Based Recommendation"
    query_text = (
        f"当前输入：{profile_snapshot['track']} / {format_subjects(profile_snapshot['subjects'])} / 分数 {format_int(profile_snapshot['score'])} / 位次 {format_int(profile_snapshot['rank'])}"
    )
    return f"""
    <div class="glass-base hero-panel">
        <div class="hero-badge">{html.escape(badge)}</div>
        <div class="hero-title">{html.escape(title)}</div>
        <div class="hero-text">{html.escape(text)}</div>
        <div class="hero-query">{html.escape(query_text)}</div>
    </div>
    """


def render_summary_cards(summary: dict | None, policy_count_override: int | None = None) -> str:
    counts = (summary or {}).get("counts", {}) if summary else {}
    cards: list[str] = []
    for bucket in DISPLAY_BUCKETS:
        meta = RISK_META[bucket]
        count_value = counts.get(bucket, "-") if summary else "-"
        if bucket == "政策红利" and policy_count_override is not None:
            count_value = policy_count_override
        cards.append(
            f'<div class="summary-card">'
            f'<div class="summary-label">{meta["emoji"]} {html.escape(bucket)}</div>'
            f'<div class="summary-value">{count_value}</div>'
            f'<div class="summary-note">{html.escape(meta["hint"])}</div>'
            f"</div>"
        )
    return '<div class="summary-row">' + "".join(cards) + "</div>"


def render_threshold_strip(summary: dict | None) -> str:
    thresholds = (summary or {}).get("thresholds", {}) if summary else {}
    return f"""
    <div class="glass-base threshold-strip">
        阈值策略：冲 ≥ {format_probability(thresholds.get('冲'))} ｜
        稳 ≥ {format_probability(thresholds.get('稳'))} ｜
        保 ≥ {format_probability(thresholds.get('保'))}
    </div>
    """


def build_trend_values(item: dict) -> list[float]:
    history = item.get("history", {})
    values = [
        history.get("max_rank_3y"),
        history.get("avg_rank_3y"),
        history.get("min_rank_3y"),
    ]
    clean_values = [float(value) for value in values if value is not None]
    if len(clean_values) >= 2:
        return clean_values
    target_rank = item.get("score", {}).get("target_rank")
    if target_rank is None:
        return [1.0, 1.0, 1.0]
    base = float(target_rank)
    return [base * 1.08, base, base * 0.94]


def build_cv_values(item: dict) -> list[float]:
    score = item.get("score", {})
    history = item.get("history", {})
    cv = float(score.get("rank_cv") or 0.0)
    years_available = int(history.get("years_available") or 0)
    scale = 0.22 if years_available >= 3 else 0.32 if years_available == 2 else 0.46
    spread = max(0.0007, cv * scale)
    return [max(0.0, cv + spread), cv, max(0.0, cv - spread * 0.85)]


def build_warning_messages(item: dict) -> list[str]:
    history = item.get("history", {})
    plan = item.get("plan", {})
    years_available = int(history.get("years_available") or 0)
    warnings: list[str] = []
    if years_available == 1:
        warnings.append("仅有 1 年历史样本，结果已做明显保守处理")
    elif years_available == 2:
        warnings.append("仅有 2 年历史样本，结果已做保守降权")
    if plan.get("is_new_major") == "新增":
        warnings.append("该专业为新增专业，历史样本不足")
    return warnings


def summarize_policy_eligibility(profile: UserProfile) -> dict[str, list[str] | int]:
    engine = PolicyEngine("configs/policy_rules.gansu.json", "configs/region_dict.gansu.json")
    results = engine.evaluate_all(profile)
    eligible = [item.plan_tag for item in results if item.eligible]
    blocked = [item for item in results if not item.eligible]

    reasons_hit: list[str] = []
    reasons_miss: list[str] = []
    for item in results:
        reasons_hit.extend(item.reasons_hit)
    for item in blocked[:4]:
        reasons_miss.extend(item.reasons_miss[:2])

    dedup_hit = list(dict.fromkeys(eligible))
    dedup_reasons_hit = list(dict.fromkeys(reasons_hit))[:6]
    dedup_reasons_miss = list(dict.fromkeys(reasons_miss))[:6]
    return {
        "eligible_plans": dedup_hit,
        "blocked_plan_count": len(blocked),
        "hit_reasons": dedup_reasons_hit,
        "miss_reasons": dedup_reasons_miss,
    }


def get_file_version(path: Path) -> tuple[str, int, int]:
    resolved = path.resolve()
    stat = resolved.stat()
    return (str(resolved), stat.st_mtime_ns, stat.st_size)


def serialize_profile(profile: UserProfile, include_selected_plan_groups: bool = True) -> str:
    payload = asdict(profile)
    payload["selected_subjects"] = list(payload.get("selected_subjects") or [])
    selected_plan_groups = list(dict.fromkeys(payload.get("selected_plan_groups") or []))
    payload["selected_plan_groups"] = selected_plan_groups if include_selected_plan_groups else []
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def deserialize_profile(profile_payload: str) -> UserProfile:
    return UserProfile(**json.loads(profile_payload))


def build_profile_input_signature(profile: UserProfile) -> tuple[tuple[object, ...], ...]:
    return (
        ("profile", serialize_profile(profile, include_selected_plan_groups=False), 0),
        get_file_version(RECORDS_PATH),
        get_file_version(METRICS_PATH),
        get_file_version(POLICY_RULES_PATH),
        get_file_version(REGION_DICT_PATH),
    )


def build_profile_generation_signature(profile: UserProfile) -> tuple[tuple[object, ...], ...]:
    return (
        ("profile", serialize_profile(profile, include_selected_plan_groups=True), 0),
        get_file_version(RECORDS_PATH),
        get_file_version(METRICS_PATH),
        get_file_version(POLICY_RULES_PATH),
        get_file_version(REGION_DICT_PATH),
    )


@st.cache_data(show_spinner=False, max_entries=64)
def get_cached_recommendation_bundle(
    profile_payload: str,
    records_version: tuple[str, int, int],
    metrics_version: tuple[str, int, int],
    rules_version: tuple[str, int, int],
    region_version: tuple[str, int, int],
) -> dict[str, dict[str, list[str] | int] | dict]:
    del records_version, metrics_version, rules_version, region_version
    profile = deserialize_profile(profile_payload)
    policy_summary = summarize_policy_eligibility(profile)
    result = recommend_for_frontend(
        str(RECORDS_PATH),
        str(METRICS_PATH),
        str(POLICY_RULES_PATH),
        str(REGION_DICT_PATH),
        profile,
    )
    return {
        "policy_summary": policy_summary,
        "result": result,
    }


def get_recommendation_cache_args(
    profile: UserProfile,
) -> tuple[str, tuple[str, int, int], tuple[str, int, int], tuple[str, int, int], tuple[str, int, int]]:
    return (
        serialize_profile(profile, include_selected_plan_groups=True),
        get_file_version(RECORDS_PATH),
        get_file_version(METRICS_PATH),
        get_file_version(POLICY_RULES_PATH),
        get_file_version(REGION_DICT_PATH),
    )


def store_generated_bundle(
    profile: UserProfile,
    bundle: dict[str, dict[str, list[str] | int] | dict],
) -> None:
    st.session_state.generated_result = bundle.get("result")
    st.session_state.generated_policy_summary = bundle.get("policy_summary")
    st.session_state.generated_profile_input_signature = build_profile_input_signature(profile)
    st.session_state.generated_profile_generation_signature = build_profile_generation_signature(profile)


def normalize_bool_choice(value: str | None) -> bool | None:
    if value == "是":
        return True
    if value == "否":
        return False
    return None


def ensure_review_state() -> None:
    defaults = {
        "review_parent_has_local_hukou": "未确认",
        "review_parent_city": "未选择",
        "review_parent_region": "未选择",
        "review_school_city": "未选择",
        "review_school_region": "未选择",
        "review_graduated_in_region_school": "未确认",
        "review_special_review_passed": "未确认",
        "review_special_identity": "未确认",
        "review_has_ethnic_language_score": "未确认",
        "review_previous_special_plan_breach": "未确认",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def collect_review_values() -> dict[str, str | bool | None]:
    parent_region = st.session_state.get("review_parent_region")
    school_region = st.session_state.get("review_school_region")
    parent_region_value = None if parent_region in {None, "", "未选择"} else parent_region
    school_region_value = None if school_region in {None, "", "未选择"} else school_region
    special_identity_choice = st.session_state.get("review_special_identity")
    return {
        "parent_has_local_hukou": normalize_bool_choice(st.session_state.get("review_parent_has_local_hukou")),
        "parent_region": parent_region_value,
        "school_region": school_region_value,
        "graduated_in_region_school": normalize_bool_choice(st.session_state.get("review_graduated_in_region_school")),
        "special_review_passed": normalize_bool_choice(st.session_state.get("review_special_review_passed")),
        "special_identity": SPECIAL_IDENTITY_OPTIONS.get(str(special_identity_choice)),
        "has_ethnic_language_score": normalize_bool_choice(st.session_state.get("review_has_ethnic_language_score")),
        "previous_special_plan_breach": normalize_bool_choice(st.session_state.get("review_previous_special_plan_breach")),
    }


def is_missing_field(value: object) -> bool:
    return value in {None, ""}


def collect_missing_fields(rules: dict, profile: UserProfile) -> set[str]:
    missing: set[str] = set()

    if rules.get("guardian_region_required", False):
        if profile.parent_has_local_hukou is None:
            missing.add("parent_has_local_hukou")
        if profile.parent_has_local_hukou:
            if is_missing_field(profile.parent_region):
                missing.add("parent_region")

    if rules.get("actual_schooling_required", False):
        if profile.graduated_in_region_school is None:
            missing.add("graduated_in_region_school")

    if rules.get("special_review_pass_required", False):
        if profile.special_review_passed is None:
            missing.add("special_review_passed")

    if rules.get("special_identity_required"):
        if is_missing_field(profile.special_identity):
            missing.add("special_identity")

    if rules.get("ethnic_language_score_required", False):
        if profile.has_ethnic_language_score is None:
            missing.add("has_ethnic_language_score")

    if rules.get("previous_special_plan_breach_forbidden", False):
        if profile.previous_special_plan_breach is None:
            missing.add("previous_special_plan_breach")

    scope = rules.get("region_scope")
    if scope and scope not in {"gansu_rural_all", "gansu_local_target_area"}:
        for field in rules.get("region_compare_fields", []):
            value = getattr(profile, field, None)
            if field == "parent_region" and profile.parent_has_local_hukou is False:
                continue
            if is_missing_field(value):
                missing.add(field)

    return missing


def describe_missing_fields(missing: set[str]) -> list[str]:
    return [REVIEW_FIELD_LABELS.get(field, field) for field in sorted(missing)]


def evaluate_plan_status(plan: dict, profile: UserProfile, engine: PolicyEngine) -> tuple[str, set[str], list[str]]:
    rules = plan.get("rules", {}) if plan else {}
    missing = collect_missing_fields(rules, profile)
    if missing:
        return "pending", missing, describe_missing_fields(missing)
    payload = {"plan_tag": plan.get("plan_tag", ""), "rules": rules}
    result = engine.evaluate_plan(payload, profile)
    return (
        "eligible" if result.eligible else "blocked",
        set(),
        [str(reason) for reason in (result.reasons_miss or []) if reason],
    )


def build_group_status(profile: UserProfile) -> tuple[dict[str, str], dict[str, set[str]], dict[str, list[str]]]:
    engine = PolicyEngine("configs/policy_rules.gansu.json", "configs/region_dict.gansu.json")
    status_by_group: dict[str, str] = {}
    missing_by_group: dict[str, set[str]] = {}
    reason_by_group: dict[str, list[str]] = {}
    for group, tags in PLAN_GROUPS.items():
        group_status = "blocked"
        group_missing: set[str] = set()
        group_reasons: list[str] = []
        for tag in tags:
            plan = PLAN_BY_TAG.get(tag)
            if not plan:
                continue
            status, missing, reasons = evaluate_plan_status(plan, profile, engine)
            if status == "eligible":
                group_status = "eligible"
                group_missing = set()
                group_reasons = []
                break
            if status == "pending":
                group_status = "pending"
                group_missing |= missing
                group_reasons = describe_missing_fields(group_missing)
            elif group_status != "pending":
                group_reasons.extend(reasons)
                group_reasons = list(dict.fromkeys([reason for reason in group_reasons if reason]))[:3]
        status_by_group[group] = group_status
        missing_by_group[group] = group_missing
        reason_by_group[group] = group_reasons
    return status_by_group, missing_by_group, reason_by_group


def build_current_profile(
    track: str,
    subjects: list[str],
    score: int,
    rank: int,
    region: str,
    hukou: str,
    nation: str,
    school_years: int,
    hukou_years: int,
    parent_hukou_years: int,
    is_registered: bool,
    parent_region: str | None,
    school_region: str | None,
    parent_has_local_hukou: bool | None,
    graduated_in_region_school: bool | None,
    special_review_passed: bool | None,
    special_identity: str | None,
    has_ethnic_language_score: bool | None,
    previous_special_plan_breach: bool | None,
) -> UserProfile:
    return UserProfile(
        track=track,
        selected_subjects=subjects,
        score=int(score) if score else None,
        rank=int(rank) if rank else None,
        region=region or None,
        hukou_nature=hukou,
        nation=nation or None,
        parent_region=parent_region,
        school_region=school_region,
        school_years=int(school_years),
        hukou_years=int(hukou_years),
        parent_hukou_years=int(parent_hukou_years),
        is_registered_poverty_family=is_registered,
        parent_has_local_hukou=parent_has_local_hukou,
        graduated_in_region_school=graduated_in_region_school,
        special_review_passed=special_review_passed,
        special_identity=special_identity,
        has_ethnic_language_score=has_ethnic_language_score,
        previous_special_plan_breach=previous_special_plan_breach,
    )


def render_policy_overview(policy_summary: dict[str, list[str] | int] | None) -> str:
    if not policy_summary:
        return ""

    eligible_plans = policy_summary.get("eligible_plans", [])
    hit_reasons = policy_summary.get("hit_reasons", [])
    miss_reasons = policy_summary.get("miss_reasons", [])
    blocked_plan_count = policy_summary.get("blocked_plan_count", 0)

    if not eligible_plans:
        return """
        <div class="glass-base policy-panel policy-panel-empty">
            <div class="policy-empty-title">暂未发现政策红利</div>
            <div class="policy-empty-text">当前考生画像下，暂未识别到可用专项计划，政策红利推荐暂不展示。</div>
        </div>
        """

    eligible_html = "".join(detail_chip(str(plan), "accent") for plan in eligible_plans[:8]) or detail_chip("当前未命中专项计划", "default")
    hit_html = "".join(detail_chip(str(reason), "default") for reason in hit_reasons[:6])
    miss_html = "".join(detail_chip(str(reason), "warning") for reason in miss_reasons[:4])

    return f"""
    <div class="glass-base policy-panel">
        <div class="policy-panel-header">
            <div>
                <div class="policy-panel-title">政策挖掘结果</div>
                <div class="policy-panel-subtitle">将户籍、地区、学籍、民族与专项身份条件结构化判定，识别当前考生可用的政策红利。</div>
            </div>
            <div class="policy-counter">命中 {len(eligible_plans)} 项｜未命中 {blocked_plan_count} 项</div>
        </div>
        <div class="policy-section">
            <div class="policy-section-label">已命中政策</div>
            <div class="detail-row">{eligible_html}</div>
        </div>
        <div class="policy-section">
            <div class="policy-section-label">命中依据（结构化规则）</div>
            <div class="detail-row">{hit_html or detail_chip('当前条件未触发明确规则', 'default')}</div>
        </div>
        <div class="policy-section">
            <div class="policy-section-label">未命中的高频原因</div>
            <div class="detail-row">{miss_html or detail_chip('当前输入下无明显限制项', 'default')}</div>
        </div>
    </div>
    """


def render_empty_panel(title: str, text: str, tips: list[str] | None = None) -> str:
    tips_html = "".join(f"<li>{html.escape(tip)}</li>" for tip in (tips or []))
    tips_block = f"<ul>{tips_html}</ul>" if tips_html else ""
    return f"""
    <div class="empty-panel">
        <div class="empty-title">{html.escape(title)}</div>
        <div class="empty-text">{html.escape(text)}</div>
        {tips_block}
    </div>
    """


def render_policy_hint(policy_summary: dict[str, list[str] | int] | None) -> str:
    if not policy_summary:
        return ""
    eligible = policy_summary.get("eligible_plans", [])
    reasons = policy_summary.get("hit_reasons", [])
    summary = "、".join(str(plan) for plan in eligible[:3]) if eligible else "暂无专项命中"
    reason_text = "；".join(str(reason) for reason in reasons[:2]) if reasons else "暂无明确规则触发"
    return f"政策提示：{summary}（依据：{reason_text}）"


def compact_html_block(block: str) -> str:
    return "\n".join(line.strip() for line in block.splitlines() if line.strip())


def infer_explicit_plan_groups(item: dict) -> list[str]:
    for key in ("matched_plan_tags", "all_matched_plan_tags"):
        matched_tags = item.get(key) or []
        if matched_tags:
            groups = [SUBTAG_TO_GROUP.get(tag, tag) for tag in matched_tags]
            return list(dict.fromkeys(groups))

    text_parts = [
        item.get("school_name"),
        item.get("major_name"),
        item.get("group_name"),
        item.get("batch"),
    ]
    combined = normalize_plan_text("".join(str(part) for part in text_parts if part))
    return infer_plan_groups_from_text(combined, PLAN_GROUPS.keys())


def infer_item_plan_groups_for_display(item: dict) -> list[str]:
    synthetic = item.get("synthetic_plan_groups") or []
    if synthetic:
        return list(dict.fromkeys([str(group) for group in synthetic if group]))
    return infer_explicit_plan_groups(item)


def filter_groups_by_batch(groups: list[str], item_batch: str | None) -> list[str]:
    return list(
        dict.fromkeys(
            [
                str(group)
                for group in groups
                if group and group_matches_batch(str(group), item_batch)
            ]
        )
    )


def resolve_item_plan_groups(
    item: dict,
    selected_plan_tags: list[str] | None = None,
) -> list[str]:
    item_batch = item.get("batch")
    explicit_groups = filter_groups_by_batch(infer_explicit_plan_groups(item), item_batch)
    synthetic_groups = filter_groups_by_batch(
        [str(group) for group in (item.get("synthetic_plan_groups") or []) if group],
        item_batch,
    )
    base_groups = explicit_groups or synthetic_groups

    if not selected_plan_tags:
        return base_groups

    selected_groups = list(dict.fromkeys([str(group) for group in selected_plan_tags if group]))
    return [group for group in selected_groups if group in base_groups]


def extract_batch_codes(value: str | None) -> set[str]:
    if not value:
        return set()
    normalized = normalize_batch(value).upper()
    return set(re.findall(r"([A-Z])段", normalized))


def group_matches_batch(group_name: str, item_batch: str | None) -> bool:
    group_batch = PLAN_GROUP_BATCH.get(group_name, "")
    if not group_batch:
        return True
    item_codes = extract_batch_codes(item_batch)
    group_codes = extract_batch_codes(group_batch)
    if item_codes and group_codes:
        return bool(item_codes.intersection(group_codes))
    item_text = normalize_batch(item_batch)
    group_text = normalize_batch(group_batch)
    return bool(item_text and group_text and (item_text in group_text or group_text in item_text))


def plan_group_matches_selected_batch(group_name: str, selected_batch: str) -> bool:
    if not selected_batch or selected_batch == "全部":
        return True
    recommendable_batches = extract_recommendable_batches(PLAN_GROUP_BATCH.get(group_name, ""))
    if not recommendable_batches:
        return False
    return any(normalize_batch(batch_name) == normalize_batch(selected_batch) for batch_name in recommendable_batches)


def item_matches_selected_plan(item: dict, selected_plan_tags: list[str]) -> bool:
    if not selected_plan_tags:
        return True
    resolved_groups = resolve_item_plan_groups(item, selected_plan_tags)
    return bool(resolved_groups)


def filter_policy_items(items: list[dict], selected_plan_tags: list[str]) -> list[dict]:
    if selected_plan_tags:
        return [item for item in items if item_matches_selected_plan(item, selected_plan_tags)]
    return items


def get_policy_view_items(
    items: list[dict],
    selected_plan_tags: list[str],
    selected_batch: str,
) -> tuple[list[dict], dict[str, int | str]]:
    batch_items = filter_items_by_batch(items, selected_batch)
    strict_items = filter_policy_items(batch_items, selected_plan_tags)

    if strict_items:
        return strict_items, {
            "mode": "strict",
            "strict_count": len(strict_items),
            "batch_count": len(batch_items),
        }
    if selected_plan_tags and not strict_items:
        return [], {
            "mode": "selected_empty",
            "strict_count": 0,
            "batch_count": len(batch_items),
        }

    return [], {
        "mode": "empty",
        "strict_count": 0,
        "batch_count": len(batch_items),
    }


def normalize_batch(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip().replace(" ", "")
    return text.replace("（", "(").replace("）", ")")


def item_matches_batch(item: dict, selected_batch: str) -> bool:
    if not selected_batch or selected_batch == "全部":
        return True
    batch_text = normalize_batch(item.get("batch"))
    if not batch_text:
        return False
    selected_text = normalize_batch(selected_batch)
    return selected_text in batch_text


def extract_recommendable_batches(batch_text: str | None) -> list[str]:
    normalized = normalize_batch(batch_text)
    if not normalized:
        return []
    return [
        option
        for option in RECOMMENDABLE_BATCH_OPTIONS
        if normalize_batch(option) in normalized
    ]


def format_group_batch_display(group_name: str) -> str:
    recommendable_batches = extract_recommendable_batches(PLAN_GROUP_BATCH.get(group_name, ""))
    if recommendable_batches:
        return " / ".join(recommendable_batches)
    return "暂无推荐数据"


def group_has_recommendation_data(group_name: str) -> bool:
    return bool(extract_recommendable_batches(PLAN_GROUP_BATCH.get(group_name, "")))


def build_group_data_notice(group_name: str) -> str:
    raw_batch = PLAN_GROUP_BATCH.get(group_name, "")
    recommendable_batches = extract_recommendable_batches(raw_batch)
    if not raw_batch:
        return ""
    if not recommendable_batches:
        return "当前原始录取数据中不含该计划对应批次，暂时无法生成推荐。"
    unsupported_tokens: list[str] = []
    if "P段" in raw_batch:
        unsupported_tokens.append("P段")
    if "单独批次" in raw_batch:
        unsupported_tokens.append("单独批次")
    if "单独投档" in raw_batch:
        unsupported_tokens.append("单独投档")
    if "按院校方案" in raw_batch:
        unsupported_tokens.append("院校单独方案")
    unsupported_tokens = list(dict.fromkeys(unsupported_tokens))
    if unsupported_tokens:
        return f"当前仅支持按{' / '.join(recommendable_batches)}推荐，{'、'.join(unsupported_tokens)}暂无原始录取数据。"
    return ""


def filter_items_by_batch(items: list[dict], selected_batch: str) -> list[dict]:
    if not selected_batch or selected_batch == "全部":
        return items
    return [item for item in items if item_matches_batch(item, selected_batch)]


def render_card(
    item: dict,
    bucket: str,
    policy_summary: dict[str, list[str] | int] | None = None,
    index: int | None = None,
    selected_plan_tags: list[str] | None = None,
) -> str:
    meta = RISK_META[bucket]
    score = item.get("score", {})
    history = item.get("history", {})
    plan = item.get("plan", {})
    cv_value = score.get("rank_cv")
    cv_status = cv_meta(cv_value)
    trend_chart = sparkline_svg(build_trend_values(item), meta["main"])
    cv_chart = smooth_curve_svg(build_cv_values(item), cv_status["color"])
    policy_bonus_value = item.get("effective_policy_bonus") if bucket == "政策红利" else item.get("policy_bonus")
    metrics = "".join(
        [
            metric_block("录取概率", format_probability(score.get("admission_probability"))),
            metric_block("目标位次", format_int(score.get("target_rank"))),
            metric_block("平均位次", format_int(history.get("avg_rank_3y"))),
            metric_block("历史年数", format_int(history.get("years_available"))),
            metric_block("政策加权", format_decimal(policy_bonus_value, 3)),
        ]
    )
    warning_chips = "".join(detail_chip(message, "warning") for message in build_warning_messages(item))
    detail_chips = "".join(
        [
            detail_chip(f"学校层次：{item.get('school_level') or '-'}"),
            detail_chip(f"选科要求：{item.get('subject_requirement') or '-'}"),
            detail_chip(f"计划数：{format_int(plan.get('plan_count'))}"),
            detail_chip(f"概率等级：{score.get('admission_probability_label') or '-'}"),
        ]
    )
    policy_hits: list[str] = []
    if bucket == "政策红利":
        policy_hits = resolve_item_plan_groups(item, selected_plan_tags)
    elif policy_summary:
        policy_hits = list(policy_summary.get("eligible_plans", []))[:4]
    policy_chips = "".join(detail_chip(f"命中政策：{plan_name}", "accent") for plan_name in policy_hits)
    reason_title = "推荐理由（含政策与风险解释）"
    policy_hint = (
        f"当前卡片匹配计划：{'、'.join(policy_hits)}"
        if bucket == "政策红利" and policy_hits
        else render_policy_hint(policy_summary)
    )
    card_index = f"<span class=\"rank-badge\">TOP {index}</span>" if index else ""
    plan_block = ""
    if bucket == "政策红利":
        plan_tags = resolve_item_plan_groups(item, selected_plan_tags)
        if plan_tags:
            if len(plan_tags) == 1:
                plan_display = plan_tags[0]
                plan_intro = PLAN_GROUP_INTRO.get(plan_display, "该志愿匹配专项计划后给予政策加权展示。")
            else:
                plan_display = "、".join(plan_tags)
                plan_intro = f"当前志愿与已勾选计划类型的交集为：{plan_display}。"
        else:
            plan_display = "未识别专项标签"
            plan_intro = "该志愿未识别到明确专项标签，默认不应出现在政策红利结果中。"
        plan_block = (
            f'<div class="plan-tag">计划类型：{html.escape(plan_display)}</div>'
            f'<div class="plan-intro">{html.escape(plan_intro)}</div>'
        )
    html_block = f"""
    <div class="vol-card">
        <div class="card-top-row">
            <div class="title-area">
                <span class="bucket-pill" style="background:{meta['soft']}; color:{meta['main']}; border-color:{meta['soft']};">{meta['emoji']} {html.escape(bucket)}</span>
                {card_index}
                <div class="card-school">{html.escape(item.get('school_name') or '未知院校')} · {html.escape(item.get('major_name') or '未知专业')}</div>
                <div class="card-meta">{html.escape(item.get('batch') or '-')}｜{html.escape(item.get('group_name') or '-')}｜{html.escape(meta['label'])}建议</div>
                {plan_block}
            </div>
            <div class="prob-box" style="background:{meta['surface']};">
                <div class="prob-label">录取概率</div>
                <div class="prob-value">{format_probability(score.get('admission_probability'))}</div>
                <div class="prob-tag" style="color:{meta['main']};">{html.escape(score.get('admission_probability_label') or '-')}</div>
            </div>
        </div>
        <div class="content-grid">
            <div class="info-column">
                <div class="metric-grid">{metrics}</div>
                <div class="reason-title">{reason_title}</div>
                <div class="reason-box">
                    <div>{html.escape(item.get('recommend_reason') or '-')}</div>
                    <div class="reason-hint">{html.escape(policy_hint)}</div>
                </div>
                <div class="detail-row">{policy_chips}</div>
                <div class="cv-note" style="background:{cv_status['soft']}; border-color:{cv_status['soft']};">
                    <span class="cv-note-badge" style="background:{cv_status['color']};">{html.escape(cv_status['label'])}</span>
                    <span class="cv-note-text" style="color:{cv_status['color']};">{html.escape(cv_status['hint'])}</span>
                </div>
                <div class="detail-row">{detail_chips}</div>
                <div class="detail-row">{warning_chips}</div>
            </div>
            <div class="chart-column">
                <div class="chart-box">
                    <div class="chart-title">近 3 年位次区间图</div>
                    {trend_chart}
                    <div class="chart-caption">以最高位次 / 平均位次 / 最低位次压缩绘制：{format_int(history.get('max_rank_3y'))} ｜ {format_int(history.get('avg_rank_3y'))} ｜ {format_int(history.get('min_rank_3y'))}</div>
                </div>
            </div>
            <div class="chart-column">
                <div class="chart-box">
                    <div class="chart-title">CV 波动曲线</div>
                    {cv_chart}
                    <div class="chart-caption">当前 CV：{format_decimal(cv_value, 4)} ｜ 红色更躁动，绿色更平稳</div>
                </div>
            </div>
        </div>
    </div>
    """
    return compact_html_block(html_block)


def initialize_sidebar_state() -> None:
    if "score_input" not in st.session_state:
        st.session_state.score_input = 0
    if "score_slider" not in st.session_state:
        st.session_state.score_slider = int(st.session_state.score_input)
    if "rank_input" not in st.session_state:
        st.session_state.rank_input = 0
    if "show_policy_panel" not in st.session_state:
        st.session_state.show_policy_panel = False
    st.session_state.setdefault("generated_result", None)
    st.session_state.setdefault("generated_policy_summary", None)
    st.session_state.setdefault("generated_profile_input_signature", None)
    st.session_state.setdefault("generated_profile_generation_signature", None)
    for bucket in DISPLAY_BUCKETS:
        st.session_state.setdefault(f"expand_bucket_{bucket}", False)
    ensure_review_state()


def sync_score_from_slider() -> None:
    st.session_state.score_input = int(st.session_state.score_slider)


def sync_score_from_input() -> None:
    st.session_state.score_slider = int(st.session_state.score_input)


def adjust_rank(delta: int) -> None:
    current_rank = int(st.session_state.get("rank_input", 0) or 0)
    st.session_state.rank_input = max(0, current_rank + int(delta))


def toggle_policy_panel() -> None:
    current = bool(st.session_state.get("show_policy_panel", False))
    st.session_state.show_policy_panel = not current


def clear_plan_selections() -> None:
    for group_name in PLAN_GROUP_ORDER:
        key = f"plan_select_{group_name}"
        if key in st.session_state:
            st.session_state[key] = False


def reset_result_expansions() -> None:
    for bucket in DISPLAY_BUCKETS:
        st.session_state[f"expand_bucket_{bucket}"] = False


def expand_bucket_results(bucket: str) -> None:
    st.session_state[f"expand_bucket_{bucket}"] = True


def get_bucket_preview_state(bucket: str) -> bool:
    return bool(st.session_state.get(f"expand_bucket_{bucket}", False))


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 12% 10%, rgba(243, 160, 76, 0.14), transparent 20%),
                radial-gradient(circle at 84% 8%, rgba(124, 59, 255, 0.08), transparent 18%),
                linear-gradient(180deg, #FEFDFC 0%, #FBF7F2 100%);
            color: #1D1D1F;
        }
        .block-container {
            max-width: 1460px;
            padding-top: 1.2rem;
            padding-bottom: 2.2rem;
        }
        section[data-testid="stSidebar"] > div {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(252,247,241,0.92) 100%);
            border-right: 1px solid rgba(236, 228, 221, 0.84);
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        section[data-testid="stSidebar"] .st-key-score_input,
        section[data-testid="stSidebar"] .st-key-rank_input,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]),
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) {
            background: linear-gradient(118deg, rgba(255, 250, 244, 0.95) 0%, rgba(231, 238, 251, 0.92) 100%);
            border: 1px solid rgba(255, 255, 255, 0.92);
            border-radius: 999px;
            padding: 10px 12px 12px 16px;
            margin: 0.12rem 0 1rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68), 0 12px 26px rgba(41, 70, 122, 0.12);
        }
        section[data-testid="stSidebar"] .st-key-score_input label[data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] .st-key-rank_input label[data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) label[data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) label[data-testid="stWidgetLabel"] p {
            color: #15181e;
            font-size: 2rem;
            font-weight: 900;
            line-height: 1.08;
            letter-spacing: 0.2px;
            margin-bottom: 2px;
        }
        section[data-testid="stSidebar"] .st-key-score_input [data-baseweb="input"],
        section[data-testid="stSidebar"] .st-key-rank_input [data-baseweb="input"],
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) [data-baseweb="input"],
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) [data-baseweb="input"] {
            min-height: 72px;
            border: 0;
            background: transparent;
            box-shadow: none;
            padding-right: 2px;
        }
        section[data-testid="stSidebar"] .st-key-score_input [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] .st-key-rank_input [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) [data-baseweb="input"] > div {
            background: transparent;
        }
        section[data-testid="stSidebar"] .st-key-score_input input,
        section[data-testid="stSidebar"] .st-key-rank_input input,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) input,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) input {
            color: #2D333C;
            font-size: clamp(2.15rem, 5.2vw, 2.75rem);
            font-weight: 500;
            letter-spacing: 0.5px;
            background: transparent;
            padding-left: 8px;
        }
        section[data-testid="stSidebar"] .st-key-score_input [data-baseweb="input"] button,
        section[data-testid="stSidebar"] .st-key-rank_input [data-baseweb="input"] button,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) [data-baseweb="input"] button,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) [data-baseweb="input"] button {
            width: 56px;
            height: 56px;
            min-width: 56px;
            border-radius: 999px;
            border: 0;
            background: linear-gradient(162deg, #4A79C5 0%, #2E5CA9 100%);
            color: #F6F9FF;
            box-shadow: 0 10px 24px rgba(38, 74, 139, 0.36);
            margin-left: 10px;
        }
        section[data-testid="stSidebar"] .st-key-score_input [data-baseweb="input"] button:hover,
        section[data-testid="stSidebar"] .st-key-rank_input [data-baseweb="input"] button:hover,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) [data-baseweb="input"] button:hover,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) [data-baseweb="input"] button:hover {
            background: linear-gradient(162deg, #5A87D3 0%, #3766B6 100%);
            color: #FFFFFF;
        }
        section[data-testid="stSidebar"] .st-key-score_input [data-baseweb="input"] button svg,
        section[data-testid="stSidebar"] .st-key-rank_input [data-baseweb="input"] button svg,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="高考分数"]) [data-baseweb="input"] button svg,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"]:has(input[aria-label="全省位次"]) [data-baseweb="input"] button svg {
            width: 20px;
            height: 20px;
        }
        section[data-testid="stSidebar"] .st-key-score_slider {
            margin-top: 0.1rem;
            margin-bottom: 0.15rem;
            padding: 0 8px;
        }
        section[data-testid="stSidebar"] .st-key-score_slider [data-baseweb="slider"] {
            padding-top: 0.2rem;
            padding-bottom: 0.2rem;
        }
        section[data-testid="stSidebar"] .st-key-score_slider [data-baseweb="slider"] > div > div {
            border-radius: 999px;
            height: 10px;
        }
        section[data-testid="stSidebar"] .st-key-score_slider [role="slider"] {
            width: 32px;
            height: 32px;
            border: 1px solid rgba(255, 255, 255, 0.95);
            background: linear-gradient(165deg, #fffdf9 0%, #f7f3ed 100%);
            box-shadow: 0 8px 18px rgba(18, 28, 44, 0.2);
        }
        .score-slider-scale {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 0.18rem 0 0.52rem;
            padding: 0 0.35rem;
            color: #8F8681;
            font-size: 0.8rem;
            letter-spacing: 0.2px;
        }
        .step-hint {
            margin-top: -0.15rem;
            margin-bottom: 0.48rem;
            font-size: 0.8rem;
            color: #6E747D;
            text-align: right;
            font-weight: 700;
        }
        .step-hint-right {
            margin-top: -0.1rem;
            margin-bottom: 0.3rem;
        }
        .plan-tag {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(70, 109, 176, 0.14);
            color: #365485;
            font-size: 0.78rem;
            font-weight: 800;
            margin-top: 6px;
        }
        .plan-intro {
            margin-top: 6px;
            color: #7A7D85;
            font-size: 0.82rem;
            line-height: 1.6;
        }
        .plan-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
        }
        .plan-meta-block {
            display: flex;
            flex-direction: column;
            gap: 3px;
            padding: 2px 0;
        }
        .plan-name {
            color: #2D333C;
            font-size: 0.9rem;
            font-weight: 800;
        }
        .plan-batch {
            font-size: 0.76rem;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(242, 244, 248, 0.92);
            border: 1px solid rgba(220, 224, 230, 0.9);
            color: #5F6872;
        }
        .plan-help {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 999px;
            border: 1px solid rgba(180, 186, 196, 0.9);
            background: #F2F3F5;
            color: #8B9098;
            font-size: 0.72rem;
            font-weight: 800;
            cursor: help;
        }
        .plan-help::after {
            content: attr(data-tip);
            position: absolute;
            left: 50%;
            bottom: 150%;
            transform: translateX(-50%);
            background: #2F3238;
            color: white;
            padding: 6px 8px;
            border-radius: 8px;
            width: 240px;
            white-space: normal;
            line-height: 1.5;
            text-align: left;
            font-size: 0.72rem;
            opacity: 0;
            pointer-events: none;
            box-shadow: 0 6px 16px rgba(0,0,0,0.18);
            z-index: 20;
        }
        .plan-help::before {
            content: "";
            position: absolute;
            left: 50%;
            bottom: 132%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: #2F3238;
            opacity: 0;
        }
        .plan-help:hover::after,
        .plan-help:hover::before {
            opacity: 1;
        }
        .plan-status {
            font-size: 0.74rem;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid transparent;
            font-weight: 800;
        }
        .plan-status-eligible {
            background: rgba(76, 134, 242, 0.12);
            color: #2E5CA9;
            border-color: rgba(76, 134, 242, 0.22);
        }
        .plan-status-pending {
            background: rgba(243, 160, 76, 0.14);
            color: #9A5B1C;
            border-color: rgba(243, 160, 76, 0.22);
        }
        .plan-status-blocked {
            background: rgba(228, 230, 235, 0.8);
            color: #7A7F88;
            border-color: rgba(210, 214, 222, 0.9);
        }
        .plan-status-mismatch {
            background: rgba(238, 111, 99, 0.10);
            color: #B14D45;
            border-color: rgba(238, 111, 99, 0.20);
        }
        .plan-status-unavailable {
            background: rgba(126, 138, 158, 0.10);
            color: #5E6775;
            border-color: rgba(126, 138, 158, 0.20);
        }
        .plan-subtext {
            color: #8A6B4D;
            font-size: 0.76rem;
            line-height: 1.5;
        }
        .plan-subtext-blocked {
            color: #8A6C6C;
        }
        .plan-subtext-mismatch {
            color: #B14D45;
        }
        .plan-subtext-unavailable {
            color: #6D7682;
        }
        .plan-toggle-placeholder {
            width: 20px;
            height: 20px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.66rem;
            font-weight: 800;
            margin-top: 5px;
        }
        .plan-toggle-pending {
            background: rgba(243, 160, 76, 0.12);
            border: 1px solid rgba(243, 160, 76, 0.28);
            color: #9A5B1C;
        }
        .plan-toggle-blocked {
            background: rgba(229, 231, 236, 0.9);
            border: 1px solid rgba(209, 214, 221, 0.95);
            color: #7A7F88;
        }
        .plan-toggle-mismatch {
            background: rgba(238, 111, 99, 0.10);
            border: 1px solid rgba(238, 111, 99, 0.20);
            color: #B14D45;
        }
        .plan-toggle-unavailable {
            background: rgba(126, 138, 158, 0.10);
            border: 1px solid rgba(126, 138, 158, 0.20);
            color: #5E6775;
        }
        .review-panel {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(236, 228, 221, 0.9);
            border-radius: 18px;
            padding: 14px 16px;
            margin-top: 10px;
            margin-bottom: 14px;
        }
        .review-title {
            font-weight: 800;
            color: #2D333C;
            margin-bottom: 6px;
        }
        .review-caption {
            color: #7A7D85;
            font-size: 0.82rem;
            margin-bottom: 8px;
        }
        .batch-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 4px;
            border-bottom: 1px dashed rgba(230, 232, 236, 0.9);
            color: #33373E;
            font-size: 0.88rem;
        }
        .batch-count {
            color: #8A9099;
            font-size: 0.78rem;
            font-weight: 700;
        }
        section[data-testid="stSidebar"] .st-key-rank_jump_down,
        section[data-testid="stSidebar"] .st-key-rank_jump_up {
            margin-top: -0.18rem;
            margin-bottom: 0.32rem;
        }
        section[data-testid="stSidebar"] .st-key-rank_jump_down button,
        section[data-testid="stSidebar"] .st-key-rank_jump_up button {
            height: 38px;
            border-radius: 999px;
            border: 1px solid rgba(110, 139, 190, 0.32);
            background: linear-gradient(155deg, rgba(197, 214, 241, 0.92) 0%, rgba(173, 196, 232, 0.88) 100%);
            color: #365485;
            font-size: 0.83rem;
            font-weight: 800;
            box-shadow: 0 7px 16px rgba(50, 81, 136, 0.18);
        }
        section[data-testid="stSidebar"] .st-key-rank_jump_down button:hover,
        section[data-testid="stSidebar"] .st-key-rank_jump_up button:hover {
            border-color: rgba(94, 124, 179, 0.38);
            background: linear-gradient(155deg, rgba(207, 221, 245, 0.98) 0%, rgba(181, 202, 236, 0.96) 100%);
            color: #2E4A79;
        }
        section[data-testid="stSidebar"] .st-key-batch_filter [data-baseweb="select"] > div {
            border-radius: 999px;
            border: 1px solid rgba(233, 142, 47, 0.65);
            background: linear-gradient(135deg, rgba(255, 248, 239, 0.95), rgba(255, 255, 255, 0.92));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 22px rgba(233, 142, 47, 0.16);
            padding-left: 8px;
        }
        section[data-testid="stSidebar"] .st-key-batch_filter [data-baseweb="select"] svg {
            color: #C66C18;
        }
        .glass-base {
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(255, 255, 255, 0.82);
            box-shadow: 0 20px 48px rgba(20, 24, 36, 0.06);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 28px;
        }
        .profile-wrap {
            padding: 24px;
            position: sticky;
            top: 18px;
        }
        .profile-title {
            font-size: 1.55rem;
            font-weight: 800;
            color: #1D1D1F;
            margin-bottom: 6px;
        }
        .profile-subtitle {
            color: #6A6D75;
            line-height: 1.7;
            font-size: 0.94rem;
            margin-bottom: 18px;
        }
        .portrait-box {
            background: linear-gradient(135deg, rgba(255,255,255,0.82), rgba(255,248,241,0.80));
            border: 1px solid rgba(239, 232, 226, 0.96);
            border-radius: 20px;
            padding: 15px 16px;
            margin-bottom: 12px;
        }
        .portrait-label {
            color: #7E7B78;
            font-size: 0.81rem;
            margin-bottom: 5px;
        }
        .portrait-value {
            color: #1D1D1F;
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.6;
        }
        .tag-row, .detail-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .detail-chip {
            padding: 7px 11px;
            border-radius: 999px;
            background: rgba(245, 242, 238, 0.94);
            color: #6E6258;
            border: 1px solid rgba(235, 226, 218, 0.98);
            font-size: 0.78rem;
            font-weight: 700;
        }
        .detail-chip-accent {
            background: rgba(243,160,76,0.10);
            color: #B46416;
            border-color: rgba(243,160,76,0.14);
        }
        .detail-chip-warning {
            background: rgba(231,76,60,0.10);
            color: #C64739;
            border-color: rgba(231,76,60,0.14);
        }
        .hero-panel {
            padding: 22px 24px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(243,160,76,0.10);
            border: 1px solid rgba(243,160,76,0.14);
            color: #C06E1B;
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .hero-title {
            color: #1D1D1F;
            font-size: 1.92rem;
            font-weight: 800;
            line-height: 1.22;
            margin-bottom: 8px;
            max-width: 920px;
        }
        .hero-text, .hero-query {
            color: #6A6D75;
            font-size: 0.95rem;
            line-height: 1.8;
            max-width: 980px;
        }
        .hero-query {
            margin-top: 10px;
            font-weight: 700;
            color: #5F5550;
        }
        .summary-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 12px;
        }
        .summary-card {
            padding: 16px 18px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(255,255,255,0.84);
            box-shadow: 0 14px 30px rgba(20, 24, 36, 0.05);
            backdrop-filter: blur(10px);
        }
        .summary-label { color: #7B7E86; font-size: 0.82rem; margin-bottom: 6px; }
        .summary-value { color: #1D1D1F; font-size: 1.7rem; font-weight: 800; margin-bottom: 4px; }
        .summary-note { color: #6A6D75; font-size: 0.84rem; line-height: 1.6; }
        .threshold-strip {
            padding: 13px 18px;
            margin-bottom: 14px;
            color: #695F58;
            font-size: 0.88rem;
            line-height: 1.7;
        }
        .policy-panel {
            padding: 20px 22px;
            margin-bottom: 16px;
        }
        .policy-panel-empty {
            border: 1px dashed rgba(191, 197, 205, 0.92);
            background: linear-gradient(180deg, rgba(249, 250, 251, 0.98), rgba(243, 245, 247, 0.96));
            box-shadow: 0 16px 36px rgba(30, 35, 44, 0.05);
        }
        .policy-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
        }
        .policy-empty-title {
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: 1px;
            color: #8D949E;
            text-align: center;
            margin: 4px 0 10px;
        }
        .policy-empty-text {
            color: #9AA1AA;
            font-size: 0.98rem;
            line-height: 1.8;
            text-align: center;
            max-width: 680px;
            margin: 0 auto;
        }
        .policy-panel-title {
            font-size: 1.12rem;
            font-weight: 800;
            color: #1D1D1F;
            margin-bottom: 4px;
        }
        .policy-panel-subtitle {
            color: #6A6D75;
            font-size: 0.88rem;
            line-height: 1.7;
            max-width: 880px;
        }
        .policy-counter {
            background: rgba(243,160,76,0.10);
            border: 1px solid rgba(243,160,76,0.14);
            color: #B6681D;
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.8rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .policy-section {
            margin-top: 14px;
        }
        .policy-section-label {
            color: #7A6A5F;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .vol-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(255,255,255,0.86);
            box-shadow: 0 18px 42px rgba(20, 24, 36, 0.06);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .card-top-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 16px;
        }
        .title-area {
            min-width: 0;
        }
        .bucket-pill {
            display: inline-flex;
            align-items: center;
            padding: 7px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            border: 1px solid;
            margin-bottom: 10px;
        }
        .card-school {
            font-size: 1.14rem;
            font-weight: 800;
            color: #1D1D1F;
            margin-bottom: 6px;
        }
        .card-meta {
            color: #74767D;
            font-size: 0.88rem;
        }
        .prob-box {
            min-width: 124px;
            text-align: right;
            border: 1px solid rgba(236, 228, 221, 0.90);
            border-radius: 18px;
            padding: 12px 14px;
        }
        .prob-label { color: #7B7E86; font-size: 0.78rem; margin-bottom: 4px; }
        .prob-value { color: #1D1D1F; font-size: 1.38rem; font-weight: 800; }
        .prob-tag { font-size: 0.82rem; font-weight: 700; }
        .content-grid {
            display: grid;
            grid-template-columns: 1.15fr 0.9fr 0.9fr;
            gap: 14px;
            align-items: stretch;
        }
        .info-column, .chart-column {
            min-width: 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }
        .mini-metric {
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(241, 235, 230, 0.94);
            border-radius: 16px;
            padding: 12px;
        }
        .mini-metric-label { color: #7B7E86; font-size: 0.78rem; margin-bottom: 4px; }
        .mini-metric-value { color: #1D1D1F; font-size: 1rem; font-weight: 800; }
        .reason-title {
            color: #7A6A5F;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 8px;
            margin-top: 2px;
        }
        .reason-box {
            background: rgba(254, 252, 249, 0.92);
            border: 1px solid rgba(241, 235, 230, 0.92);
            color: #303239;
            border-radius: 18px;
            padding: 14px 16px;
            line-height: 1.75;
            font-size: 0.91rem;
            margin-bottom: 12px;
        }
        .reason-hint {
            margin-top: 8px;
            color: #8A6F5E;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .rank-badge {
            display: inline-flex;
            align-items: center;
            margin-left: 8px;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(124, 59, 255, 0.12);
            color: #5A2FCC;
            font-size: 0.72rem;
            font-weight: 800;
        }
        .empty-panel {
            background: rgba(255, 255, 255, 0.82);
            border: 1px dashed rgba(233, 142, 47, 0.25);
            border-radius: 20px;
            padding: 20px 22px;
            color: #5F5550;
            margin-bottom: 16px;
            box-shadow: 0 12px 28px rgba(20, 24, 36, 0.05);
        }
        .empty-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #1D1D1F;
            margin-bottom: 6px;
        }
        .empty-text {
            font-size: 0.9rem;
            line-height: 1.7;
            margin-bottom: 6px;
        }
        .empty-panel ul {
            margin: 0.35rem 0 0 1.1rem;
            color: #7A6A5F;
            font-size: 0.84rem;
        }
        .cv-note {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid;
            border-radius: 16px;
            padding: 12px 14px;
        }
        .cv-note-badge {
            display: inline-flex;
            align-items: center;
            color: white;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .cv-note-text {
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.6;
        }
        .chart-box {
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(241, 235, 230, 0.92);
            border-radius: 18px;
            padding: 14px;
            height: 100%;
        }
        .chart-title { color: #2B2C31; font-size: 0.88rem; font-weight: 800; margin-bottom: 8px; }
        .chart-caption { color: #7A7D85; font-size: 0.8rem; margin-top: 4px; line-height: 1.6; }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            margin-bottom: 0.75rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.60);
            border: 1px solid rgba(236, 228, 221, 0.84);
            border-radius: 999px;
            padding: 10px 18px;
            height: auto;
            box-shadow: 0 8px 20px rgba(20, 24, 36, 0.03);
        }
        .stTabs [aria-selected="true"] {
            background: rgba(255,255,255,0.92);
            color: #1D1D1F;
            box-shadow: 0 14px 26px rgba(20, 24, 36, 0.05);
        }
        .stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(243,160,76,0.18);
            background: linear-gradient(135deg, #F3A04C 0%, #E98E2F 100%);
            color: white;
            font-weight: 800;
            box-shadow: 0 14px 28px rgba(233, 142, 47, 0.24);
        }
        .stButton > button:hover {
            border-color: rgba(243,160,76,0.28);
            color: white;
        }
        @media (max-width: 1250px) {
            .content-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 1100px) {
            .summary-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
initialize_sidebar_state()

with st.sidebar:
    st.header("考生信息录入")
    st.slider(
        "高考分数滑块",
        min_value=0,
        max_value=750,
        step=1,
        key="score_slider",
        on_change=sync_score_from_slider,
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="score-slider-scale"><span>0</span><span>300</span><span>600</span><span>750</span></div>',
        unsafe_allow_html=True,
    )
    score = st.number_input("高考分数", min_value=0, max_value=750, step=1, key="score_input", on_change=sync_score_from_input)
    st.markdown('<div class="step-hint">±1 精确步进</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-hint step-hint-right">±1000 快速步进</div>', unsafe_allow_html=True)
    rank_jump_cols = st.columns(2, gap="small")
    with rank_jump_cols[0]:
        st.button("-1000", key="rank_jump_down", use_container_width=True, on_click=adjust_rank, args=(-1000,))
    with rank_jump_cols[1]:
        st.button("+1000", key="rank_jump_up", use_container_width=True, on_click=adjust_rank, args=(1000,))
    rank = st.number_input("全省位次", min_value=0, step=1, key="rank_input")

    batch_filter = st.selectbox(
        "批次筛选",
        BATCH_FILTER_OPTIONS,
        index=0,
        key="batch_filter",
    )

    st.caption("以下继续补充选科、户籍和地区信息，用于选科过滤与政策规则识别。")
    track = st.radio("首选科类", ["物理", "历史"], horizontal=True)
    subjects = st.multiselect(
        "再选科目（四选二）",
        ["化学", "生物", "地理", "政治"],
        max_selections=2,
        placeholder="请选择两门",
    )
    city = st.selectbox("户籍所在市州", list(GANSU_CITY_COUNTIES.keys()))
    region = st.selectbox("户籍所在区县", GANSU_CITY_COUNTIES[city])
    hukou = st.radio("户籍性质", ["urban", "rural_only"], horizontal=True, format_func=format_hukou)
    nation_choice = st.selectbox("民族", NATION_OPTIONS, index=0)
    if nation_choice == NATION_OTHER_LABEL:
        nation_custom = st.text_input("其他民族", value="")
        nation = nation_custom.strip() or nation_choice
    else:
        nation = nation_choice
    is_registered = st.checkbox("是否建档立卡")
    st.button("挖掘政策红利", use_container_width=True, on_click=toggle_policy_panel)

    school_years = 3
    hukou_years = 3
    parent_hukou_years = 3

    review_values = collect_review_values()
    current_profile = build_current_profile(
        track=track,
        subjects=subjects,
        score=int(score),
        rank=int(rank),
        region=region,
        hukou=hukou,
        nation=nation,
        school_years=int(school_years),
        hukou_years=int(hukou_years),
        parent_hukou_years=int(parent_hukou_years),
        is_registered=is_registered,
        parent_region=review_values.get("parent_region"),
        school_region=review_values.get("school_region"),
        parent_has_local_hukou=review_values.get("parent_has_local_hukou"),
        graduated_in_region_school=review_values.get("graduated_in_region_school"),
        special_review_passed=review_values.get("special_review_passed"),
        special_identity=review_values.get("special_identity"),
        has_ethnic_language_score=review_values.get("has_ethnic_language_score"),
        previous_special_plan_breach=review_values.get("previous_special_plan_breach"),
    )

    selected_plan_tags: list[str] = []
    if st.session_state.show_policy_panel:
        st.markdown("---")
        status_by_group, missing_by_group, reason_by_group = build_group_status(current_profile)
        pending_fields = {
            field
            for group_name, status in status_by_group.items()
            if status == "pending"
            for field in missing_by_group.get(group_name, set())
        }

        st.markdown(
            '<div class="review-panel">'
            '<div class="review-title">资格审查</div>'
            '<div class="review-caption">为避免字段闪动，审查项已固定展示；请补全"未确认"字段后再勾选计划类型。</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.selectbox("父母是否本地户籍", BOOL_REVIEW_OPTIONS, key="review_parent_has_local_hukou")
        parent_city = st.selectbox(
            "父母户籍城市",
            ["未选择", *GANSU_CITY_COUNTIES.keys()],
            key="review_parent_city",
        )
        parent_regions = ["未选择"]
        if parent_city in GANSU_CITY_COUNTIES:
            parent_regions = ["未选择", *GANSU_CITY_COUNTIES[parent_city]]
        if st.session_state.get("review_parent_region") not in parent_regions:
            st.session_state.review_parent_region = "未选择"
        st.selectbox("父母户籍区县", parent_regions, key="review_parent_region")

        school_city = st.selectbox(
            "学籍城市",
            ["未选择", *GANSU_CITY_COUNTIES.keys()],
            key="review_school_city",
        )
        school_regions = ["未选择"]
        if school_city in GANSU_CITY_COUNTIES:
            school_regions = ["未选择", *GANSU_CITY_COUNTIES[school_city]]
        if st.session_state.get("review_school_region") not in school_regions:
            st.session_state.review_school_region = "未选择"
        st.selectbox("学籍区县", school_regions, key="review_school_region")

        st.selectbox("是否在本地学校就读", BOOL_REVIEW_OPTIONS, key="review_graduated_in_region_school")
        st.selectbox("专项资格审核是否通过", BOOL_REVIEW_OPTIONS, key="review_special_review_passed")
        st.selectbox("专项身份", list(SPECIAL_IDENTITY_OPTIONS.keys()), key="review_special_identity")
        st.selectbox("是否有民族语成绩", BOOL_REVIEW_OPTIONS, key="review_has_ethnic_language_score")
        st.selectbox("是否存在专项计划失信", BOOL_REVIEW_OPTIONS, key="review_previous_special_plan_breach")

        review_values = collect_review_values()
        current_profile = build_current_profile(
            track=track,
            subjects=subjects,
            score=int(score),
            rank=int(rank),
            region=region,
            hukou=hukou,
            nation=nation,
            school_years=int(school_years),
            hukou_years=int(hukou_years),
            parent_hukou_years=int(parent_hukou_years),
            is_registered=is_registered,
            parent_region=review_values.get("parent_region"),
            school_region=review_values.get("school_region"),
            parent_has_local_hukou=review_values.get("parent_has_local_hukou"),
            graduated_in_region_school=review_values.get("graduated_in_region_school"),
            special_review_passed=review_values.get("special_review_passed"),
            special_identity=review_values.get("special_identity"),
            has_ethnic_language_score=review_values.get("has_ethnic_language_score"),
            previous_special_plan_breach=review_values.get("previous_special_plan_breach"),
        )
        status_by_group, missing_by_group, reason_by_group = build_group_status(current_profile)
        pending_fields = {
            field
            for group_name, status in status_by_group.items()
            if status == "pending"
            for field in missing_by_group.get(group_name, set())
        }

        st.subheader("计划类型选择")
        st.caption("系统会识别当前考生可能可报的计划类型；只有与当前批次匹配且通过资格审查的计划才能勾选，右侧"政策红利"仅展示对应计划志愿。")
        st.button("清空计划筛选", key="clear_plan_filters", on_click=clear_plan_selections, use_container_width=True)

        eligible_count = 0
        for group_name in PLAN_GROUP_ORDER:
            raw_batch = PLAN_GROUP_BATCH.get(group_name, "")
            batch = format_group_batch_display(group_name)
            intro = PLAN_GROUP_INTRO.get(group_name, "专项计划匹配后给予政策加权展示。")
            status = status_by_group.get(group_name, "blocked")
            has_recommendation_data = group_has_recommendation_data(group_name)
            data_notice = build_group_data_notice(group_name)
            batch_compatible = plan_group_matches_selected_batch(group_name, batch_filter)
            reason_items = reason_by_group.get(group_name, [])
            reason_text = ""
            if not has_recommendation_data:
                reason_text = data_notice
            elif not batch_compatible:
                reason_text = f"当前批次为{batch_filter}，该计划可推荐批次为{batch or '其他批次'}。"
            elif status == "pending" and reason_items:
                reason_text = f"待补充：{'、'.join(reason_items)}"
            elif status == "blocked" and reason_items:
                reason_text = f"当前阻断：{'；'.join(reason_items[:2])}"
            elif data_notice:
                reason_text = data_notice
            if not has_recommendation_data:
                status_label = "暂无数据"
                status_class = "plan-status plan-status-unavailable"
            elif not batch_compatible:
                status_label = "批次不匹配"
                status_class = "plan-status plan-status-mismatch"
            else:
                status_label = "可勾选" if status == "eligible" else "待补充资格" if status == "pending" else "很遗憾..."
                status_class = (
                    "plan-status plan-status-eligible"
                    if status == "eligible"
                    else "plan-status plan-status-pending"
                    if status == "pending"
                    else "plan-status plan-status-blocked"
                )
            is_enabled = status == "eligible" and batch_compatible and has_recommendation_data
            if is_enabled:
                eligible_count += 1
            checkbox_key = f"plan_select_{group_name}"
            tip_text = intro if not reason_text else f"{intro} 当前状态：{reason_text}"
            col_check, col_meta = st.columns([0.12, 0.88], gap="small")
            with col_check:
                if is_enabled:
                    checked = st.checkbox("", key=checkbox_key)
                else:
                    if checkbox_key in st.session_state:
                        st.session_state[checkbox_key] = False
                    checked = False
                    if not has_recommendation_data:
                        placeholder_class = "plan-toggle-placeholder plan-toggle-unavailable"
                        placeholder_text = "无"
                    elif not batch_compatible:
                        placeholder_class = "plan-toggle-placeholder plan-toggle-mismatch"
                        placeholder_text = "批"
                    else:
                        placeholder_class = (
                            "plan-toggle-placeholder plan-toggle-pending"
                            if status == "pending"
                            else "plan-toggle-placeholder plan-toggle-blocked"
                        )
                        placeholder_text = "待" if status == "pending" else "禁"
                    st.markdown(f'<div class="{placeholder_class}">{placeholder_text}</div>', unsafe_allow_html=True)
            with col_meta:
                if not has_recommendation_data:
                    subtext_class = "plan-subtext plan-subtext-unavailable"
                elif not batch_compatible:
                    subtext_class = "plan-subtext plan-subtext-mismatch"
                else:
                    subtext_class = (
                        "plan-subtext"
                        if status == "pending"
                        else "plan-subtext plan-subtext-blocked"
                    )
                reason_block = (
                    f'<div class="{subtext_class}">{html.escape(reason_text)}</div>'
                    if reason_text
                    else ""
                )
                st.markdown(
                    f'<div class="plan-meta-block">'
                    f'<div class="plan-row">'
                    f'<span class="plan-name">{html.escape(group_name)}</span>'
                    f'<span class="plan-batch">{html.escape(batch or raw_batch or "-")}</span>'
                    f'<span class="{status_class}">{html.escape(status_label)}</span>'
                    f'<span class="plan-help" data-tip="{html.escape(tip_text)}">?</span>'
                    f"</div>"
                    f"{reason_block}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if checked and is_enabled:
                selected_plan_tags.append(group_name)
        if eligible_count == 0:
            if pending_fields:
                st.caption("当前仍有资格字段未确认，请优先补充审查信息。")
            else:
                st.caption("当前条件下暂无可勾选的计划类型，可继续补充地区、户籍与学籍信息。")

    current_profile.selected_plan_groups = list(dict.fromkeys(selected_plan_tags))
    live_policy_summary = summarize_policy_eligibility(current_profile)
    current_profile_generation_signature = build_profile_generation_signature(current_profile)

    run = st.button("生成推荐", type="primary", use_container_width=True, on_click=reset_result_expansions)

profile_snapshot = build_profile_snapshot(
    track=track,
    subjects=subjects,
    score=int(score),
    rank=int(rank),
    region=region,
    hukou=hukou,
    nation=nation,
    school_years=int(school_years),
)

result = st.session_state.get("generated_result")
profile = current_profile if result else None
policy_summary: dict[str, list[str] | int] | None = st.session_state.get("generated_policy_summary") or live_policy_summary
blocking_errors: list[str] = []
warnings: list[str] = []
error_message: str | None = None
stored_profile_generation_signature = st.session_state.get("generated_profile_generation_signature")
results_need_refresh = bool(result) and stored_profile_generation_signature != current_profile_generation_signature

if run:
    profile = current_profile

    form_errors = validate_form(subjects, int(rank), int(score))
    blocking_errors = [message for message in form_errors if "必须" in message or "请选择" in message]
    warnings = [message for message in form_errors if message not in blocking_errors]
    if not blocking_errors:
        try:
            with st.spinner("正在生成推荐结果..."):
                bundle = get_cached_recommendation_bundle(*get_recommendation_cache_args(profile))
            store_generated_bundle(profile, bundle)
            policy_summary = bundle.get("policy_summary") or live_policy_summary
            result = bundle.get("result")
            results_need_refresh = False
        except Exception as exc:
            error_message = f"推荐引擎运行失败：{exc}"

filtered_policy_count = None
batch_counts: dict[str, int] = {}
policy_view_items: list[dict] = []
policy_view_meta: dict[str, int | str] = {"mode": "empty", "strict_count": 0, "batch_count": 0}
if result:
    policy_items = result.get("results", {}).get("政策红利", [])
    policy_view_items, policy_view_meta = get_policy_view_items(policy_items, selected_plan_tags, batch_filter)
    filtered_policy_count = len(policy_view_items)
    for bucket_items in result.get("results", {}).values():
        for item in bucket_items:
            batch_label = str(item.get("batch") or "未知批次")
            batch_counts[batch_label] = batch_counts.get(batch_label, 0) + 1

st.markdown(render_hero(profile_snapshot, has_result=bool(result)), unsafe_allow_html=True)
st.markdown(render_summary_cards(result.get("summary") if result else None, filtered_policy_count), unsafe_allow_html=True)
if result:
    st.markdown(render_threshold_strip(result.get("summary")), unsafe_allow_html=True)
    st.markdown(render_policy_overview(policy_summary), unsafe_allow_html=True)

if error_message:
    st.markdown(
        render_empty_panel(
            "推荐引擎出现异常",
            "当前数据或规则文件无法完成推断，演示版将保留输入信息供检查。",
            tips=["确认 data/processed 目录存在", "检查 configs 下的政策规则是否缺失"],
        ),
        unsafe_allow_html=True,
    )
    st.error(error_message)

for message in blocking_errors:
    st.error(message)
for message in warnings:
    st.warning(message)
if result and results_need_refresh:
    st.info("左侧基础信息或计划筛选已变更，当前展示的是上次生成结果；点击"生成推荐"后即可刷新。")

if batch_counts:
    with st.sidebar:
        st.markdown("---")
        st.subheader("批次分布")
        for batch_name, count in sorted(batch_counts.items(), key=lambda x: (-x[1], x[0])):
            st.markdown(
                f'<div class="batch-row"><span>{html.escape(batch_name)}</span><span class="batch-count">({count})</span></div>',
                unsafe_allow_html=True,
            )

tabs = st.tabs(DISPLAY_BUCKETS)
for tab, bucket in zip(tabs, DISPLAY_BUCKETS):
    with tab:
        items = result.get("results", {}).get(bucket, []) if result else []
        if bucket == "政策红利":
            items = policy_view_items
        else:
            items = filter_items_by_batch(items, batch_filter)
        if not result:
            st.markdown(
                render_empty_panel(
                    "等待生成推荐",
                    "填写左侧信息并点击"生成推荐"。演示版要求必须填写位次，并选择两门再选科目。",
                    tips=["演示推荐组合：历史 + 政治/地理", "或物理 + 化学/生物", "建议填写甘肃县区信息以触发政策规则"],
                ),
                unsafe_allow_html=True,
            )
            continue
        if not items:
            if bucket == "政策红利" and selected_plan_tags:
                st.markdown(
                    render_empty_panel(
                        "当前计划下暂无匹配志愿",
                        "当前批次下，勾选计划与可检索专项志愿交集为空。",
                        tips=["切到"全部"或更换批次", "点击"清空计划筛选"", "保留资格审查条件，先看当前批次全部专项项"],
                    ),
                    unsafe_allow_html=True,
                )
            elif bucket == "政策红利":
                st.markdown(
                    """
                    <div class="empty-panel policy-panel-empty">
                        <div class="policy-empty-title">暂未发现政策红利</div>
                        <div class="policy-empty-text">当前考生画像下，暂未识别到可用专项计划，政策红利推荐暂不展示。</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    render_empty_panel(
                        "暂无匹配结果",
                        "当前条件下没有可推荐志愿，请调整位次、科类或选科组合后再试。",
                        tips=["提升/降低位次 5%-10% 后再试", "补充户籍性质、学籍年限、建档立卡信息"],
                    ),
                    unsafe_allow_html=True,
                )
            continue
        if bucket == "政策红利":
            if selected_plan_tags:
                st.caption(f"当前仅展示所选计划类型：{'、'.join(selected_plan_tags)}")
            else:
                st.caption("该分组仅展示已识别到明确专项计划命中的志愿。")

        expanded = get_bucket_preview_state(bucket)
        display_items = items if expanded else items[:PREVIEW_LIMIT]
        if len(items) > PREVIEW_LIMIT:
            if expanded:
                st.caption(f"当前已展示全部 {len(items)} 条推荐数据。")
            else:
                st.caption(f"当前先展示前 {PREVIEW_LIMIT} 条，共 {len(items)} 条推荐数据。")

        for idx, item in enumerate(display_items, start=1):
            st.markdown(
                render_card(
                    item,
                    bucket,
                    policy_summary,
                    index=idx,
                    selected_plan_tags=selected_plan_tags if bucket == "政策红利" else None,
                ),
                unsafe_allow_html=True,
            )

        if len(items) > PREVIEW_LIMIT and not expanded:
            st.button(
                "加载全部推荐数据",
                key=f"load_all_{bucket}",
                on_click=expand_bucket_results,
                args=(bucket,),
                use_container_width=True,
            )
