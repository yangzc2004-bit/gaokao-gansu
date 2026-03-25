import streamlit as st


st.set_page_config(page_title="甘肃高考志愿推荐系统 · 深色科技预览", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, rgba(52, 120, 246, 0.16), transparent 24%),
            radial-gradient(circle at 82% 12%, rgba(0, 196, 255, 0.10), transparent 18%),
            linear-gradient(180deg, #071018 0%, #0b1220 55%, #0d1422 100%);
        color: #eef4ff;
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero-panel {
        background: linear-gradient(135deg, rgba(11, 20, 34, 0.96), rgba(15, 26, 44, 0.92));
        border: 1px solid rgba(111, 168, 255, 0.18);
        border-radius: 26px;
        padding: 28px;
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.28);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(44, 120, 255, 0.16);
        border: 1px solid rgba(93, 162, 255, 0.22);
        color: #cfe5ff;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 14px;
    }
    .hero-title {
        font-size: 2.45rem;
        font-weight: 800;
        color: #fbfdff;
        line-height: 1.14;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
    }
    .hero-subtitle {
        color: #b9c8dc;
        font-size: 1rem;
        line-height: 1.8;
        max-width: 840px;
    }
    .summary-card {
        background: rgba(13, 22, 36, 0.92);
        border: 1px solid rgba(112, 160, 235, 0.16);
        border-radius: 22px;
        padding: 18px;
        min-height: 120px;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.18);
    }
    .summary-label {
        color: #90a7c4;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    .summary-value {
        color: #f7fbff;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .summary-note {
        color: #b5c3d6;
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .section-title {
        color: #f8fbff;
        font-size: 1.14rem;
        font-weight: 700;
        margin: 12px 0 16px 0;
    }
    .result-card {
        background: linear-gradient(180deg, rgba(12, 19, 32, 0.96), rgba(14, 22, 36, 0.96));
        border: 1px solid rgba(103, 150, 230, 0.16);
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.22);
    }
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 7px 12px;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
        margin-right: 8px;
        border: 1px solid transparent;
    }
    .pill-risk {
        background: rgba(40, 110, 235, 0.18);
        color: #d7e8ff;
        border-color: rgba(92, 157, 255, 0.24);
    }
    .pill-prob {
        background: rgba(17, 146, 110, 0.16);
        color: #d7fff2;
        border-color: rgba(55, 196, 155, 0.22);
    }
    .card-title {
        color: #ffffff;
        font-size: 1.18rem;
        font-weight: 800;
        margin: 14px 0 6px 0;
    }
    .card-subtitle {
        color: #9fb1c9;
        font-size: 0.92rem;
        margin-bottom: 14px;
    }
    .reason-box {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #edf4ff;
        border-radius: 16px;
        padding: 14px 16px;
        line-height: 1.75;
        font-size: 0.94rem;
        margin-top: 14px;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-top: 12px;
    }
    .mini-stat {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 14px;
    }
    .mini-stat-label {
        color: #93a9c4;
        font-size: 0.8rem;
        margin-bottom: 6px;
    }
    .mini-stat-value {
        color: #ffffff;
        font-size: 1.08rem;
        font-weight: 700;
    }
    .hint-box {
        background: rgba(255, 184, 77, 0.12);
        border: 1px solid rgba(255, 184, 77, 0.18);
        color: #ffe5b9;
        border-radius: 16px;
        padding: 13px 15px;
        font-size: 0.9rem;
        margin-top: 14px;
        line-height: 1.7;
    }
    .sidebar-card {
        background: rgba(13, 22, 36, 0.94);
        border: 1px solid rgba(110, 155, 230, 0.14);
        border-radius: 20px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .sidebar-title {
        color: #8ea4c1;
        font-size: 0.84rem;
        margin-bottom: 8px;
    }
    .sidebar-value {
        color: #f3f8ff;
        font-size: 0.98rem;
        font-weight: 700;
        line-height: 1.7;
    }
    @media (max-width: 900px) {
        .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

summary_cards = [
    ("🔥 冲刺池", "12", "高潜力候选，适合少量布局"),
    ("🧭 稳妥池", "18", "匹配度最佳，适合作为主力"),
    ("🛡️ 保底池", "16", "安全边际充足，负责兜底"),
    ("🎯 政策红利", "7", "可优先关注的加权机会"),
]

sample_cards = {
    "冲": [
        {
            "school": "常州大学",
            "major": "国际经济与贸易",
            "meta": "本科批｜历史｜专业组 02",
            "prob": "39.1%",
            "label": "冲刺",
            "reason": "近3年历史数据较完整；当前位次略高于目标位次，存在冲刺空间；专业计划名额偏少，系统已从严评估；专项政策匹配带来一定加权。",
            "stats": [("目标位次", "4,812"), ("平均位次", "5,034"), ("CV波动", "0.0269"), ("历史年数", "3")],
            "hint": "冲刺建议适合少量布局，不建议大量占坑。",
        },
        {
            "school": "华侨大学",
            "major": "哲学",
            "meta": "本科批｜历史｜专业组 01",
            "prob": "33.4%",
            "label": "冲刺",
            "reason": "仅有2年历史数据，已保守降权；当前位次略高于目标位次，存在冲刺空间；新增专业历史样本不足，系统已保守处理。",
            "stats": [("目标位次", "4,690"), ("平均位次", "4,955"), ("CV波动", "0.0312"), ("历史年数", "2")],
            "hint": "新增专业样本少，适合保留但要谨慎。",
        },
    ],
    "稳": [
        {
            "school": "湖南工业大学",
            "major": "英语",
            "meta": "本科批｜历史｜专业组 04",
            "prob": "63.7%",
            "label": "稳妥",
            "reason": "近3年历史数据较完整；当前位次与目标位次接近，匹配度较稳；专项政策匹配带来一定加权。",
            "stats": [("目标位次", "5,182"), ("平均位次", "5,161"), ("CV波动", "0.0217"), ("历史年数", "3")],
            "hint": "这类志愿适合作为中间主力区。",
        }
    ],
    "保": [
        {
            "school": "天津外国语大学",
            "major": "经济学",
            "meta": "本科批｜历史｜专业组 03",
            "prob": "98.0%",
            "label": "保底",
            "reason": "近3年历史数据较完整；当前位次优于目标位次，安全边际较大；专业计划占比较高，录取稳定性略好。",
            "stats": [("目标位次", "6,488"), ("平均位次", "6,124"), ("CV波动", "0.0187"), ("历史年数", "3")],
            "hint": "保底建议负责兜底，优先保证可录取性。",
        }
    ],
}

with st.sidebar:
    st.markdown("### 视觉预览说明")
    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-title">预览定位</div>
            <div class="sidebar-value">纯视觉预览，不接正式业务逻辑</div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-title">风格方向</div>
            <div class="sidebar-value">深色科技面板 · 高对比信息层级 · 轻发光点缀</div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-title">为什么选这套</div>
            <div class="sidebar-value">可读性最高，最适合“推荐系统 / 决策产品”这种信息密集页面</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="hero-panel">
        <div class="hero-badge">AI 志愿推荐系统 · Dark Panel Preview</div>
        <div class="hero-title">甘肃高考志愿推荐系统</div>
        <div class="hero-subtitle">
            这一版放弃大片浅色毛玻璃，改成高对比深色科技面板。
            核心目标只有一个：让用户第一眼就看清“冲 / 稳 / 保”的差异，
            并且愿意相信这是一套严肃的 AI 决策产品。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

summary_cols = st.columns(4)
for column, card in zip(summary_cols, summary_cards):
    with column:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-label">{card[0]}</div>
                <div class="summary-value">{card[1]}</div>
                <div class="summary-note">{card[2]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

selected_tab = st.segmented_control("查看预览分区", ["冲", "稳", "保"], default="冲")

st.markdown(f"<div class='section-title'>{selected_tab}志愿结果页预览</div>", unsafe_allow_html=True)

for card in sample_cards[selected_tab]:
    stats_html = "".join(
        [
            f"<div class='mini-stat'><div class='mini-stat-label'>{label}</div><div class='mini-stat-value'>{value}</div></div>"
            for label, value in card["stats"]
        ]
    )
    st.markdown(
        f"""
        <div class="result-card">
            <span class="pill pill-risk">{selected_tab} · {card['label']}</span>
            <span class="pill pill-prob">录取概率 {card['prob']}</span>
            <div class="card-title">{card['school']} · {card['major']}</div>
            <div class="card-subtitle">{card['meta']}</div>
            <div class="stat-grid">{stats_html}</div>
            <div class="reason-box">{card['reason']}</div>
            <div class="hint-box">{card['hint']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div class='section-title'>设计说明</div>", unsafe_allow_html=True)
notes_left, notes_right = st.columns(2)
with notes_left:
    st.markdown(
        """
        - 去掉大面积低对比玻璃，改成深色实体面板
        - 重点信息全部提亮：标题、概率、风险档、关键指标
        - 保留一点科技蓝高光，增加高级感，但不干扰阅读
        """
    )
with notes_right:
    st.markdown(
        """
        - 这套更适合后续直接并入正式结果页
        - 如果你满意，我下一步就按这套重做主前端
        - 正式版还能继续补排序、筛选、详情弹层
        """
    )
