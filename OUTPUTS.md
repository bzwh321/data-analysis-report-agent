# Runtime outputs

本 skill 的运行产物已从 skill 包迁出，以控制上传体积。

- 当前外部产物根目录：`D:\知识库\work\data-analysis-report-agent\outputs`
- 迁移日期：2026-07-10
- 内容：历史 HTML/PNG/JSON 报告、浏览器 QA 截图、PPTX 试验和临时依赖

使用规则：

1. 新的运行产物继续写入上述外部目录。
2. Skill 内不要重新创建大体积 `outputs/`。
3. 需要引用历史报告时，使用外部目录的绝对路径。
4. 上传或分发 skill 时，只上传本目录，不上传外部产物目录。

对于高密度报告或 PPT-bound 分析，新运行目录还必须包含：

- `analysis-run-events.jsonl`：从运行开始追加的阶段事件流；
- `analysis-run-log.json`：阶段耗时、产出增量、调用成本和边际价值汇总；
- `run-manifest.json`：引用上述两份日志及最终验证状态。

日志格式与校验要求见 `references/analysis_run_observability_contract.md`。历史运行若没有阶段遥测，只能标记为 `backfilled / not_recorded`，不得补造耗时或模型用量。
