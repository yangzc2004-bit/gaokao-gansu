import html
import math
import sys
from pathlib import Path

# Ensure project root is in sys.path (needed for Streamlit Cloud)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from backend.models.schemas import UserProfile
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
    return f"{int(value):,}"


def format_hukou(value: str) -> str:
    return "农村户籍" if value == "rural_only" else "不限"


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
            <div class="portrait-label">民族 / 连续学籍年限</div>
            <div class="portrait-value">{html.escape(nation_text)} ｜ {snapshot['school_years']} 年</div>
        </div>
        <div class="tag-row">{tags_html}</div>
    </div>
    """


def render_hero(profile_snapshot: dict[str, str | int | list[str]], has_result: bool) -> str:
    title = "甘肃高考志愿推荐系统 · 毕业设计演示版"
    text = (
        "本页重点展示位次预测、风险分层与政策规则结构化挖掘的联动效果，可直接用于论文演示与答辩讲解。"
        if has_result
        else "先在左侧填写考生信息并点击“生成推荐”，右侧将展示冲 / 稳 / 保 / 政策红利结果，并给出推荐依据。"
    )
    badge = "Thesis Demo · Policy Mining + Rank-Based Recommendation"
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


def render_summary_cards(summary: dict | None) -> str:
    counts = (summary or {}).get("counts", {}) if summary else {}
    cards: list[str] = []
    for bucket in ["冲", "稳", "保", "政策红利"]:
        meta = RISK_META[bucket]
        count_value = counts.get(bucket, "—") if summary else "—"
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


def render_policy_overview(policy_summary: dict[str, list[str] | int] | None) -> str:
    if not policy_summary:
        return ""

    eligible_plans = policy_summary.get("eligible_plans", [])
    hit_reasons = policy_summary.get("hit_reasons", [])
    miss_reasons = policy_summary.get("miss_reasons", [])
    blocked_plan_count = policy_summary.get("blocked_plan_count", 0)

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
            <div class="policy-section-label">命中依据</div>
            <div class="detail-row">{hit_html}</div>
        </div>
        <div class="policy-section">
            <div class="policy-section-label">未命中的高频原因</div>
            <div class="detail-row">{miss_html or detail_chip('当前输入下无明显限制项', 'default')}</div>
        </div>
    </div>
    """


