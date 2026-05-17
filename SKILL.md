---
name: data-analysis-report-agent
description: 数据分析报告Agent。触发条件：用户说「帮我分析数据」「做一份数据分析报告」「分析利润率/销售/品类走势」「找出异常原因」「数据归因」「跑一次数据分析」。大脑Agent（BrainAgent）主导分析决策，内置DEFINE→PLAN→REFLECT三阶段迭代，最多5轮，取数Agent执行结构化取数，全链路Harness硬校验，结论可追溯到具体数据字段，最终输出HTML报告。
runner: python runner.py
entry: D:\知识库\skills\data-analysis-report-agent\runner.py
allowed tools: Read, Write, Bash, Glob, Grep, Agent
last_verified: 2026-05-17
---

# data-analysis-report-agent — 数据分析报告Agent

## 核心定位

解决普通LLM分析的三大结构性问题：

| 问题 | 本系统的对策 |
|------|------------|
| 数据复述，无归因 | DEFINE阶段先设假设，REFLECT对照验证 |
| 结论无法追溯来源 | Harness强校验：每条finding必须有data_source |
| 推断组织原因（无数据） | 组织归因不是必须模块，无数据则跳过 |
| 不知道何时停止分析 | 硬代码停止判断（轮次/影响阈值/重叠度），非LLM自判 |

---

## 架构总览

```
Experience库（人工撰写，业务判断力唯一来源）
    ↓ 注入上下文
BrainAgent (temp=0.3)
    ├── Phase 1: 设计分析框架 → 01_framework.json
    ├── Phase 2: 迭代循环（≤5轮）
    │     DEFINE（问自己）→ 假设+判断标准
    │     PLAN  （问数据）→ Plan JSON → Harness校验
    │     ACT            → FetcherAgent执行取数
    │     REFLECT（问自己）→ 对照假设解读 → CONTINUE/PIVOT/STOP
    └── Phase 3: 整合洞察 → final_insights JSON
                ↓
    FormatterAgent (temp=0.1) → ECharts配置
    DesignerAgent  (temp=0.2) → HTML报告
```

---

## 快速调用

### 最小调用（MockFetcher演示）

```python
from runner import AnalysisRunner
from agents import MockFetcher

runner = AnalysisRunner(
    fetcher=MockFetcher(),
    output_path="output/report.html"
)
runner.run("分析2024年各品类利润率走势，找出异常并归因")
```

### 命令行

```bash
cd D:\知识库\skills\data-analysis-report-agent
python runner.py --demo                         # 演示模式
python runner.py -q "你的分析问题" -o report.html  # 自定义问题
```

### 接入真实数据源

```python
from agents.fetcher_agent import BaseFetcher

class MyFetcher(BaseFetcher):
    def fetch(self, plan: dict) -> dict:
        rows = my_db_query(plan['query_spec'])
        return {"row_count": len(rows), "fields": list(rows[0].keys()), "rows": rows}

runner = AnalysisRunner(fetcher=MyFetcher(), output_path="report.html")
runner.run("你的分析问题")
```

---

## 文件结构

```
data-analysis-report-agent/
├── SKILL.md                   ← 本文件（主索引）
├── config.py                  ← 所有参数（MAX_ROUNDS=5, MIN_IMPACT_PCT=3%）
├── runner.py                  ← 主入口
├── agents/
│   ├── brain_agent.py         ← 大脑Agent（DEFINE→PLAN→REFLECT）
│   ├── fetcher_agent.py       ← 取数Agent（BaseFetcher + MockFetcher）
│   ├── formatter_agent.py     ← 制图Agent
│   └── designer_agent.py      ← 设计Agent（HTML报告）
├── harness/
│   ├── plan_validator.py      ← Plan格式硬校验
│   ├── data_validator.py      ← 取数结果硬校验
│   └── output_validator.py    ← 结论可追溯性校验
├── experience/                ← 经验库（必须人工撰写）
│   ├── thresholds.json        ← 业务阈值
│   ├── priority_rules.md      ← 优先级逻辑
│   ├── good_summaries.md      ← 好结论范例+禁用词表
│   └── plan_schema.json       ← Plan格式Schema
├── run_logs/demo_run/         ← 5轮示例留档
├── examples/                  ← 接入示例（CSV/SQL/demo）
└── docs/                      ← 架构文档+定制指南
```

---

## 关键配置（config.py）

```python
MAX_ROUNDS         = 5      # 最大迭代轮次，到达强制收拢
MIN_IMPACT_PCT     = 3.0    # 影响<3%停止该分支
OVERLAP_THRESHOLD  = 0.80   # 与已有洞察重叠>80%停止
BRAIN_TEMP         = 0.3    # 大脑温度
FETCHER_TEMP       = 0.0    # 取数温度（确定性）
ALLOWED_STEPS      = ['trend_analysis','decomposition','attribution','risk_mining']
```

---

## 经验库维护规范

**关键原则：experience/ 目录必须由人工（领域专家）撰写，不能由LLM自动生成。**
LLM自生成经验库 = 系统退化为普通LLM分析，丧失业务判断力。

更新频率建议：
- `thresholds.json`：每季度或业务目标调整时
- `priority_rules.md`：每半年结合案例复盘
- `good_summaries.md`：出现优秀分析案例时及时沉淀

---

## 环境依赖

```
pip install anthropic
ANTHROPIC_API_KEY=your_key（环境变量）
Python 3.11+
```

---

## GitHub仓库

https://github.com/bzwh321/data-analysis-report-agent

（本地路径与GitHub保持同步，在此目录执行 `git push` 即可更新）
