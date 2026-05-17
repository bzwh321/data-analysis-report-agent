# 定制指南

## 接入你自己的数据源

### 最小步骤（3步）

**第1步：继承 BaseFetcher**

```python
from agents.fetcher_agent import BaseFetcher

class MyFetcher(BaseFetcher):
    def fetch(self, plan: dict) -> dict:
        spec = plan['query_spec']
        # 用 spec['metrics'] / spec['group_by'] / spec['filters'] / spec['date_range']
        # 执行你的查询逻辑（SQL / pandas / API）
        rows = my_query(spec)
        return {
            "row_count": len(rows),
            "fields": list(rows[0].keys()),
            "rows": rows,
        }
```

**第2步：替换 experience/ 目录内容**

| 文件 | 必改内容 | 示例 |
|------|---------|------|
| `thresholds.json` | 你的业务阈值（利润率/增速/市占率等） | `"gm_rate": {"critical_low": 15.0}` |
| `priority_rules.md` | 你的优先级判断逻辑 | "SKU 断货率>5% 排第一" |
| `good_summaries.md` | 你的好结论范例（可直接用现有模板） | 保持现有原则，替换业务词汇 |

**第3步：运行**

```python
from runner import AnalysisRunner
runner = AnalysisRunner(fetcher=MyFetcher(), output_path="report.html")
runner.run("你的分析问题")
```

---

## 调整分析行为（config.py）

| 参数 | 默认值 | 何时调整 |
|------|--------|---------|
| `MAX_ROUNDS` | 5 | 数据量大 / 分析维度多 → 增大（最多8）；快速预览 → 减小到2 |
| `MIN_IMPACT_PCT` | 3.0 | 精细分析场景可降到1.5；宽泛扫描可升到5.0 |
| `OVERLAP_THRESHOLD` | 0.80 | 洞察重复多 → 降到0.65；允许更多深挖 → 升到0.90 |
| `BRAIN_TEMP` | 0.3 | 需要更稳定的结论 → 降到0.1；需要更多探索 → 升到0.5 |

---

## 添加新的分析步骤

默认只允许4种 `analytical_step`（白名单硬编码）。添加新步骤：

1. 在 `config.py` 的 `ALLOWED_STEPS` 中添加：
   ```python
   ALLOWED_STEPS = [
       'trend_analysis', 'decomposition', 'attribution', 'risk_mining',
       'cohort_analysis',   # 新增
   ]
   ```

2. 在 `FetcherAgent.fetch()` 中添加对应的取数逻辑：
   ```python
   elif step == 'cohort_analysis':
       return self._cohort_analysis(...)
   ```

3. 更新 `experience/plan_schema.json` 中的 `analytical_step_enum`。

---

## 切换 LLM（从 Claude 换到 OpenAI）

在 `config.py` 中修改：
```python
LLM_MODEL = "gpt-4o"
```

然后在 `agents/brain_agent.py` 中将 `anthropic.Anthropic()` 替换为 `openai.OpenAI()`，
调整 `_call()` 方法的 API 调用格式。

---

## 经验库维护规范

**关键原则：experience/ 目录的内容必须由人工（领域专家）撰写，不能由 LLM 自动生成。**

若让 LLM 自生成经验库，系统退化为普通 LLM 分析，失去业务判断能力。

建议更新频率：
- `thresholds.json`：每季度或业务目标调整时更新
- `priority_rules.md`：每半年结合实际案例复盘后更新
- `good_summaries.md`：每次出现优秀分析案例时及时沉淀