def render_card(item: dict, bucket: str, policy_summary: dict[str, list[str] | int] | None = None) -> str:
    meta = RISK_META[bucket]
    score = item.get("score", {})
    history = item.get("history", {})
    plan = item.get("plan", {})
    cv_value = score.get("rank_cv")
    cv_status = cv_meta(cv_value)
    trend_chart = sparkline_svg(build_trend_values(item), meta["main"])
    cv_chart = smooth_curve_svg(build_cv_values(item), cv_status["color"])
    metrics = "".join(
        [
            metric_block("录取概率", format_probability(score.get("admission_probability"))),
            metric_block("目标位次", format_int(score.get("target_rank"))),
            metric_block("平均位次", format_int(history.get("avg_rank_3y"))),
            metric_block("历史年数", format_int(history.get("years_available"))),
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
    policy_hits = [] if not policy_summary else list(policy_summary.get("eligible_plans", []))[:4]
    policy_chips = "".join(detail_chip(f"命中政策：{plan_name}", "accent") for plan_name in policy_hits)
    reason_title = "推荐理由（含政策与风险解释）"
    return f"""
    <div class="vol-card">
        <div class="card-top-row">
            <div class="title-area">
                <span class="bucket-pill" style="background:{meta['soft']}; color:{meta['main']}; border-color:{meta['soft']};">{meta['emoji']} {html.escape(bucket)}</span>
                <div class="card-school">{html.escape(item.get('school_name') or '未知院校')} · {html.escape(item.get('major_name') or '未知专业')}</div>
                <div class="card-meta">{html.escape(item.get('batch') or '-')}｜{html.escape(item.get('group_name') or '-')}｜{html.escape(meta['label'])}建议</div>
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
                <div class="reason-box">{html.escape(item.get('recommend_reason') or '-')}</div>
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
        .policy-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
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

with st.sidebar:
    st.header("考生信息录入")
    st.caption("用于演示政策规则结构化判定、位次匹配与冲稳保推荐结果。")
    track = st.radio("首选科类", ["物理", "历史"], horizontal=True)
    subjects = st.multiselect(
        "再选科目（四选二）",
        ["化学", "生物", "地理", "政治"],
        max_selections=2,
        placeholder="请选择两门",
    )
    score = st.number_input("高考分数", min_value=0, max_value=750, value=0)
    rank = st.number_input("全省位次", min_value=0, value=0)
    region = st.text_input("户籍所在县/区")
    hukou = st.selectbox("户籍性质", ["rural_only", "any"], format_func=format_hukou)
    nation = st.text_input("民族", value="汉族")
    school_years = st.number_input("高中学籍连续年限", min_value=0, max_value=10, value=3)
    hukou_years = st.number_input("本人户籍连续年限", min_value=0, max_value=10, value=3)
    parent_hukou_years = st.number_input("监护人户籍连续年限", min_value=0, max_value=10, value=3)
    is_registered = st.checkbox("是否建档立卡")
    run = st.button("生成推荐", type="primary", use_container_width=True)

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

result = None
profile = None
policy_summary: dict[str, list[str] | int] | None = None
blocking_errors: list[str] = []
warnings: list[str] = []

if run:
    profile = UserProfile(
        track=track,
        selected_subjects=subjects,
        score=int(score) if score else None,
        rank=int(rank) if rank else None,
        region=region or None,
        hukou_nature=hukou,
        nation=nation or None,
        school_years=int(school_years),
        hukou_years=int(hukou_years),
        parent_hukou_years=int(parent_hukou_years),
        is_registered_poverty_family=is_registered,
    )

    form_errors = validate_form(subjects, int(rank), int(score))
    blocking_errors = [message for message in form_errors if "必须" in message or "请选择" in message]
    warnings = [message for message in form_errors if message not in blocking_errors]
    if not blocking_errors:
        policy_summary = summarize_policy_eligibility(profile)
        result = recommend_for_frontend(
            "data/processed/admission_records.csv",
            "data/processed/admission_metrics_long.csv",
            "configs/policy_rules.gansu.json",
            "configs/region_dict.gansu.json",
            profile,
        )

st.markdown(render_hero(profile_snapshot, has_result=bool(result)), unsafe_allow_html=True)
st.markdown(render_summary_cards(result.get("summary") if result else None), unsafe_allow_html=True)
if result:
    st.markdown(render_threshold_strip(result.get("summary")), unsafe_allow_html=True)
    st.markdown(render_policy_overview(policy_summary), unsafe_allow_html=True)

for message in blocking_errors:
    st.error(message)
for message in warnings:
    st.warning(message)

tabs = st.tabs(["冲", "稳", "保", "政策红利"])
for tab, bucket in zip(tabs, ["冲", "稳", "保", "政策红利"]):
    with tab:
        items = result.get("results", {}).get(bucket, []) if result else []
        if not result:
            st.info("填写左侧信息后点击“生成推荐”。当前版本要求必须填写位次，并选择两门再选科目。")
            st.caption("建议答辩演示优先使用：历史 + 政治/地理，或物理 + 化学/生物，并填写甘肃县区信息。")
            continue
        if not items:
            st.warning("当前没有匹配结果。建议调整位次、科类或选科组合后重试。")
            st.caption("如需突出政策挖掘亮点，优先填写县区、户籍性质、连续学籍年限与建档立卡信息。")
            continue
        if bucket == "政策红利":
            st.caption("该分组优先展示政策命中后更值得关注的志愿，用于体现政策规则结构化挖掘带来的排序提升。")
        for item in items[:10]:
            st.markdown(render_card(item, bucket, policy_summary), unsafe_allow_html=True)
