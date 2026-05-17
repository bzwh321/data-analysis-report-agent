"""
custom_fetcher_example.py — 接入自有数据源示例

展示如何继承 BaseFetcher 接入真实数据库或 CSV 文件。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from agents.fetcher_agent import BaseFetcher
from runner import AnalysisRunner


# ── 示例1：CSV 文件取数 ────────────────────────────────────────────────────

class CSVFetcher(BaseFetcher):
    """
    从 CSV 文件取数。
    CSV 要求列名：date / category / subcategory / revenue / cost / profit_rate
    """

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path, parse_dates=['date'])

    def fetch(self, plan: dict) -> dict:
        df = self.df.copy()
        spec = plan.get('query_spec', {})

        # 过滤
        filters = spec.get('filters', {})
        for col, val in filters.items():
            if col in df.columns:
                df = df[df[col] == val]

        # 日期范围
        date_range = spec.get('date_range', {})
        if date_range.get('start'):
            df = df[df['date'] >= date_range['start']]
        if date_range.get('end'):
            df = df[df['date'] <= date_range['end']]

        # 聚合（按 group_by）
        group_by = [g for g in spec.get('group_by', []) if g in df.columns]
        metrics = [m for m in spec.get('metrics', []) if m in df.columns]

        if group_by and metrics:
            df = df.groupby(group_by)[metrics].mean().reset_index()

        rows = df.to_dict('records')
        return {
            "row_count": len(rows),
            "fields": list(df.columns),
            "rows": rows,
        }


# ── 示例2：SQL 数据库取数 ──────────────────────────────────────────────────

class SimpleSQLFetcher(BaseFetcher):
    """
    直接映射 Plan 到 SQL（适合 schema 简单固定的场景）。
    比 LLMAssistedFetcher 更快更稳定，但需要手动写映射逻辑。
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def fetch(self, plan: dict) -> dict:
        from sqlalchemy import create_engine, text

        sql = self._build_sql(plan)
        engine = create_engine(self.connection_string)
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(r._mapping) for r in result]

        return {
            "row_count": len(rows),
            "fields": list(rows[0].keys()) if rows else [],
            "rows": rows,
        }

    def _build_sql(self, plan: dict) -> str:
        """根据 Plan 生成 SQL（按你的实际 schema 定制）"""
        spec = plan.get('query_spec', {})
        metrics = ", ".join(spec.get('metrics', ['profit_rate']))
        group_by = ", ".join(spec.get('group_by', ['category']))
        filters = spec.get('filters', {})
        date_range = spec.get('date_range', {})

        where_clauses = []
        if date_range.get('start'):
            where_clauses.append(f"date >= '{date_range['start']}'")
        if date_range.get('end'):
            where_clauses.append(f"date <= '{date_range['end']}'")
        for col, val in filters.items():
            where_clauses.append(f"{col} = '{val}'")

        where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return f"SELECT {group_by}, AVG({metrics}) as {metrics} FROM sales {where} GROUP BY {group_by}"


# ── 运行示例 ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 使用 CSV 文件（把路径替换为你的实际文件）
    csv_path = "examples/sample_data.csv"

    if not os.path.exists(csv_path):
        print(f"示例 CSV 不存在（{csv_path}），改用 MockFetcher 演示")
        from agents import MockFetcher
        fetcher = MockFetcher()
    else:
        fetcher = CSVFetcher(csv_path)

    runner = AnalysisRunner(
        fetcher=fetcher,
        output_path="output/custom_report.html",
    )
    runner.run("分析各品类利润率走势，找出异常并归因")
