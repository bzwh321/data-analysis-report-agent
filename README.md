# Data Analysis Report Agent

<!-- Provenance marker: bzwh -->

一个用于生成**可审查数据分析报告**的 Codex skill。

它的核心设计不是“把一堆提示词塞进工作流”，而是把报告生产拆成几层：

- 通用报告流程
- 语义层
- 案例经验层
- 页面风格层
- 本地确定性校验

![Data Analysis Report Agent topology](docs/assets/skill-topology.svg)

## 这个 Skill 解决什么问题

很多数据分析报告失败，不是因为模型不会写，而是因为：

- 表头和业务含义混在提示词里，换一个案例就污染工作流；
- 阈值、经验判断、好结论样例被写进通用流程，导致下一个项目继承错误经验；
- 页面风格只是一段文字描述，报告 agent 不知道应该怎么排版；
- 最终报告没有结构校验，容易出现没有数据来源、没有边界说明、没有行动建议的结论。

这个 skill 的目标是让报告生产变成一个可维护协议：

```text
用户问题 + 数据
  -> 选择 case pack
  -> 读取语义层
  -> 读取案例经验层
  -> 选择报告风格
  -> 生成分析计划
  -> 记录阶段事件、成本和边际价值
  -> 校验计划/数据/输出
  -> 生成可审查报告
  -> 如需 PPTX，交给 data-report-presentation-planner 形成并锁定 v0.5 故事线、语义布局与全局颜色方案
  -> 交给 data-report-ppt-author，以隔离页级任务包让 Page Visual Designer 锁定 slide-plan、SVG视觉参考和图表设计契约
  -> Harness 通过页面设计门禁；仅代表页或风险页调用设计 Judge，再由同一页级 PPT Implementer 上下文制作和组合原生对象
  -> data-report-pptx-renderer 作为 Compiler/SDK 编译和确定性校验
  -> 合并锁定页面，交付可编辑演示文稿
```

## 重要边界

这个仓库不是一个独立模型运行器。

它不包含：

- API key
- provider SDK client
- model name
- hidden runtime
- 网络调用
- 自动取数服务
- PPTX 渲染 runtime

Codex 或其他宿主 agent 负责推理、读数据、写报告。`harness/` 里的 Python 文件只做本地确定性结构校验。
当用户需要可编辑 PPTX 时，本 skill 应先输出结构化报告和决策就绪的 `analysis_material_pack` v0.3：分析 Agent 必须完成业务问题驱动的 ReAct、候选结论审查与重写、管理用途和下一验证问题，并把图表候选绑定到要证明的 finding。随后再调用 `D:\知识库\skills\data-report-presentation-planner` 完成 v0.5 故事线、人审、逐页合同、语义布局意图和全局语义颜色方案。Planner 负责选择、合并、删除和排序已经审查的素材，不负责为弱结论补业务意义；编译后只把页级素材与紧邻上下文下发。大纲获批后由 `D:\知识库\skills\data-report-ppt-author` 从隔离任务包执行：标准页只运行 Page Visual Designer、一个可恢复的页级 PPT Implementer 上下文和 rendered-slide Judge；Chart Design UI 与 page-design Judge 按复杂度或风险触发；确定性 Harness 与 QA 每页必跑。Author 只能解析颜色契约，PPT Implementer 不得自行撰写文字颜色。审查用 SVG 不得进入最终 PPTX。`D:\知识库\skills\data-report-pptx-renderer` 只作为 Compiler/SDK 和 legacy fallback。不要把 `pptxgenjs`、`python-pptx` 或 HTML 转 PPT 逻辑塞进本 skill。

运行产物、浏览器截图、试验依赖和生成报告不得长期存放在 skill 包内。宿主环境应把它们写到外部工作目录；本机当前产物位置记录在 [`OUTPUTS.md`](OUTPUTS.md)。这样上传或分发 skill 时不会携带大体积历史产物。

## 目录结构

```text
data-analysis-report-agent/
├── SKILL.md                         # skill 主说明：稳定流程和报告契约
├── README.md                        # GitHub 使用说明
├── experience/                      # 通用、跨案例报告经验
│   ├── thresholds.json
│   ├── priority_rules.md
│   ├── good_summaries.md
│   └── plan_schema.json
├── cases/                           # 案例包
│   ├── retail-profitability/
│   ├── boss-data-analyst-jobs/
│   └── workforce-cost-budget/
├── styles/                          # 页面设计风格包
│   ├── manifest.yaml
│   ├── analytical-deep-dive/
│   ├── executive-diagnostic-brief/
│   ├── consulting-board-memo/
│   └── operating-review/
├── harness/                         # 本地确定性校验
│   ├── plan_validator.py
│   ├── data_validator.py
│   ├── output_validator.py
│   └── run_observability_validator.py
└── docs/
    ├── architecture.md
    ├── customization_guide.md
    ├── skill-topology.html
    └── assets/
        ├── skill-topology.svg
        └── report-template-gallery.svg
```

