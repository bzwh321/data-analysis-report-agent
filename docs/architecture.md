# 架构设计文档

## 整体架构

```
Experience库（参照系，人工撰写）
    ↓ 注入上下文
大脑Agent (BrainAgent, temp=0.3)
    │
    ├── Phase 1: 设计分析框架
    │     输出 → 01_framework.json（留档）
    │
    ├── Phase 2: 迭代循环（最多5轮）
    │     ┌── DEFINE（问自己）
    │     │     设立假设 + 判断标准（取数前）
    │     │     输出 → 02_round_N_define.json
    │     │
    │     ├── PLAN（问数据）
    │     │     假设 → Plan JSON（Harness强校验）
    │     │     输出 → 02_round_N_plan.json
    │     │
    │     ├── ACT
    │     │     取数Agent执行 → data JSON
    │     │     Harness数据结果校验
    │     │     输出 → 02_round_N_data.json
    │     │
    │     └── REFLECT（问自己）
    │           对照假设解读数据，更新洞察池
    │           停止判断（硬代码）→ CONTINUE / PIVOT / STOP
    │           输出 → 02_round_N_reflect.json
    │
    └── Phase 3: 洞察整合
          输出 → 03_final_insights.json
          含 executive_summary / findings / data_gaps / chart_instructions
                    ↓
          制图Agent (FormatterAgent, temp=0.1)
                    ↓
          设计Agent (DesignerAgent, temp=0.2)
                    ↓
          Harness（格式+完整性校验）
                    ↓
          最终报告 HTML
```

## 核心设计原则

### 1. 分工优于全能
每个 Agent 只做一件事：
- BrainAgent：分析决策（不取数、不制图）
- FetcherAgent：取数执行（不分析、不设计）
- FormatterAgent：图表生成（只处理图表指令）
- DesignerAgent：报告渲染（只做 HTML 组装）

### 2. 硬约束优于软提示
关键约束由 Harness 硬代码断言，而非 prompt 软提示：
- Plan JSON 格式校验（plan_validator.py）
- 数据范围校验（data_validator.py）
- 结论可追溯性校验（output_validator.py）
- 轮次上限（config.MAX_ROUNDS = 5）

### 3. 假设驱动优于数据驱动
DEFINE 阶段在取数前先设立假设，REFLECT 阶段对照假设解读数据。
避免"拿到数据再想说什么"的信息复述型分析。

### 4. 结论止步于数据边界
- 每条结论必须追溯到本轮 data JSON 的具体字段
- 无数据支撑的组织归因不得出现
- 边界处自然给出下一步方向，不声明"当前数据无法..."

### 5. 经验不能由 LLM 生成
`experience/` 目录必须由人工（领域专家）撰写。
LLM 在 DEFINE 阶段读取经验库作为判断参照系，但不自动更新经验库。

### 6. 过程可追溯才可信
每次运行生成唯一 `run_id`，所有中间过程文件保存在 `run_logs/{run_id}/`。
历史可追溯，便于审查大脑 Agent 的推理路径。

## 停止判断（硬代码）

```python
def should_stop(reflect, insight_pool, round_num):
    if round_num >= MAX_ROUNDS:          # A: 轮次上限
        return True, "MAX_ROUNDS"
    if reflect['impact_pct'] < MIN_IMPACT_PCT:  # B: 影响低于阈值
        return True, "LOW_IMPACT"
    if compute_overlap(insight_pool) > OVERLAP_THRESHOLD:  # C: 重复
        return True, "OVERLAP"
    if not reflect['has_insight']:       # D: 无洞察 → 换方向
        return False, "PIVOT"
    return False, "CONTINUE"
```

停止判断由系统执行，不依赖 LLM 自我判断。

## Plan JSON 格式

```json
{
  "round": 2,
  "analytical_step": "decomposition",
  "question": "年度利润率下滑主要由哪个品类驱动？",
  "query_spec": {
    "metrics": ["profit_rate"],
    "group_by": ["category", "month"],
    "filters": {},
    "date_range": {"start": "2024-01", "end": "2024-12"}
  },
  "expected_output": {
    "format": "table",
    "required_fields": ["category", "profit_rate_2024", "profit_rate_2023", "pp_change"],
    "unit_sales": "万元",
    "unit_rate": "百分比"
  },
  "acceptance_criteria": {
    "min_rows": 3,
    "profit_rate_range": [0, 100],
    "all_required_fields": true
  },
  "stop_condition": {
    "if_impact_below_pct": 3,
    "reason": "子维度影响<3%则停止拆解"
  }
}
```

## 中间过程留档结构

```
run_logs/{run_id}/
├── 00_experience_snapshot.json   # 本次注入的经验库快照
├── 01_framework.json             # 大脑的分析框架设计
├── 02_round_1_define.json        # 第1轮 DEFINE（假设+判断标准）
├── 02_round_1_plan.json          # 第1轮 Plan（Harness已校验）
├── 02_round_1_data.json          # 第1轮取数结果
├── 02_round_1_reflect.json       # 第1轮解读+决策
├── 02_round_2_define.json
├── ...（最多5轮）
├── 03_final_insights.json        # Phase 3整合输出
└── 04_harness_log.json           # Harness校验记录
```
