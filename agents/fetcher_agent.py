"""
fetcher_agent.py — 取数 Agent

职责：接收大脑 Agent 生成的 Plan JSON，执行取数，返回 data JSON。
取数 Agent 只接受 Plan JSON 格式（经 Harness 校验后传入），不接受自然语言指令。

接入自己的数据源：
  继承 BaseFetcher，实现 fetch(plan: dict) -> dict 方法。
  plan 结构见 experience/plan_schema.json。
  返回格式：
    {
      "row_count": 12,
      "fields": ["month", "profit_rate", ...],
      "rows": [{"month": "2024-01", "profit_rate": 15.2, ...}, ...]
    }

内置实现：
  MockFetcher — 基于样例零售数据的模拟取数，适合快速验证流程。
  SQLFetcher  — 基于 SQLAlchemy 的 SQL 取数（需配置 connection_string）。
"""

import json
import random
from abc import ABC, abstractmethod
from typing import Any

import anthropic

from config import FETCHER_TEMP, LLM_MODEL


# ── 抽象基类 ───────────────────────────────────────────────────────────────

class BaseFetcher(ABC):
    """
    继承此类并实现 fetch 方法，即可接入任意数据源。

    Example:
        class MyFetcher(BaseFetcher):
            def fetch(self, plan: dict) -> dict:
                # 解析 plan['query_spec']，执行你的查询逻辑
                sql = self._plan_to_sql(plan['query_spec'])
                rows = my_db.execute(sql)
                return {
                    "row_count": len(rows),
                    "fields": list(rows[0].keys()),
                    "rows": [dict(r) for r in rows],
                }
    """

    @abstractmethod
    def fetch(self, plan: dict) -> dict:
        """
        Args:
            plan: 已通过 Harness 校验的 Plan JSON dict
        Returns:
            data dict，必须包含 row_count / fields / rows
        """
        ...

    def validate_output(self, data: dict, plan: dict) -> tuple[bool, list[str]]:
        """校验取数结果是否满足 plan 的 acceptance_criteria"""
        errors = []
        criteria = plan.get('acceptance_criteria', {})

        if 'min_rows' in criteria and data.get('row_count', 0) < criteria['min_rows']:
            errors.append(
                f"row_count({data.get('row_count')}) < min_rows({criteria['min_rows']})"
            )
        required_fields = plan.get('expected_output', {}).get('required_fields', [])
        actual_fields = set(data.get('fields', []))
        missing = [f for f in required_fields if f not in actual_fields]
        if missing:
            errors.append(f"缺少必需字段：{missing}")
        if criteria.get('all_required_fields') and missing:
            errors.append("all_required_fields 校验失败")

        return len(errors) == 0, errors


# ── 模拟取数（零售场景示例）─────────────────────────────────────────────────