## 你需要输入什么

最少需要：

| 输入 | 必需 | 说明 |
|---|---:|---|
| 用户问题 | 是 | 例如“上海数据分析师岗位的薪资、经验门槛和技能要求是什么？” |
| 数据 | 是 | Excel、CSV、SQL 结果、JSON rows，或宿主环境能读取的数据 |
| 字段含义 | 强烈建议 | 最好通过 `cases/<case-id>/semantic_layer.yaml` 提供 |
| 案例经验 | 可选 | 阈值、优先级规则、好结论样例 |
| 报告风格 | 可选 | 从 `styles/manifest.yaml` 选择 |
| 输出格式 | 可选 | HTML、Markdown、结构化 JSON，或宿主 agent 支持的其他报告形态；PPTX 通过 Planner → PPT Author → Compiler/SDK 工作流生成 |

如果没有语义层，不要让 agent 直接根据表头猜业务含义。先补语义层，再做报告。

## 快速使用

在 Codex 中，把本目录作为 skill 使用，然后给出问题、数据路径和 case/style 选择。

示例：

```text
使用 data-analysis-report-agent。
数据在：D:\...\BOSS直聘数据分析师职位-案例分析原始数据.xlsx
使用 case：cases/boss-data-analyst-jobs
使用风格：styles/consulting-board-memo
请生成一份 HTML 报告，回答：
上海数据分析师岗位的薪资水平、经验门槛和核心技能要求是什么？
```

如果是新数据，先让 agent 生成语义层：

```text
使用 data-analysis-report-agent。
请先读取这个 Excel 的表头和前几行，帮我创建一个新的 case pack。
要求：
1. 不要把业务字段含义写进 SKILL.md
2. 字段含义写到 semantic_layer.yaml
3. 阈值和案例经验写到 cases/<case-id>/experience/
```

## 工作流

1. 识别问题和输出目标。
2. 选择或创建 case pack。
3. 读取通用经验层 `experience/`。
4. 读取案例语义层 `cases/<case-id>/semantic_layer.yaml`。
5. 读取案例经验层 `cases/<case-id>/experience/`。
6. 选择页面风格 `styles/<style-id>/`。
7. 生成分析计划。
8. 用 `harness/plan_validator.py` 校验计划。
9. 初始化并持续写入 `analysis-run-events.jsonl` 和 `analysis-run-log.json`。
10. 读取或检查数据。
11. 用 `harness/data_validator.py` 校验数据结构。
12. 提炼事实、推断、建议，并记录每轮产出增量和边际价值。
13. 生成报告。
14. 用 `harness/output_validator.py` 校验最终结构。
15. 用 `harness/run_observability_validator.py` 校验运行日志。

## 语义层怎么维护

语义层文件位置：

```text
cases/<case-id>/semantic_layer.yaml
```

语义层只回答一个问题：

> 这些字段在这个案例里是什么意思？

推荐结构：

```yaml
semantic_layer_id: your-case-id
version: "0.1"
purpose: 说明这个语义层服务什么案例

source:
  expected_file_name: your-data.xlsx
  expected_sheet: Sheet1

grain:
  default: row_grain
  supported:
    - name: row_grain
      keys: [date, segment]
      meaning: 每一行代表什么

fields:
  raw_field_name:
    source_header: 原始表头
    role: metric
    business_name: 业务名称
    unit: pct
    meaning: 这个字段衡量什么
    quality_rule: 使用前需要注意什么

derived_metrics:
  derived_metric_name:
    business_name: 派生指标名称
    unit: pct
    formula: numerator / denominator * 100
    meaning: 为什么要算这个指标

business_terms:
  业务词: 业务词定义

analysis_boundaries:
  - 这份数据能证明什么
  - 这份数据不能证明什么
```

维护规则：

- 字段含义、口径、单位、粒度写在语义层。
- 不要在语义层写 prompt 指令。
- 不要在语义层写页面风格。
- 不要在语义层写“模型应该怎么想”。
- 原始字段有歧义时，必须写 `quality_rule` 或 `analysis_boundaries`。
- 每次字段变更，更新 `version` 或在 `purpose` 中说明适用范围。

好语义层的标准：

- 读者不用看原始 Excel，也能知道每个字段代表什么。
- agent 不需要猜表头含义。
- 报告能明确停在数据边界内。

## 经验层怎么维护

经验层分两类。

### 1. 通用经验层

位置：

```text
experience/
```

只放跨案例都成立的规则，例如：

- 每条结论必须有数据来源。
- 区分事实、推断和建议。
- 不要编造组织原因。
- 影响很小的分支可以停止下钻。

不要把某个行业、某个案例的阈值写到这里。

### 2. 案例经验层

位置：

```text
cases/<case-id>/experience/
```

包含：

| 文件 | 用途 |
|---|---|
| `thresholds.json` | 这个案例的阈值、告警线、物料性标准 |
| `priority_rules.md` | 这个案例里结论如何排序 |
| `good_summaries.md` | 好结论写法样例 |

