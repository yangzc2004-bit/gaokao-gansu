"""志愿对比组件 - 横向对比 2~4 个志愿"""

import streamlit as st


def render_compare_view(selected_items: list):
    """横向对比 2~4 个志愿

    Args:
        selected_items: 志愿列表，每项为 dict，包含 school_name, major_name, score, history, recommend_reason 等字段
    """
    if len(selected_items) < 2:
        st.info("请至少选择 2 个志愿进行对比")
        return

    items = selected_items[:4]  # 最多 4 个

    if len(selected_items) > 4:
        st.warning("最多支持 4 个志愿对比，已取前 4 个")

    # 标题
    st.markdown("## 📊 志愿横向对比")

    # 横向卡片
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        score = item.get("score", {}) or {}
        history = item.get("history", {}) or {}
        with col:
            st.markdown(f"### {item.get('school_name', '未知')}")
            st.markdown(f"**专业**: {item.get('major_name', '-')}")

            prob = score.get("admission_probability", 0)
            prob_pct = prob * 100 if isinstance(prob, (int, float)) else 0
            st.markdown(f"**录取概率**: {prob_pct:.1f}%")

            st.markdown(f"**目标位次**: {score.get('target_rank', '-')}")
            st.markdown(f"**平均位次**: {history.get('avg_rank_3y', '-')}")
            st.markdown(f"**CV**: {score.get('rank_cv', '-')}")
            st.markdown(f"**推荐理由**: {item.get('recommend_reason', '-')}")

    # 表格汇总
    st.markdown("---")
    st.markdown("### 关键指标汇总")

    rows = []
    for item in items:
        score = item.get("score", {}) or {}
        history = item.get("history", {}) or {}
        prob = score.get("admission_probability", 0)
        rows.append({
            "院校": item.get("school_name", "未知"),
            "专业": item.get("major_name", "-"),
            "录取概率(%)": round(prob * 100, 1) if isinstance(prob, (int, float)) else 0,
            "目标位次": score.get("target_rank", "-"),
            "3年平均位次": history.get("avg_rank_3y", "-"),
            "CV": score.get("rank_cv", "-"),
        })

    st.table(rows)
