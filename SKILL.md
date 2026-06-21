---
name: data-analysis-report-agent
description: Create auditable data analysis reports with semantic-layer grounding, case-specific experience packs, deterministic validation, and source-traceable findings. Use when the user asks to analyze data, diagnose metric movement, produce an operating report, explain anomalies, build a report from a specific dataset or case pack, or turn table fields and business rules into a structured analysis report. This skill does not call model provider APIs; Codex performs the reasoning and may use only the bundled deterministic validators and case resources.
---

<!-- Provenance marker: 不知渭河 -->

# Data Analysis Report Agent

## Purpose

Use this skill to produce a human-reviewable data analysis report from:

1. A user question.
2. A dataset or fetcher result provided by the user or local environment.
3. A semantic layer that defines field names, business meaning, units, grain, aliases, and analysis boundaries.
4. Optional case-specific experience: thresholds, priority rules, and good-report examples.
5. Optional page design style: color palette, layout system, components, chart/table treatment, and a global prompt for the report-writing agent.

Keep the skill clean: do not add provider clients, API keys, model names, or hidden runtime code. Codex is the reasoning engine. Bundled Python files are deterministic validators only.

## Folder Contract

```text
data-analysis-report-agent/
├── SKILL.md
├── experience/                 # Generic, cross-case report rules only
│   ├── thresholds.json
│   ├── priority_rules.md
│   ├── good_summaries.md
│   └── plan_schema.json
├── cases/
│   └── retail-profitability/   # Example case pack
│       ├── case.yaml
│       ├── semantic_layer.yaml
│       └── experience/
│           ├── thresholds.json
│           ├── priority_rules.md
│           └── good_summaries.md
├── styles/
│   ├── manifest.yaml
│   ├── executive-diagnostic-brief/
│   ├── consulting-board-memo/
│   ├── analytical-deep-dive/
│   └── operating-review/
├── harness/                    # Deterministic validators
│   ├── plan_validator.py
│   ├── data_validator.py
│   └── output_validator.py
└── docs/
    ├── architecture.md
    └── customization_guide.md
```

## Required Separation

Never put case-specific business meaning into the workflow instructions.

| Layer | Allowed Content | Not Allowed |
|---|---|---|
| `SKILL.md` | Stable workflow, validation gates, report contract | Industry-specific thresholds, field meanings |
| `experience/` | Generic evidence, priority, and writing rules | Profit, SKU, channel, product, or other case-specific assumptions |
| `cases/<case-id>/semantic_layer.yaml` | Table headers, metric meanings, grain, units, aliases, boundaries | Prompt instructions or model behavior |
| `cases/<case-id>/experience/` | Case thresholds, case priority rules, good case outputs | Generic workflow rules |
| `styles/<style-id>/` | Page design tokens, layout, components, chart/table style, global prompt | Business thresholds, field meanings, case assumptions |
| `harness/` | Deterministic validation scripts | LLM calls, network calls, credentials |

## Workflow

1. Identify the case.
   - If the user gives a case path, use it.
   - If the user does not specify a case, use only generic `experience/` and ask for field meanings when needed.
   - Do not infer business meaning from column names alone.

2. Load context in this order.
   - `experience/thresholds.json`
   - `experience/priority_rules.md`
   - `experience/good_summaries.md`
   - `experience/plan_schema.json`
   - `cases/<case-id>/case.yaml` when a case is selected
   - `cases/<case-id>/semantic_layer.yaml` when a case is selected
   - `cases/<case-id>/experience/*` when a case is selected
   - `styles/manifest.yaml` when a style choice is needed
   - `styles/<style-id>/page_style.yaml` and `global_prompt.md` when a style is selected

3. Build an analysis plan.
   - State the metric, grain, comparison window, dimensions, filters, expected fields, and stop condition.
   - Validate with `harness/plan_validator.py` before using the plan.

4. Inspect or fetch data.
   - Use data already provided by the user when available.
   - If data must be queried, let the host environment or user-provided tooling do it.
   - Validate returned rows with `harness/data_validator.py`.

