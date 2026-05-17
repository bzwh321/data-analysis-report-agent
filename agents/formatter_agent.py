"""
formatter_agent.py — 制图 Agent

职责：接收大脑 Phase 3 输出的 chart_instructions，生成 ECharts 配置 JSON。
温度 0.1，输出必须是合法 JSON，供设计 Agent 嵌入 HTML 报告。
"""

import json
import re
from typing import Any

import anthropic

from config import FORMATTER_TEMP, LLM_MODEL


_FORMATTER_SYSTEM = """你是图表配置专家，只输出 ECharts option JSON，不输出任何说明文字。

ECharts 规则（必须遵守）：
1. markArea / markLine 必须放在 series 数组的某个 item 内部，绝对不能放在 option 顶层
2. 颜色方案：主色 #004C64，辅色 #009FD7，背景 #D4E6F1，警示 #D4380D
3. 所有数值标注直接在图上，不依赖 legend hover
4. 输出只有一个 JSON 对象，对应单个图表的 option

Example markLine 结构（正确）：
{
  "series": [
    {
      "name": "利润率",
      "type": "bar",
      "data": [...],
      "markLine": {
        "silent": true,
        "data": [{"yAxis": 10, "name": "干预线"}],
        "lineStyle": {"color": "#D4380D", "type": "dashed"}
      }
    }
  ]
}
"""


class FormatterAgent:
    """
    将 chart_instructions 列表转化为 ECharts option JSON 列表。

    Usage:
        formatter = FormatterAgent()
        charts = formatter.format(
            chart_instructions=final_insights["chart_instructions"],
            data=round_data,
        )
        # charts: list of ECharts option dicts
    """

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key)

    def format(self, chart_instructions: list[dict], data: dict[str, Any]) -> list[dict]:
        charts = []
        for inst in chart_instructions:
            option = self._generate_one(inst, data)
            if option:
                charts.append({"title": inst.get("title", ""), "option": option})
        return charts

    def _generate_one(self, instruction: dict, data: dict) -> dict | None:
        # 找到对应轮次数据
        relevant_data = {}
        for key, val in data.items():
            if isinstance(val, dict) and 'rows' in val:
                relevant_data[key] = val['rows'][:20]  # 限制数据量

        prompt = (
            f"图表需求：{json.dumps(instruction, ensure_ascii=False)}\n"
            f"可用数据（取前20行）：{json.dumps(relevant_data, ensure_ascii=False)}\n\n"
            "请输出该图表的 ECharts option JSON。"
        )
        try:
            resp = self.client.messages.create(
                model=LLM_MODEL,
                max_tokens=2048,
                temperature=FORMATTER_TEMP,
                system=_FORMATTER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            # 提取 JSON
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if m:
                raw = m.group(1).strip()
            return json.loads(raw)
        except Exception as e:
            print(f"  [Formatter] 图表生成失败：{instruction.get('title')} | {e}")
            return None
