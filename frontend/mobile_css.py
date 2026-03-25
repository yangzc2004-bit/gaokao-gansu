"""移动端适配 CSS"""

MOBILE_CSS = """
<style>
/* ===== 移动端适配 ===== */
@media (max-width: 768px) {
    /* 摘要行单列 */
    .summary-row {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
    }

    /* 内容网格单列 */
    .content-grid {
        grid-template-columns: 1fr !important;
    }

    /* 卡片顶部行垂直排列 */
    .card-top-row {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 6px !important;
    }

    /* 标签换行 */
    .tag-row {
        flex-wrap: wrap !important;
    }

    /* 表格水平滚动 */
    .stDataFrame, .stTable {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }

    /* 侧边栏全宽 */
    [data-testid="stSidebar"] {
        min-width: 100vw !important;
    }

    /* 主区域无额外 padding */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }

    /* 对比列堆叠 */
    [data-testid="column"] {
        min-width: 100% !important;
    }

    /* 按钮全宽 */
    .stButton > button {
        width: 100% !important;
    }

    /* 字体缩小 */
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
}

/* ===== 小屏手机 ===== */
@media (max-width: 480px) {
    .summary-row {
        gap: 4px !important;
    }

    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    h1 { font-size: 1.3rem !important; }
}
</style>
"""