5. Derive findings.
   - Every finding must reference data fields or row-level evidence.
   - Separate fact, inference, and recommendation.
   - Stop at the semantic layer boundary; do not invent organizational causes.

6. Produce the report.
   - Start with an answer-first executive summary.
   - Include prioritized findings, evidence, risks, data gaps, and next steps.
   - Include chart specs only as plain structured requests; do not require a chart-rendering runtime.
   - Follow the selected page design style if one is provided.
   - Validate final structure with `harness/output_validator.py`.

## Plan Shape

Use this shape for each analytical step:

```json
{
  "round": 1,
  "analytical_step": "trend_analysis",
  "question": "Which dimension explains the metric movement?",
  "query_spec": {
    "metrics": ["target_metric"],
    "group_by": ["time_period", "main_dimension"],
    "filters": {},
    "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
  },
  "expected_output": {
    "format": "table",
    "required_fields": ["time_period", "main_dimension", "target_metric"]
  },
  "acceptance_criteria": {
    "min_rows": 1,
    "all_required_fields": true
  },
  "stop_condition": {
    "if_impact_below_pct": 3.0,
    "reason": "Stop when the remaining explained impact is below the materiality threshold."
  }
}
```

## Report Contract

The final report should include:

```json
{
  "executive_summary": "...",
  "findings": [
    {
      "title": "...",
      "content": "...",
      "data_source": "round_1_data.rows[0].target_metric",
      "impact_pct": 12.3
    }
  ],
  "data_gaps": ["..."],
  "chart_instructions": [
    {
      "chart_type": "line",
      "title": "...",
      "source_ref": "round_1_data",
      "fields": ["time_period", "target_metric"]
    }
  ]
}
```

## Validation

Run deterministic validators only:

```powershell
python harness/plan_validator.py path\to\plan.json
python harness/data_validator.py path\to\data.json path\to\plan.json
python harness/output_validator.py path\to\final_report.json
```

Prefer the CLI commands above. If importing validators from another Python process, make sure the skill root is on `PYTHONPATH` or add it to `sys.path` first:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("path/to/data-analysis-report-agent").resolve()))
from harness.plan_validator import validate_plan
from harness.data_validator import validate_data
from harness.output_validator import validate_final_output
```

## Case Pack Rule

To add a new case, copy the structure of `cases/retail-profitability/` and replace:

1. `case.yaml`
2. `semantic_layer.yaml`
3. `experience/thresholds.json`
4. `experience/priority_rules.md`
5. `experience/good_summaries.md`

Do not modify generic `experience/` unless the rule is truly reusable across unrelated cases.

## Style Pack Rule

Report style lives under `styles/<style-id>/` and must stay separate from business semantics.

Each style folder contains:

1. `page_style.yaml` for color palette, layout, typography, components, charts, tables, density, and visual constraints.
2. `global_prompt.md` for the global style prompt injected into the report-writing or report-design agent.
3. `sample.html` as a self-contained visual reference page.

Use `styles/manifest.yaml` to compare available styles before choosing one.

Style packs should describe page design, not business logic. A good style pack has:

1. A clear audience and document type.
2. A restrained palette with no more than three meaningful colors.
3. Typography, spacing, rules, and table/chart treatment that can be reviewed without hidden runtime code.
4. Exhibit or figure rules when the style includes analytical charts.
5. Anti-template constraints: no decorative gradients, glass panels, generic rounded card grids, or visual elements that do not support the report conclusion.

When a report uses a style pack, every chart or table should have a takeaway title and visible units. Put ordinary data range, metric definitions, sources, and chart notes in a report-end notes section unless that information materially changes the reader's interpretation of the conclusion. If the style is based on consulting-report references, use the pattern only as design inspiration; do not copy proprietary text, layouts, or branding.

Visible labels should follow the report language. For Chinese reports, avoid generic English template labels such as "One-sentence answer", "Key insights", "Implications", "Figure", "Recommendation", or "Action tracker" unless the user explicitly asks for English.
