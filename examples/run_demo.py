"""
run_demo.py — 快速上手演示

运行前：pip install anthropic
设置环境变量：export ANTHROPIC_API_KEY=your_key_here（Windows: set ANTHROPIC_API_KEY=...）

运行：
  python examples/run_demo.py
"""

import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner import AnalysisRunner
from agents import MockFetcher


def demo_retail_analysis():
    """演示场景：零售公司年度利润率分析"""
    print("=" * 60)
    print("演示场景：零售公司 2024 年品类利润率分析")
    print("数据源：MockFetcher（内置样例数据，无需真实数据库）")
    print("=" * 60)

    runner = AnalysisRunner(
        fetcher=MockFetcher(),
        experience_dir=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "experience"
        ),
        output_path="output/demo_report.html",
    )

    html = runner.run(
        question="分析2024年各品类利润率走势，找出年度下滑的根因，区分事件性冲击和结构性变化，给出行动建议",
        context={
            "company": "示例零售公司",
            "date_range": {"start": "2024-01", "end": "2024-12"},
            "categories": ["家具", "技术", "办公用品"],
            "analyst_note": "重点关注利润率<10%的品类和连续季度下行的子品类",
        },
    )

    print(f"\n报告已生成：output/demo_report.html（大小：{len(html):,} bytes）")
    return html


def demo_custom_question():
    """演示：使用自定义问题"""
    runner = AnalysisRunner(
        fetcher=MockFetcher(),
        output_path="output/custom_report.html",
    )
    # 替换为你自己的分析问题
    return runner.run("哪个品类存在慢性结构漂移风险？预计何时影响总量利润率？")


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    demo_retail_analysis()
