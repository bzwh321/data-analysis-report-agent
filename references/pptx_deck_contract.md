# PPTX Deck Handoff Contract

Use this compatibility contract when an approved presentation plan is converted into editable PowerPoint execution data for `data-report-pptx-renderer`.

The report skill owns analysis. The sibling `data-report-presentation-planner` owns Deck architecture, outline approval, slide intent, and evidence allocation. The renderer owns native PowerPoint construction.

## Upstream Synthesis Requirement

Do not jump directly from findings to PPTX rendering. For new work, first run `D:\知识库\skills\data-report-presentation-planner\SKILL.md`, obtain a hash-locked human approval, and compile the storyboard/page contexts. The embedded `agents/deck-synthesis-agent/SKILL.md` is a compatibility route for older fixtures only.

Each PPTX slide must carry `synthesis_ref`, pointing to the synthesis slide that decided:

1. Which findings were merged.
2. Why they belong on one page.
3. What the page's primary claim is.
4. Which renderer pattern, if any, fits the already approved composition. Archetypes are optional case references, not global requirements.

The renderer receives the final execution payload; it must not decide the analytical merge, split a page, or change the approved page count.

## Required Top-Level Shape

```json
{
  "contract_version": "0.1",
  "deck_goal": "boss_consulting_deck",
  "audience": "management",
  "title": "报告标题",
  "style_id": "template-green-dashboard",
  "sources": [{"id": "sales_trend", "label": "示例：月度销售额"}],
  "slides": []
}
```

## Slide Contract

Each slide must include:

| Field | Purpose |
| --- | --- |
| `id` | Stable slide identifier for validation and debugging |
| `synthesis_ref` | ID of the deck synthesis slide that created this PPT slide |
| `layout` | Renderer layout, such as `dashboard_performance` |
| `slide_role` | Analytical role, such as `performance_dashboard` or `comparison_exhibit` |
| `title` | Reader-facing slide title |
| `claim` | The one-sentence conclusion the page proves |
| `evidence_refs` | Source IDs used by the claim and visual payload |
| `visual_mode` | `native_chart`, `shape_exhibit`, or `hybrid_dashboard` |

Do not send a PPT page as a full-slide image. If a visual cannot be native-editable, mark the specific object as a fallback and explain why; do not hide it in the main slide object.

## Layout Payloads

`dashboard_performance` must provide:

- `dashboard.kpis`
- `dashboard.trend_chart`
- `dashboard.ring_metrics`
- `dashboard.insights`

`comparison_vs` must provide:

- `comparison.left`
- `comparison.right`
- Optional `comparison.reason_cards`

`problem_solution_grid` must provide:

- `problem_solution.problems`
- `problem_solution.solutions`

`finding_with_chart` must provide `chart`. `finding_with_table` must provide `table`.

## Editable Chart Requirements

Native charts must include real data, not only a visual description:

```json
{
  "type": "line",
  "title": "销售额趋势",
  "labels": ["1月", "2月"],
  "series": [{"name": "销售额", "values": [100, 200]}],
  "source_ref": "sales_trend",
  "takeaway": "2月销售额较1月提升",
  "reference_lines": [{"value": 150, "label": "目标线"}],
  "annotations": [{"label": "峰值", "target_label": "2月"}],
  "highlight_labels": ["2月"]
}
```

For consulting-style dashboard pages, line and bar charts with six or more labels should provide at least one focus mechanism: `annotations`, `highlight_labels`, or `reference_lines`. Annotation anchors should use `target_label`, `target_range`, or explicit normalized coordinates.

## Validation Gate

Before calling the PPTX renderer, run:

```powershell
python harness/pptx_contract_validator.py path\to\deck.json
```

Passing this validator means the deck handoff has:

1. A declared audience, goal, style, source registry, and slide list.
2. Slide-level claim and evidence references.
3. Layout-specific payloads for dense consulting pages.
4. Editable chart data arrays for native charts.
5. Source references for charts and tables.
6. No full-slide screenshot route.

Renderer validation is still required after PPTX generation.