class MockFetcher(BaseFetcher):
    """
    内置模拟取数 Agent，用于演示和快速验证流程。
    数据场景：某零售公司 2024 年分品类利润率分析。
    品类：家具（Furniture）/ 技术（Technology）/ 办公用品（Office Supplies）
    """

    # 固定样例数据（真实业务请替换为真实数据源）
    _MONTHLY_PROFIT = {
        "家具":    [14.2, 13.8, 15.1, 14.6, 13.9, 14.5, 5.8, 6.2, 6.7, 13.1, 12.8, 11.9],
        "技术":    [13.1, 13.5, 14.2, 12.8, 13.6, 14.1, 13.3, 12.9, 13.8, 14.2, 13.1, 12.7],
        "办公用品": [18.2, 17.9, 18.5, 18.1, 17.8, 18.3, 17.6, 18.0, 18.4, 17.9, 18.2, 18.6],
    }
    _MONTHS = [f"{m}月" for m in range(1, 13)]
    _SUBCATEGORIES = {
        "技术": ["复印机", "设备", "电话"],
        "家具": ["椅子", "书架", "桌子"],
        "办公用品": ["文具", "纸张", "装订"],
    }
    _SUBCATEGORY_SHARE = {
        "复印机": [28, 27, 26, 25, 25, 24, 24, 23, 23, 22, 22, 21],
        "设备":   [38, 38, 39, 39, 40, 40, 40, 41, 41, 42, 42, 43],
        "电话":   [34, 35, 35, 36, 35, 36, 36, 36, 36, 36, 36, 36],
    }

    def fetch(self, plan: dict) -> dict:
        step = plan.get('analytical_step', '')
        spec = plan.get('query_spec', {})
        filters = spec.get('filters', {})
        category = filters.get('category')
        metrics = spec.get('metrics', [])
        group_by = spec.get('group_by', [])

        if step == 'trend_analysis':
            return self._trend_analysis(metrics, group_by)
        elif step == 'decomposition':
            return self._decomposition(metrics, group_by)
        elif step == 'attribution':
            return self._attribution(category, metrics, group_by)
        elif step == 'risk_mining':
            return self._risk_mining(category, metrics, group_by)
        else:
            return {"row_count": 0, "fields": [], "rows": [], "error": f"未知 step: {step}"}

    def _trend_analysis(self, metrics: list, group_by: list) -> dict:
        rows = []
        for cat, monthly in self._MONTHLY_PROFIT.items():
            annual_2024 = round(sum(monthly) / 12, 2)
            annual_2023 = round(annual_2024 + random.uniform(0.2, 1.5), 2)
            rows.append({
                "category": cat,
                "profit_rate_2024": annual_2024,
                "profit_rate_2023": annual_2023,
                "pp_change": round(annual_2024 - annual_2023, 2),
                "yoy_growth_gmv": round(random.uniform(8, 22), 1),
            })
        return {
            "row_count": len(rows),
            "fields": ["category", "profit_rate_2024", "profit_rate_2023",
                       "pp_change", "yoy_growth_gmv"],
            "rows": rows,
        }

    def _decomposition(self, metrics: list, group_by: list) -> dict:
        rows = []
        for cat, monthly in self._MONTHLY_PROFIT.items():
            annual = round(sum(monthly) / 12, 2)
            q3 = round(sum(monthly[6:9]) / 3, 2)
            other = round((sum(monthly[:6]) + sum(monthly[9:])) / 9, 2)
            rows.append({
                "category": cat,
                "profit_rate_annual": annual,
                "profit_rate_q3": q3,
                "profit_rate_non_q3": other,
                "q3_contribution_pct": round(abs(q3 - other) / max(abs(annual - other), 0.01) * 100, 1),
            })
        return {
            "row_count": len(rows),
            "fields": ["category", "profit_rate_annual", "profit_rate_q3",
                       "profit_rate_non_q3", "q3_contribution_pct"],
            "rows": rows,
        }

    def _attribution(self, category: str, metrics: list, group_by: list) -> dict:
        cat = category or "家具"
        monthly = self._MONTHLY_PROFIT.get(cat, self._MONTHLY_PROFIT["家具"])
        rows = []
        for i, m in enumerate(self._MONTHS):
            pr_2023 = round(monthly[i] + random.uniform(0.5, 2.0), 2)
            rows.append({
                "month": m,
                "profit_rate_2024": monthly[i],
                "profit_rate_2023": pr_2023,
                "pp_change": round(monthly[i] - pr_2023, 2),
            })
        return {
            "row_count": 12,
            "fields": ["month", "profit_rate_2024", "profit_rate_2023", "pp_change"],
            "rows": rows,
        }

    def _risk_mining(self, category: str, metrics: list, group_by: list) -> dict:
        cat = category or "技术"
        subcats = self._SUBCATEGORIES.get(cat, [])
        rows = []
        for sub in subcats:
            shares = self._SUBCATEGORY_SHARE.get(sub, [30] * 12)
            rows.append({
                "subcategory": sub,
                "share_q1_2023": shares[0],
                "share_q4_2024": shares[-1],
                "share_change_pp": shares[-1] - shares[0],
                "trend": "下行" if shares[-1] < shares[0] else "上行",
            })
        return {
            "row_count": len(rows),
            "fields": ["subcategory", "share_q1_2023", "share_q4_2024",
                       "share_change_pp", "trend"],
            "rows": rows,
        }


# ── SQL 取数（生产环境接入示例）────────────────────────────────────────────

class LLMAssistedFetcher(BaseFetcher):
    """
    使用 LLM 将 Plan JSON 转化为 SQL，然后在真实数据库执行。
    适用于数据库 schema 复杂、无法写死映射关系的场景。

    Usage:
        fetcher = LLMAssistedFetcher(
            schema_description="表 sales: date, category, subcategory, revenue, cost, profit...",
            connection_string="postgresql://user:pwd@host/db"
        )
    """

    def __init__(self, schema_description: str, connection_string: str,
                 api_key: str | None = None):
        self.schema_description = schema_description
        self.connection_string = connection_string
        self.client = anthropic.Anthropic(api_key=api_key)

    def _plan_to_sql(self, plan: dict) -> str:
        prompt = (
            f"数据库 Schema：\n{self.schema_description}\n\n"
            f"Plan：\n{json.dumps(plan, ensure_ascii=False)}\n\n"
            "请生成 SQL 查询，只输出 SQL，不要解释。"
        )
        resp = self.client.messages.create(
            model=LLM_MODEL,
            max_tokens=1024,
            temperature=FETCHER_TEMP,
            messages=[{"role": "user", "content": prompt}],
        )
        sql = resp.content[0].text.strip()
        # 移除 markdown 代码块标记
        sql = sql.replace('```sql', '').replace('```', '').strip()
        return sql

    def fetch(self, plan: dict) -> dict:
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            raise ImportError("需要安装 sqlalchemy：pip install sqlalchemy")

        sql = self._plan_to_sql(plan)
        engine = create_engine(self.connection_string)
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(r._mapping) for r in result]

        if not rows:
            return {"row_count": 0, "fields": [], "rows": []}
        return {
            "row_count": len(rows),
            "fields": list(rows[0].keys()),
            "rows": rows,
        }
