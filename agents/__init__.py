"""
数据分析报告 Agent 套件
包含：BrainAgent / BaseFetcher / FormatterAgent / DesignerAgent
"""
from .brain_agent import BrainAgent
from .fetcher_agent import BaseFetcher, MockFetcher
from .formatter_agent import FormatterAgent
from .designer_agent import DesignerAgent

__all__ = [
    "BrainAgent",
    "BaseFetcher",
    "MockFetcher",
    "FormatterAgent",
    "DesignerAgent",
]
