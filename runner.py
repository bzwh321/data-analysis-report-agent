"""
runner.py — 向后兼容入口

工作流主逻辑已迁移至 workflow.py。
此文件保留 AnalysisRunner 类接口，确保现有调用代码无需修改。

推荐新代码直接使用：
  from workflow import run_workflow
  state = run_workflow("你的问题", fetcher=MockFetcher())
  html = state.report_html
"""

from agents import MockFetcher
from workflow import run_workflow, WorkflowState


class AnalysisRunner:
    """
    向后兼容包装。新代码请直接调用 workflow.run_workflow()。

    Args:
        fetcher:        取数 Agent 实例（默认 MockFetcher）
        experience_dir: 经验库目录
        log_dir:        运行日志根目录
        api_key:        Anthropic API Key
        output_path:    报告输出路径（None 则只返回 HTML 字符串）
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
        """执行完整分析流程，返回 HTML 报告字符串。"""
        state: WorkflowState = run_workflow(
            question=question,
            context=context or {},
            fetcher=self.fetcher,
            experience_dir=self.experience_dir,
            log_dir=self.log_dir,
            output_path=self.output_path,
            api_key=self.api_key,
        )
        return state.report_html


def run_demo() -> str:
    """快速演示（MockFetcher，无需真实数据库）"""
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
    import argparse
    parser = argparse.ArgumentParser(description="数据分析报告Agent（兼容入口）")
    parser.add_argument("--question", "-q", type=str, help="分析问题")
    parser.add_argument("--output", "-o", type=str, default="report.html", help="输出文件路径")
    parser.add_argument("--demo", action="store_true", help="运行演示模式")
    args = parser.parse_args()

    if args.demo or not args.question:
        run_demo()
    else:
        AnalysisRunner(output_path=args.output).run(args.question)
