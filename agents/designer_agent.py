"""
designer_agent.py — 设计 Agent

职责：接收最终洞察 JSON + 图表配置，生成完整的 HTML 分析报告。
温度 0.2，风格固定（Economist 图表风格），LLM 负责内容布局，不负责样式定义。

设计规范：
- 背景：#FAFAFA，卡片白色 + 轻阴影
- 图表区：ECharts，背景 #D4E6F1，颜色 #004C64 / #009FD7
- 结论区：段落叙述，数字加粗，无分析框架子标题
- 移动友好：max-width 1080px，padding 充足
"""

import json
from string import Template

import anthropic

from config import DESIGNER_TEMP, LLM_MODEL


# ── HTML 模板（样式固定，LLM 只填内容）───────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$report_title</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "PingFang SC","Microsoft YaHei",sans-serif; background:#FAFAFA; color:#1a1a1a; }
.container { max-width:1080px; margin:0 auto; padding:40px 24px; }
.header { background:linear-gradient(135deg,#004C64,#009FD7); color:#fff; padding:40px; border-radius:12px; margin-bottom:32px; }
.header h1 { font-size:28px; font-weight:700; margin-bottom:8px; }
.header .subtitle { font-size:14px; opacity:0.85; }
.summary-card { background:#fff; border-left:4px solid #004C64; border-radius:8px; padding:24px 28px; margin-bottom:32px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.summary-card h2 { font-size:15px; color:#004C64; margin-bottom:12px; text-transform:uppercase; letter-spacing:.04em; }
.summary-card p { font-size:16px; line-height:1.8; color:#1a1a1a; }
.section { background:#fff; border-radius:12px; padding:28px; margin-bottom:24px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.section h3 { font-size:17px; font-weight:600; margin-bottom:16px; padding-bottom:10px; border-bottom:1px solid #eee; color:#004C64; }
.section p { font-size:15px; line-height:1.85; margin-bottom:12px; }
.section ol { padding-left:1.4em; }
.section ol li { font-size:15px; line-height:1.85; margin-bottom:8px; }
.chart-wrap { background:#D4E6F1; border-radius:8px; padding:8px; margin-top:16px; }
.chart-box { width:100%; height:320px; }
.data-gap { background:#FFF7E6; border:1px solid #FFD591; border-radius:8px; padding:20px 24px; margin-top:24px; }
.data-gap h4 { font-size:14px; color:#D46B08; margin-bottom:10px; }
.data-gap ul { padding-left:1.2em; }
.data-gap ul li { font-size:14px; line-height:1.7; color:#7C4A00; }
.meta { font-size:12px; color:#999; text-align:right; margin-top:40px; }
strong { color:#004C64; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="subtitle">数据分析报告 · 大脑Agent生成 · run_id: $run_id</div>
    <h1>$report_title</h1>
  </div>

  <div class="summary-card">
    <h2>Executive Summary</h2>
    <p>$executive_summary</p>
  </div>

  $findings_html

  $charts_html

  $data_gaps_html

  <div class="meta">本报告由 数据分析报告Agent 自动生成 · 结论已经 Harness 校验</div>
</div>
<script>
$charts_js
</script>
</body>
</html>
"""


def _render_findings(findings: list[dict]) -> str:
    html = ""
    for i, f in enumerate(findings, 1):
        content = f.get("content", "")
        # 数字加粗
        import re
        content = re.sub(r'(\d+\.?\d*%?pp?)', r'<strong>\1</strong>', content)
        impact = f.get("impact_pct", "")
        impact_tag = f'<span style="font-size:12px;color:#009FD7;margin-left:8px">影响:{impact}%</span>' if impact else ""
        html += f"""
  <div class="section">
    <h3>{i}. {f.get("title", f"发现{i}")}{impact_tag}</h3>
    <p>{content}</p>
  </div>"""
    return html


def _render_charts(charts: list[dict]) -> str:
    if not charts:
        return ""
    html_parts = []
    js_parts = []
    for i, c in enumerate(charts):
        cid = f"chart_{i}"
        html_parts.append(f"""
  <div class="section">
    <h3>{c.get("title", f"图表{i+1}")}</h3>
    <div class="chart-wrap"><div id="{cid}" class="chart-box"></div></div>
  </div>""")
        option_json = json.dumps(c.get("option", {}), ensure_ascii=False)
        js_parts.append(f"""
(function(){{
  var c = echarts.init(document.getElementById('{cid}'));
  c.setOption({option_json});
}})();""")
    return "".join(html_parts), "".join(js_parts)


def _render_data_gaps(gaps: list[str]) -> str:
    if not gaps:
        return ""
    items = "".join(f"<li>{g}</li>" for g in gaps)
    return f"""
  <div class="data-gap">
    <h4>数据盲点（待验证假设）</h4>
    <ul>{items}</ul>
  </div>"""


class DesignerAgent:
    """
    将最终洞察 dict + 图表 list 渲染为 HTML 报告字符串。

    Usage:
        designer = DesignerAgent()
        html = designer.render(
            final_insights=final_insights,
            charts=charts,
            run_id="run_20240517",
            question="分析2024年利润率...",
        )
        with open("report.html", "w", encoding="utf-8") as f:
            f.write(html)
    """

    def render(
        self,
        final_insights: dict,
        charts: list[dict],
        run_id: str = "",
        question: str = "",
    ) -> str:
        findings = final_insights.get("findings", [])
        gaps = final_insights.get("data_gaps", [])
        summary = final_insights.get("executive_summary", "")

        findings_html = _render_findings(findings)
        chart_result = _render_charts(charts)
        if isinstance(chart_result, tuple):
            charts_html, charts_js = chart_result
        else:
            charts_html, charts_js = chart_result, ""
        data_gaps_html = _render_data_gaps(gaps)

        title = question[:40] + "..." if len(question) > 40 else question

        html = Template(_HTML_TEMPLATE).substitute(
            report_title=title or "数据分析报告",
            run_id=run_id,
            executive_summary=summary,
            findings_html=findings_html,
            charts_html=charts_html,
            charts_js=charts_js,
            data_gaps_html=data_gaps_html,
        )
        return html
