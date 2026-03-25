import html
import math

import streamlit as st


st.set_page_config(page_title="甘肃高考志愿推荐系统 · 结构预览", layout="wide")


PROFILE = {
    "name": "甘肃历史类考生",
    "score": 560,
    "rank": 5000,
    "track": "历史",
    "subjects": ["政治", "地理"],
    "region": "会宁县",
    "hukou": "农村户籍",
    "school_years": 3,
    "tags": ["位次优先", "专项可加权", "本科批", "推荐模式 V2"],
}


CARDS_BY_BUCKET = {
    "冲": [
        {
            "bucket_label": "冲刺",
            "school": "常州大学",
            "major": "国际经济与贸易",
            "group": "专业组 02",
            "batch": "本科批",
            "probability": "39.1%",
            "probability_label": "中低",
            "target_rank": "4,812",
            "avg_rank": "5,034",
            "cv": 0.0269,
            "years": "3",
            "trend_values": [5320, 5140, 4980],
            "cv_values": [0.032, 0.028, 0.021],
            "reason": "近3年历史数据较完整；当前位次略高于目标位次，存在冲刺空间；专业计划名额偏少，系统已从严评估。",
        },
        {
            "bucket_label": "冲刺",
            "school": "华侨大学",
            "major": "哲学",
            "group": "专业组 01",
            "batch": "本科批",
            "probability": "33.4%",
            "probability_label": "中低",
            "target_rank": "4,690",
            "avg_rank": "4,955",
            "cv": 0.0312,
            "years": "2",
            "trend_values": [5090, 4950, 4720],
            "cv_values": [0.036, 0.031, 0.028],
            "reason": "仅有2年历史数据，已保守降权；新增专业历史样本不足，系统已保守处理。",
        },
    ],
    "稳": [
        {
            "bucket_label": "稳妥",
            "school": "湖南工业大学",
            "major": "英语",
            "group": "专业组 04",
            "batch": "本科批",
            "probability": "63.7%",
            "probability_label": "中",
            "target_rank": "5,182",
            "avg_rank": "5,161",
            "cv": 0.0217,
            "years": "3",
            "trend_values": [5240, 5190, 5050],
            "cv_values": [0.024, 0.022, 0.019],
            "reason": "近3年历史数据较完整；当前位次与目标位次接近，匹配度较稳；专项政策匹配带来一定加权。",
        },
        {
            "bucket_label": "稳妥",
            "school": "西安财经大学",
            "major": "金融学",
            "group": "专业组 03",
            "batch": "本科批",
            "probability": "61.2%",
            "probability_label": "中",
            "target_rank": "5,240",
            "avg_rank": "5,208",
            "cv": 0.0210,
            "years": "3",
            "trend_values": [5380, 5230, 5010],
            "cv_values": [0.026, 0.023, 0.021],
            "reason": "历史位次稳定，当前位次与目标位次接近，适合作为中间主力志愿。",
        },
    ],
    "保": [
        {
            "bucket_label": "保底",
            "school": "天津外国语大学",
            "major": "经济学",
            "group": "专业组 03",
            "batch": "本科批",
            "probability": "98.0%",
            "probability_label": "高",
            "target_rank": "6,488",
            "avg_rank": "6,124",
            "cv": 0.0187,
            "years": "3",
            "trend_values": [6480, 6310, 6080],
            "cv_values": [0.022, 0.019, 0.016],
            "reason": "当前位次优于目标位次，安全边际较大；专业计划占比较高，录取稳定性略好。",
        },
        {
            "bucket_label": "保底",
            "school": "兰州工业学院",
            "major": "经济与金融",
            "group": "专业组 02",
            "batch": "本科批",
            "probability": "98.5%",
            "probability_label": "高",
            "target_rank": "6,720",
            "avg_rank": "6,380",
            "cv": 0.0209,
            "years": "3",
            "trend_values": [6710, 6440, 6220],
            "cv_values": [0.025, 0.021, 0.018],
            "reason": "作为保底志愿更稳，安全边际充足，适合做最后兜底层。",
        },
    ],
    "政策红利": [
        {
            "bucket_label": "政策红利",
            "school": "西北师范大学",
            "major": "思想政治教育",
            "group": "国家专项组",
            "batch": "本科批",
            "probability": "71.5%",
            "probability_label": "较高",
            "target_rank": "5,360",
            "avg_rank": "5,420",
            "cv": 0.0203,
            "years": "3",
            "trend_values": [5490, 5380, 5390],
            "cv_values": [0.022, 0.020, 0.019],
            "reason": "专项政策适配度较高，位次匹配接近稳区，适合作为政策优先关注志愿。",
        },
        {
            "bucket_label": "政策红利",
            "school": "甘肃农业大学",
            "major": "农林经济管理",
            "group": "地方专项组",
            "batch": "本科批",
            "probability": "76.8%",
            "probability_label": "较高",
            "target_rank": "5,860",
            "avg_rank": "5,980",
            "cv": 0.0196,
            "years": "3",
            "trend_values": [6070, 5980, 5890],
            "cv_values": [0.023, 0.020, 0.016],
            "reason": "地方专项加权明显，当前位次具备一定安全边际，适合作为政策优先卡位。",
        },
    ],
}


