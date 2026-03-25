import streamlit as st


st.set_page_config(page_title="甘肃高考志愿推荐系统 · 浅色专业预览", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 10%, rgba(85, 144, 255, 0.10), transparent 20%),
            radial-gradient(circle at 88% 8%, rgba(102, 201, 255, 0.10), transparent 16%),
            linear-gradient(180deg, #f5f8fc 0%, #eef3f9 100%);
        color: #16253a;
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero-panel {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(182, 201, 228, 0.75);
        border-radius: 26px;
        padding: 28px;
        box-shadow: 0 18px 50px rgba(50, 82, 120, 0.10);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 14px;
        border-radius: 999px;
        background: #eef5ff;
        border: 1px solid #d7e6fb;
        color: #2b5daa;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        color: #11233a;
        line-height: 1.14;
        margin-bottom: 0.55rem;
        letter-spacing: -0.03em;
    }
    .hero-subtitle {
        color: #5a708d;
        font-size: 1rem;
        line-height: 1.8;
        max-width: 860px;
    }
    .summary-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(196, 211, 232, 0.9);
        border-radius: 22px;
        padding: 18px;
        min-height: 120px;
        box-shadow: 0 14px 32px rgba(76, 101, 139, 0.08);
    }
    .summary-label {
        color: #6a7f98;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    .summary-value {
        color: #10233a;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .summary-note {
        color: #5f738b;
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .section-title {
        color: #152741;
        font-size: 1.14rem;
        font-weight: 700;
        margin: 12px 0 16px 0;
    }
    .result-card {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(196, 211, 232, 0.92);
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 18px 42px rgba(67, 93, 132, 0.08);
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
        background: #edf4ff;
        color: #2a5da9;
        border-color: #d7e7ff;
    }
    .pill-prob {
        background: #ebfbf4;
        color: #177d55;
        border-color: #cceedd;
    }
    .card-title {
        color: #10243c;
        font-size: 1.18rem;
        font-weight: 800;
        margin: 14px 0 6px 0;
    }
    .card-subtitle {
        color: #6b809a;
        font-size: 0.92rem;
        margin-bottom: 14px;
    }
    .reason-box {
        background: #f7faff;
        border: 1px solid #e1ebf6;
        color: #1d314c;
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
        background: #f9fbfe;
        border: 1px solid #e3ecf6;
        border-radius: 16px;
        padding: 14px;
    }
    .mini-stat-label {
        color: #6b819b;
        font-size: 0.8rem;
        margin-bottom: 6px;
    }
    .mini-stat-value {
        color: #10243b;
        font-size: 1.08rem;
        font-weight: 700;
    }
    .hint-box {
        background: #fff7ea;
        border: 1px solid #f5dfb5;
        color: #825b11;
        border-radius: 16px;
        padding: 13px 15px;
        font-size: 0.9rem;
        margin-top: 14px;
        line-height: 1.7;
    }
    .sidebar-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(198, 212, 232, 0.92);
        border-radius: 20px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 12px 24px rgba(67, 93, 132, 0.06);
    }
    .sidebar-title {
        color: #71849d;
        font-size: 0.84rem;
        margin-bottom: 8px;
    }
    .sidebar-value {
        color: #152741;
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
            <div class="sidebar-value">浅色极简专业风 · 清爽留白 · 高信任感</div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-title">适合谁</div>
            <div class="sidebar-value">更适合学生和家长第一次使用时的接受度</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="hero-panel">
        <div class="hero-badge">AI 志愿推荐系统 · Light Professional Preview</div>
        <div class="hero-title">甘肃高考志愿推荐系统</div>
        <div class="hero-subtitle">
            这一版走浅色极简专业风，核心感觉是干净、可信、易理解。
            它不像炫技型 AI 页面，更像一个真正可以给学生和家长长期使用的正式产品。
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
        - 强调正式感和亲和度，而不是炫技感
        - 信息密度高，但页面依然清爽，适合长时间看
        - 适合给学生、家长、老师直接看，不会有距离感
        """
    )
with notes_right:
    st.markdown(
        """
        - 这一套更适合做最终正式版首页和结果页
        - 如果你喜欢，我可以再做一版首页预览与它统一
        - 正式并入主前端时，可以保留现在的业务结构不动
        """
    )
