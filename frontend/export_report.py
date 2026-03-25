"""报告导出组件 - 生成自包含 HTML 推荐报告"""

from datetime import datetime


def generate_html_report(profile_snapshot: dict, results: dict, policy_summary: str = "") -> str:
    """生成 HTML 推荐报告

    Args:
        profile_snapshot: 考生画像，含 name, score, rank, province, subject_type 等
        results: 推荐结果，含 rush/stable/safe/policy_bonus 等列表
        policy_summary: 政策挖掘摘要文本

    Returns:
        完整 HTML 字符串（内联 CSS，可直接保存为 .html）
    """
    profile = profile_snapshot or {}
    results = results or {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _render_items(items, max_n=10):
        if not items:
            return "<p>暂无数据</p>"
        rows = ""
        for i, item in enumerate(items[:max_n], 1):
            score = item.get("score", {}) or {}
            prob = score.get("admission_probability", 0)
            prob_pct = round(prob * 100, 1) if isinstance(prob, (int, float)) else 0
            rows += f"""<tr>
                <td>{i}</td>
                <td>{item.get('school_name', '-')}</td>
                <td>{item.get('major_name', '-')}</td>
                <td>{prob_pct}%</td>
                <td>{score.get('target_rank', '-')}</td>
                <td>{item.get('recommend_reason', '-')}</td>
            </tr>"""
        return f"""<table>
            <thead><tr><th>#</th><th>院校</th><th>专业</th><th>录取概率</th><th>目标位次</th><th>推荐理由</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>"""

    categories = [
        ("🔴 冲刺志愿", results.get("rush", [])),
        ("🟡 稳妥志愿", results.get("stable", [])),
        ("🟢 保底志愿", results.get("safe", [])),
        ("🔵 政策红利", results.get("policy_bonus", [])),
    ]

    sections = ""
    for title, items in categories:
        sections += f"<h2>{title}</h2>\n{_render_items(items)}\n"

    policy_html = ""
    if policy_summary:
        policy_html = f"<h2>📋 政策挖掘结果</h2><div class='policy'>{policy_summary}</div>"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>高考志愿推荐报告</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif; padding: 20px; max-width: 1100px; margin: 0 auto; color: #333; background: #f9f9f9; }}
  h1 {{ text-align: center; color: #1a5276; margin-bottom: 10px; }}
  .timestamp {{ text-align: center; color: #888; margin-bottom: 30px; font-size: 14px; }}
  .profile {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 30px; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  .profile h2 {{ margin-bottom: 12px; color: #2c3e50; }}
  .profile-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }}
  .profile-grid .item {{ background: #f0f4f8; padding: 10px; border-radius: 6px; }}
  .profile-grid .label {{ font-size: 12px; color: #888; }}
  .profile-grid .value {{ font-size: 18px; font-weight: bold; color: #1a5276; }}
  h2 {{ margin: 24px 0 12px; color: #2c3e50; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 20px; }}
  th {{ background: #2c3e50; color: #fff; padding: 10px 8px; font-size: 13px; text-align: left; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #eee; font-size: 13px; }}
  tr:hover {{ background: #f5f9fc; }}
  .policy {{ background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); white-space: pre-wrap; line-height: 1.7; }}
  .footer {{ text-align: center; margin-top: 40px; color: #aaa; font-size: 12px; }}
  @media (max-width: 768px) {{
    .profile-grid {{ grid-template-columns: 1fr 1fr; }}
    table {{ font-size: 12px; }}
    th, td {{ padding: 6px 4px; }}
  }}
</style>
</head>
<body>
<h1>📄 甘肃高考志愿推荐报告</h1>
<p class="timestamp">生成时间：{timestamp}</p>

<div class="profile">
  <h2>👤 考生画像</h2>
  <div class="profile-grid">
    <div class="item"><div class="label">姓名</div><div class="value">{profile.get('name', '-')}</div></div>
    <div class="item"><div class="label">省份</div><div class="value">{profile.get('province', '甘肃')}</div></div>
    <div class="item"><div class="label">科类</div><div class="value">{profile.get('subject_type', '-')}</div></div>
    <div class="item"><div class="label">高考分数</div><div class="value">{profile.get('score', '-')}</div></div>
    <div class="item"><div class="label">省排名</div><div class="value">{profile.get('rank', '-')}</div></div>
  </div>
</div>

{sections}
{policy_html}

<div class="footer">本报告由甘肃高考志愿推荐系统自动生成，仅供参考。</div>
</body>
</html>"""
    return html