例子：

```json
{
  "salary_parse_rate": {
    "warning_low": 0.85,
    "desc": "薪资可解析率低于85%时，薪资结论必须降级。"
  },
  "impact_min_pct": 3.0
}
```

维护规则：

- 只写这个案例适用的经验。
- 阈值必须能解释为什么重要。
- `good_summaries.md` 应该给“好输出样例”，不是堆分析方法。
- 案例经验不能覆盖语义层字段含义。
- 如果一条规则开始适用于多个无关案例，再考虑提升到根目录 `experience/`。

## 页面风格怎么维护

风格文件位置：

```text
styles/<style-id>/
├── page_style.yaml
├── global_prompt.md
└── sample.html
```

风格层只回答：

> 报告应该长什么样？

不要把业务字段、阈值、行业经验写进风格层。

当前内置风格：

![Report template gallery](docs/assets/report-template-gallery.svg)

| 风格 | 适用场景 |
|---|---|
| `analytical-deep-dive` | 白皮书、研究报告、深度分析 |
| `executive-diagnostic-brief` | 高管诊断、异常判断、快速决策 |
| `consulting-board-memo` | 董事会备忘录、推荐路径、方案取舍 |
| `operating-review` | 周会/月会复盘、行动追踪、状态管理 |

风格维护规则：

- `page_style.yaml` 写配色、字体、布局、容器、图表和表格规则。
- `global_prompt.md` 写给报告撰写 agent 的全局页面提示词。
- `sample.html` 是静态视觉参考页。
- 不要引用 CDN、外部脚本或隐藏运行时。
- 不要用装饰性渐变、玻璃态、通用卡片堆。
- 中文报告不要出现泛用英文模板标签。

## 校验方式

计划校验：

```powershell
python harness/plan_validator.py path\to\plan.json
```

数据校验：

```powershell
python harness/data_validator.py path\to\data.json path\to\plan.json
```

输出校验：

```powershell
python harness/output_validator.py path\to\final_report.json
```

skill 结构校验：

```powershell
$env:PYTHONUTF8='1'
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

## 内置案例

### BOSS 数据分析师岗位案例

路径：

```text
cases/boss-data-analyst-jobs/
```

用途：

- 招聘岗位样例分析
- 薪资文本解析
- 经验/学历字段混杂处理
- 技能标签统计
- 公司类型结构观察

本地 HTML 报告样例：

- `cases/boss-data-analyst-jobs/report.html`
- `cases/boss-data-analyst-jobs/report-executive-diagnostic-brief.html`
- `cases/boss-data-analyst-jobs/report-consulting-board-memo.html`
- `cases/boss-data-analyst-jobs/report-operating-review.html`

### 人工成本预算案例

路径：

```text
cases/workforce-cost-budget/
```

用途：

- 人工成本预算分析
- 组织层级口径
- 成本/营收效率
- 疑似人数代理字段处理

### 零售利润率案例

路径：

```text
cases/retail-profitability/
```

用途：

- 零售利润率下滑归因
- 事件性冲击和结构漂移区分
- 促销季影响分析

## 新增一个案例的步骤

1. 复制目录：

```text
cases/retail-profitability/
```

2. 改名为：

```text
cases/your-case-id/
```

3. 修改：

```text
case.yaml
semantic_layer.yaml
experience/thresholds.json
experience/priority_rules.md
experience/good_summaries.md
```

4. 用真实样例数据跑一遍：

- plan validator
- data validator
- output validator

5. 如果生成 HTML 报告，确认：

- 没有外部 CDN
- 图片路径可用
- 数据范围和公式在末尾注释
- 主体结论不超过语义层边界

## 新增一个风格的步骤

1. 创建目录：

```text
styles/your-style-id/
```

2. 添加：

```text
page_style.yaml
global_prompt.md
sample.html
```

3. 在 `styles/manifest.yaml` 注册。

4. 用同一份数据生成至少一份完整报告，确认风格差异不是只换颜色。

风格差异应该体现在：

- 配色
- 版心
- 容器结构
- 图表摆放
- 表格密度
- 信息层级
- 结尾模块

## 发布前检查清单

- [ ] `SKILL.md` 没有 case-specific 字段含义。
- [ ] 根目录 `experience/` 没有某个案例专属阈值。
- [ ] 每个 case 都有 `semantic_layer.yaml`。
- [ ] 每个 case 的经验写在 `cases/<case-id>/experience/`。
- [ ] 每个 style 都有 `page_style.yaml`、`global_prompt.md`、`sample.html`。
- [ ] HTML 样例不依赖外部 CDN 或脚本。
- [ ] 校验脚本仍然是本地确定性逻辑。
- [ ] 不包含 API key、provider SDK client、模型名或隐藏 runtime。
- [ ] README 中的图片路径在 GitHub 上可显示。

## License

根据你的项目发布策略补充。若要公开给他人复用，建议在上传 GitHub 前明确许可证。
