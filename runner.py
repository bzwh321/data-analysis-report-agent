"""
runner.py — 主入口，编排完整分析流程

用法：
  python runner.py --question "分析2024年各品类利润率走势" --output report.html

或在代码中调用：
  from runner import AnalysisRunner, run_demo
  runner = AnalysisRunner(fetcher=MockFetcher())
  html = runner.run("分析2024年各品类利润率走势，找出异常并归因")
"""

import argparse
import os
import time

from agents import BrainAgent, MockFetcher, FormatterAgent, DesignerAgent


class AnalysisRunner:
    """
    数据分析报告 Agent 主编排器。

    Args:
        fetcher: 取数 Agent 实例（实现 BaseFetcher 接口）
        experience_dir: 经验库目录路径
        log_dir: 运行日志根目录
        api_key: Anthropic API Key（不传则读取 ANTHROPIC_API_KEY 环境变量）
        output_path: 报告输出路径（None 则返回 HTML 字符串不写文件）
    """

    def __init__(
        self,
        fetcher=None,
        experience_dir: str = "experience/",
        log_dir: str = "run_logs/",
        api_key: str | None = None,
        output_path: str | None = None,
    ):
        self.fetcher = fetcher or MockFetcher()
        self.experience_dir = experience_dir
        self.log_dir = log_dir
        self.api_key = api_key
        self.output_path = output_path

    def run(self, question: str, context: dict | None = None) -> str:
        """
        执行完整分析流程，返回 HTML 报告字符串。

        流程：
          1. BrainAgent.run()  → final_insights dict
          2. FormatterAgent.format() → ECharts option list
          3. DesignerAgent.render() → HTML 字符串
          4. 写入文件（如果 output_path 不为 None）
        """
        run_id = f"run_{int(time.time())}"
        print(f"\n{'='*60}")
        print(f"数据分析报告Agent 启动")
        print(f"run_id: {run_id}")
        print(f"问题: {question}")
        print(f"{'='*60}")

        # Step 1: 大脑 Agent
        brain = BrainAgent(
            fetcher=self.fetcher,
            experience_dir=self.experience_dir,
            log_dir=self.log_dir,
            run_id=run_id,
            api_key=self.api_key,
        )
        final_insights = brain.run(question, context or {})

        # Step 2: 制图 Agent
        formatter = FormatterAgent(api_key=self.api_key)
        chart_instructions = final_insights.get("chart_instructions", [])
        charts = formatter.format(chart_instructions, brain.round_data)

        # Step 3: 设计 Agent → HTML
        designer = DesignerAgent()
        html = designer.render(
            final_insights=final_insights,
            charts=charts,
            run_id=run_id,
            question=question,
        )

        # Step 4: 写文件
        if self.output_path:
            os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n✅ 报告已写入：{self.output_path}")

        print(f"\n✅ 运行完成 | run_id: {run_id}")
        return html


def run_demo() -> str:
    """快速演示（使用 MockFetcher，无需真实数据库）"""
    runner = AnalysisRunner(
        fetcher=MockFetcher(),
        output_path="run_logs/demo_output/report.html",
    )
    return runner.run(
        question="分析2024年各品类利润率走势，找出年度下滑的根因并给出行动建议",
        context={
            "company": "示例零售公司",
            "date_range": {"start": "2024-01", "end": "2024-12"},
            "categories": ["家具", "技术", "办公用品"],
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据分析报告Agent")
    parser.add_argument("--question", "-q", type=str,
                        help="分析问题（留空则运行演示）")
    parser.add_argument("--output", "-o", type=str, default="report.html",
                        help="输出文件路径（默认：report.html）")
    parser.add_argument("--experience", "-e", type=str, default="experience/",
                        help="经验库目录（默认：experience/）")
    parser.add_argument("--demo", action="store_true",
                        help="运行演示模式（使用 MockFetcher）")
    args = parser.parse_args()

    if args.demo or not args.question:
        print("运行演示模式...")
        run_demo()
    else:
        runner = AnalysisRunner(
            experience_dir=args.experience,
            output_path=args.output,
        )
        runner.run(args.question)