TAB_META = {
    "冲": {"emoji": "🔥", "main": "#F3A04C", "soft": "rgba(243,160,76,0.14)", "surface": "#FFF4E8"},
    "稳": {"emoji": "🧭", "main": "#7C3BFF", "soft": "rgba(124,59,255,0.12)", "surface": "#F6F0FF"},
    "保": {"emoji": "🛡️", "main": "#10B981", "soft": "rgba(16,185,129,0.12)", "surface": "#EBFBF5"},
    "政策红利": {"emoji": "🎯", "main": "#B6681D", "soft": "rgba(243,160,76,0.12)", "surface": "#FFF7EF"},
}


def sparkline_svg(values: list[float], color: str, width: int = 240, height: int = 84) -> str:
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1
    step_x = width / max(len(values) - 1, 1)
    points: list[str] = []
    base_points = [f"0,{height}"]
    for index, value in enumerate(values):
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
        f'{dots}'
        '</svg>'
    )


def smooth_curve_svg(values: list[float], color: str, width: int = 240, height: int = 84) -> str:
    average = sum(values) / len(values)
    spread = (max(values) - min(values)) if len(values) > 1 else 0.0
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
        f'</linearGradient></defs>'
        f'<line x1="0" y1="{baseline:.1f}" x2="{width:.1f}" y2="{baseline:.1f}" stroke="{color}" stroke-opacity="0.16" stroke-width="1.4" stroke-dasharray="4 5" />'
        f'<path d="{area_path}" fill="url(#{gradient_id})" />'
        f'<path d="{line_path}" fill="none" stroke="{color}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" />'
        '</svg>'
    )


def format_cv(value: float) -> str:
    return f"{value:.4f}"


def metric_block(label: str, value: str) -> str:
    return (
        '<div class="mini-metric">'
        f'<div class="mini-metric-label">{html.escape(label)}</div>'
        f'<div class="mini-metric-value">{html.escape(value)}</div>'
        '</div>'
    )


def cv_meta(cv: float) -> dict[str, str]:
    if cv >= 0.028:
        return {
            "color": "#E74C3C",
            "soft": "#FDEDEC",
            "label": "大小年明显",
            "hint": "波动较大，建议降低排序或搭配更稳志愿。",
        }
    if cv <= 0.021:
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


