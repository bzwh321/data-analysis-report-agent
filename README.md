# 数据分析报告 Agent

> 一个基于大脑Agent架构的自动化数据分析报告系统。不是数据复述，是假设驱动的迭代归因。

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 它解决什么问题

| 普通LLM分析 | 本系统 |
|------------|--------|
| 拿到数据，描述数据 | 先设假设，取数验证假设 |
| 结论无法追溯来源 | 每条结论追溯到具体数据字段 |
| 不知道分析到哪里停 | 硬代码停止判断（轮次/影响阈值/重叠度） |
| 推断组织原因 | 数据不支持则跳过，不编结论 |
| 一次取数定结论 | 最多5轮迭代，自动调整追问方向 |
| 无法复现分析路径 | 全过程留档，run_id唯一标识 |

---

## 架构

```
Experience库（人工撰写，业务判断力的唯一来源）
    ↓ 注入上下文
大脑Agent (temp=0.3)
    │
    ├── Phase 1  设计分析框架
    │
    ├── Phase 2  迭代循环（最多5轮）
    │     DEFINE（问自己）→ 设立假设
    │     PLAN  （问数据）→ Plan JSON → Harness校验
    │     ACT            → 取数Agent执行
    │     REFLECT（问自己）→ 对照假设解读 → CONTINUE/PIVOT/STOP
    │
    └── Phase 3  整合洞察 → final_insights JSON
                    ↓
          制图Agent (temp=0.1) + 设计Agent (temp=0.2)
                    ↓
          Harness（结论可追溯性 + 格式校验）
                    ↓
          最终报告 HTML
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install anthropic
```

### 2. 设置 API Key

```bash
# macOS / Linux
export ANTHROPIC_API_KEY=your_key_here

# Windows
set ANTHROPIC_API_KEY=your_key_here
```

### 3. 运行演示（内置样例数据，无需真实数据库）

```bash
python runner.py --demo
```

或在代码中：

```python
from runner import AnalysisRunner
from agents import MockFetcher

runner = AnalysisRunner(fetcher=MockFetcher(), output_path="report.html")
runner.run("分析2024年各品类利润率走势，找出年度下滑的根因并给出行动建议")
```

### 4. 接入真实数据源

```python
from agents.fetcher_agent import BaseFetcher
from runner import AnalysisRunner

class MyFetcher(BaseFetcher):
    def fetch(self, plan: dict) -> dict:
        spec = plan['query_spec']
        rows = my_db_query(spec)  # 你的取数逻辑
        return {"row_count": len(rows), "fields": list(rows[0].keys()), "rows": rows}

runner = AnalysisRunner(fetcher=MyFetcher(), output_path="report.html")
runner.run("你的分析问题")
```

---

## 文件结构

```
数据分析报告Agent/
├── config.py                  # 所有参数硬编码（MAX_ROUNDS=5, MIN_IMPACT_PCT=3%...）
├── runner.py                  # 主入口，编排完整流程
│
├── agents/
│   ├── brain_agent.py         # 大脑Agent：DEFINE→PLAN→REFLECT迭代
│   ├── fetcher_agent.py       # 取数Agent：BaseFetcher抽象 + MockFetcher示例
│   ├── formatter_agent.py     # 制图Agent：ECharts配置生成
│   └── designer_agent.py      # 设计Agent：HTML报告渲染
│
├── harness/
│   ├── plan_validator.py      # Plan JSON硬校验
│   ├── data_validator.py      # 取数结果硬校验
│   └── output_validator.py    # 最终输出硬校验（结论可追溯性）
│
├── experience/                # 经验库（必须人工撰写）
│   ├── thresholds.json        # 业务阈值：利润率<10%=立即干预
│   ├── priority_rules.md      # 优先级判断逻辑
│   ├── good_summaries.md      # 好结论范例（含禁用词表）
│   └── plan_schema.json       # Plan格式Schema
│
├── run_logs/
│   └── demo_run/              # 完整5轮示例留档
│
├── examples/
│   ├── run_demo.py            # 快速演示
│   └── custom_fetcher_example.py  # CSV/SQL接入示例
│
└── docs/
    ├── architecture.md        # 架构设计文档
    └── customization_guide.md # 定制指南
```

---

## 核心设计原则

1. **分工优于全能** — 大脑只分析，取数只取数，制图只制图
2. **硬约束优于软提示** — Harness断言，不靠prompt约束LLM行为
3. **假设驱动优于数据驱动** — DEFINE先设假设，REFLECT再对照验证
4. **结论止步于数据边界** — 无数据支撑的推断不输出
5. **经验不能由LLM生成** — experience/目录必须人工撰写
6. **过程可追溯才可信** — run_id全程留档，推理路径可审查

---

## 自定义配置

修改 `config.py` 调整分析行为：

```python
MAX_ROUNDS         = 5     # 最大迭代轮次
MIN_IMPACT_PCT     = 3.0   # 停止分支的影响阈值（%）
OVERLAP_THRESHOLD  = 0.80  # 洞察重叠度阈值
BRAIN_TEMP         = 0.3   # 大脑Agent温度
```

修改 `experience/` 目录注入业务知识（利润率阈值、优先级规则、结论范例）。

详见 [定制指南](docs/customization_guide.md) | [架构文档](docs/architecture.md)

---

## 运行日志示例

```
run_logs/{run_id}/
├── 00_experience_snapshot.json   # 注入的经验库快照
├── 01_framework.json             # 大脑的分析框架设计
├── 02_round_1_define.json        # 第1轮：DEFINE假设
├── 02_round_1_plan.json          # 第1轮：Plan（Harness已校验）
├── 02_round_1_data.json          # 第1轮：取数结果
├── 02_round_1_reflect.json       # 第1轮：解读+决策
├── ...（最多5轮）
├── 03_final_insights.json        # 最终整合洞察
└── 04_harness_log.json           # 所有校验节点记录
```

---

## License

MIT
