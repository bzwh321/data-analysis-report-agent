# Customization Guide

## Add A Case Pack

Create:

```text
cases/your-case-id/
├── case.yaml
├── semantic_layer.yaml
└── experience/
    ├── thresholds.json
    ├── priority_rules.md
    └── good_summaries.md
```

## `case.yaml`

Use it for metadata only:

```yaml
case_id: your-case-id
display_name: Your Case Name
description: What this case pack is for.
semantic_layer: semantic_layer.yaml
experience_dir: experience
default_question: Optional default question.
default_context: {}
```

## `semantic_layer.yaml`

Record field meaning, not prompt behavior:

```yaml
semantic_layer_id: your-case-id
version: "0.1"
grain:
  default: daily_metric
  supported:
    - name: daily_metric
      keys: [date, segment]
      meaning: One row per date and segment.
fields:
  date:
    role: dimension
    business_name: Date
    meaning: Reporting date.
  target_metric:
    role: metric
    business_name: Target Metric
    unit: pct
    meaning: Define exactly what this metric measures.
business_terms:
  Example term: Define the term.
analysis_boundaries:
  - State what the data can and cannot prove.
```

## Case Experience

Use `cases/your-case-id/experience/` for:

| File | Purpose |
|---|---|
| `thresholds.json` | Case-specific materiality and business thresholds |
| `priority_rules.md` | How to rank findings for this case |
| `good_summaries.md` | Examples of good case-specific report language |

Do not put case-specific rules in root `experience/`.

## Add A Report Style

For HTML or React, first require a validated `report_text_pack` from
`../references/report_text_pack_contract.md`. Then read
`../references/human_authored_html_design_system.md` as the frozen cross-style
format contract and
`../styles/color-system/color_system.yaml` as the separate color authority. A
style may specialize audience, document character, and report rhythm, but may
not rewrite approved text, weaken the format contract, or define a local palette.

Create:

```text
styles/your-style-id/
├── page_style.yaml
├── global_prompt.md
└── sample.html
```

Register it in `styles/manifest.yaml`.

Use `page_style.yaml` for:

- audience
- design intent
- typography
- page layout
- component rules
- chart and table style
- responsive constraints
- things to avoid

Use `global_prompt.md` as the full-page design prompt that the renderer receives. It may arrange approved text but may not author analytical prose.

Use `sample.html` as a self-contained reference page. Do not reference external CDNs or model/runtime scripts.

Do not put field meanings, thresholds, or business assumptions into a style folder.

Style quality rules:

- Map the reading path and content units to grid spans before choosing components.
- Create an alignment ledger and reuse one column-count and gutter token across all structural blocks.
- Treat shared rendered edges as equal only when they are within `1px`; reject accidental `2-16px` near misses.
- Default to no card; justify every container by state, interaction, print grouping, or exception contrast.
- Let unequal content length and importance produce unequal spans or heights.
- Start from the document role: executive brief, board memo, analytical exhibit report, or operating tracker.
- Reference `styles/color-system/color_system.yaml`; do not add local palette values or color semantics.
- Give every chart/table a takeaway title and unit.
- Put ordinary data range, metric definitions, sources, and derived-metric notes in a report-end notes section; keep only decision-critical caveats next to the finding.
- Avoid AI-template patterns: gradient hero blocks, glassmorphism, generic rounded KPI card grids, decorative badges, and icons that do not carry meaning.
- Use report-native visible labels. For Chinese reports, avoid generic English template labels unless English is explicitly requested.
- Do not use equal-width three-card summaries as the default ending; prefer an evidence-gap table, action tracker, decision record, or validation checklist.
- For charts with more than six marks, label only peaks, troughs, endpoints, exception windows, or values required for the conclusion.
- Keep `sample.html` offline and auditable: inline CSS is allowed; external scripts, CDNs, provider SDKs, and hidden API calls are not.
- Render the sample at desktop width and one narrower width before accepting the style.

## Generic Experience

Only edit root `experience/` when the rule applies across unrelated cases. Examples:

- Every finding needs evidence.
- Do not invent organizational causes.
- Separate fact, inference, and recommendation.
- Stop at the data boundary.

## Review Checklist

- [ ] No API keys or provider SDK clients were added.
- [ ] Field meanings live in `semantic_layer.yaml`.
- [ ] Case thresholds live under `cases/your-case-id/experience/`.
- [ ] Report style lives under `styles/your-style-id/`.
- [ ] HTML/React style follows `references/human_authored_html_design_system.md`.
- [ ] HTML/React style references `styles/color-system/color_system.yaml` and defines no local palette.
- [ ] Structural blocks share one page grid, and rendered anchor alignment has been checked at desktop and narrow widths.
- [ ] Style sample has no external CDN, model call, provider SDK, or hidden runtime dependency.
- [ ] Style prompt includes anti-template constraints and chart/source rules.
- [ ] Generic `experience/` has no case-specific business assumptions.
- [ ] Harness scripts remain deterministic and local.