def render_card(card: dict, bucket: str) -> str:
    tab = TAB_META[bucket]
    status = cv_meta(card["cv"])
    trend_chart = sparkline_svg(card["trend_values"], tab["main"])
    cv_chart = smooth_curve_svg(card["cv_values"], status["color"])
    metrics = "".join(
        [
            metric_block("录取概率", card["probability"]),
            metric_block("目标位次", card["target_rank"]),
            metric_block("平均位次", card["avg_rank"]),
            metric_block("历史年数", card["years"]),
        ]
    )
    return f"""
    <div class="vol-card">
        <div class="card-top-row">
            <div class="title-area">
                <span class="bucket-pill" style="background:{tab['soft']}; color:{tab['main']}; border-color:{tab['soft']};">{tab['emoji']} {html.escape(bucket)}</span>
                <div class="card-school">{html.escape(card['school'])} · {html.escape(card['major'])}</div>
                <div class="card-meta">{html.escape(card['batch'])}｜{html.escape(card['group'])}｜{html.escape(card['bucket_label'])}建议</div>
            </div>
            <div class="prob-box" style="background:{tab['surface']};">
                <div class="prob-label">录取概率</div>
                <div class="prob-value">{html.escape(card['probability'])}</div>
                <div class="prob-tag" style="color:{tab['main']};">{html.escape(card['probability_label'])}</div>
            </div>
        </div>
        <div class="content-grid">
            <div class="info-column">
                <div class="metric-grid">{metrics}</div>
                <div class="reason-box">{html.escape(card['reason'])}</div>
                <div class="cv-note" style="background:{status['soft']}; border-color:{status['soft']};">
                    <span class="cv-note-badge" style="background:{status['color']};">{html.escape(status['label'])}</span>
                    <span class="cv-note-text" style="color:{status['color']};">{html.escape(status['hint'])}</span>
                </div>
            </div>
            <div class="chart-column">
                <div class="chart-box">
                    <div class="chart-title">历年位次趋势图</div>
                    {trend_chart}
                    <div class="chart-caption">2023 → 2024 → 2025，线越平缓，位次越稳定</div>
                </div>
            </div>
            <div class="chart-column">
                <div class="chart-box">
                    <div class="chart-title">CV 波动曲线</div>
                    {cv_chart}
                    <div class="chart-caption">当前 CV：{format_cv(card['cv'])}｜红色提示大小年，绿色代表更平稳</div>
                </div>
            </div>
        </div>
    </div>
    """


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
        max-width: 1440px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
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
        top: 20px;
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
    .tag-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }
    .tag {
        padding: 7px 11px;
        border-radius: 999px;
        background: rgba(243,160,76,0.10);
        color: #B46416;
        border: 1px solid rgba(243,160,76,0.14);
        font-size: 0.8rem;
        font-weight: 700;
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
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.22;
        margin-bottom: 8px;
        max-width: 920px;
    }
    .hero-text {
        color: #6A6D75;
        font-size: 0.95rem;
        line-height: 1.8;
        max-width: 940px;
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
        min-width: 120px;
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

left_col, right_col = st.columns([1.0, 2.5], gap="large")

with left_col:
    tags_html = "".join([f'<span class="tag">{html.escape(tag)}</span>' for tag in PROFILE["tags"]])
    st.markdown(
        f"""
        <div class="glass-base profile-wrap">
            <div class="profile-title">考生画像</div>
            <div class="profile-subtitle">保持左侧画像区，右侧只看当前板块的志愿推荐，更接近正式结果页的使用方式。</div>
            <div class="portrait-box">
                <div class="portrait-label">考生类型</div>
                <div class="portrait-value">{html.escape(PROFILE['name'])}</div>
            </div>
            <div class="portrait-box">
                <div class="portrait-label">分数 / 位次</div>
                <div class="portrait-value">{PROFILE['score']} 分 ｜ 全省 {PROFILE['rank']}</div>
            </div>
            <div class="portrait-box">
                <div class="portrait-label">科类 / 选科</div>
                <div class="portrait-value">{html.escape(PROFILE['track'])} ｜ {'、'.join(PROFILE['subjects'])}</div>
            </div>
            <div class="portrait-box">
                <div class="portrait-label">地区 / 户籍</div>
                <div class="portrait-value">{html.escape(PROFILE['region'])} ｜ {html.escape(PROFILE['hukou'])}</div>
            </div>
            <div class="portrait-box">
                <div class="portrait-label">连续学籍年限</div>
                <div class="portrait-value">{PROFILE['school_years']} 年</div>
            </div>
            <div class="tag-row">{tags_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    st.markdown(
        """
        <div class="glass-base hero-panel">
            <div class="hero-badge">Preview · 原布局思路 + 轻微毛玻璃卡片</div>
            <div class="hero-title">右侧按板块切换展示，只看当前选中的冲 / 稳 / 保 / 政策红利志愿</div>
            <div class="hero-text">这版不再混排全部推荐，而是回到正式页的使用逻辑：点击一个板块，只显示该板块的志愿卡片。每张卡片拉成长方形，左侧放基本信息与提示，中间放历年位次趋势图，右侧放 CV 波动曲线，并用红绿提示用户大小年是否明显。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="summary-row">
            <div class="summary-card"><div class="summary-label">🔥 冲刺池</div><div class="summary-value">12</div><div class="summary-note">有机会，但波动更大，适合少量布局</div></div>
            <div class="summary-card"><div class="summary-label">🧭 稳妥池</div><div class="summary-value">18</div><div class="summary-note">匹配度较高，适合作为主力志愿</div></div>
            <div class="summary-card"><div class="summary-label">🛡️ 保底池</div><div class="summary-value">16</div><div class="summary-note">安全边际更大，适合兜底</div></div>
            <div class="summary-card"><div class="summary-label">🎯 政策红利</div><div class="summary-value">7</div><div class="summary-note">优先看专项计划与政策加成</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["冲", "稳", "保", "政策红利"])
    for tab, bucket in zip(tabs, ["冲", "稳", "保", "政策红利"]):
        with tab:
            for card in CARDS_BY_BUCKET[bucket]:
                st.markdown(render_card(card, bucket), unsafe_allow_html=True)
