# Data Analysis Report Agent

将原始数据、业务口径和研究问题交给 AI，生成证据可核对、文字克制、图文一致的 HTML 数据分析报告。

## 本次更新

报告生产链已拆分为数据分析、图表设计、文字撰写、对抗审查、报告组装和 HTML 渲染六个协作 Agent。

新增验证回流机制。文字或图表发现证据不足、口径错误或文图不一致时，会退回分析层补数，再重新生成受影响内容。

格式、风格和配色现在独立管理。仓库内置“编辑式证据报告”和“互联网汇报风格”，图表与图标统一使用已登记的红、黄、绿、灰配色。

## 核心流程

```text
原始数据与问题
  -> ReAct 分析与证据验证
  -> 图表 Agent + 文字 Agent
  -> 对抗审查
  -> Report Assembler 文图仲裁
  -> HTML Renderer
  -> 渲染后结构与视觉检查
```

图表与文字相互印证，但不互相复印。图表必须完整绘制声明指标的基础数据，文字只提炼最重要的证据和结论。

## 目录

```text
agents/       独立 Agent 与运行参数
assets/       矢量图标等报告素材
cases/        可选业务案例包
experience/   跨案例通用分析规则
harness/      确定性合同校验器
references/   分析、图表、文字和组装合同
styles/       格式风格与独立配色系统
SKILL.md      主工作流入口
```

## 使用

```powershell
git clone https://github.com/bzwh321/data-analysis-report-agent.git
```

将完整目录导入支持 Skills 的 AI 环境，并明确要求使用本目录中的 `SKILL.md`。同时提供：

- 原始数据或可读取的数据路径；
- 关键字段含义、单位和数据粒度；
- 希望回答的业务问题；
- 报告读者与输出风格。

不要只复制 `SKILL.md`，Agent 还需要读取 `agents/`、`references/`、`styles/`、`experience/` 和 `harness/`。

## 报告风格与配色

- `editorial-evidence-report`：编辑式证据报告，适合通用经营分析。
- `internet-reporting`：互联网汇报风格，强调连续阅读和自然图文关系。
- `styles/color-system/color_system.yaml`：唯一配色来源；用户新增配色必须先登记。
- `assets/chart-icons/chart-emphasis-icons.svg`：红、黄、绿、灰矢量强调图标。

## 校验

```powershell
python harness/test_material_pack_contract.py
python harness/test_run_observability_contract.py
python harness/test_agent_runtime_contract.py
python harness/test_report_text_contract.py
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

本仓库不包含模型客户端、API Key、自动取数服务或运行期报告。生成的 HTML、截图和临时文件应保存在 skill 目录之外。
