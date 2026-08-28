# Chart Prompt Resource Index

Use this index to connect the HTML chart Agent with reusable chart-prompt
resources. Keep concrete prompt files outside the report run when they already
live in the public GitHub prompt repository or its local mirror. This file is
the stable routing layer; update it when the repository path changes.

## Authority Order

1. Active color system: `styles/color-system/color_system.yaml`.
2. Selected report style: `styles/<style-id>/global_prompt.md`,
   `page_style.yaml`, and `sample.html`.
3. Chart-form prompt from the external visual-prompt repository or approved
   local mirror.
4. General chart design principles below.

Color rules always come from the color system, even when a chart-form prompt
contains its own color examples.

## External Repository Linkage

Record one of the following before a production run:

```yaml
visual_prompt_repository:
  source_type: github_public_repo_or_local_mirror
  repo_url: null
  local_mirror: null
  required_index_file: null
  status: unresolved
```

If the repository is unresolved, the chart Agent may use the general principles
in this file, but must record `prompt_resource_status: fallback_used` in the
chart spec and list the missing chart-form prompt in `chart_opinion.concerns`.

## Chart Form Routing

Use the chosen chart form to locate the matching prompt:

| Need | Preferred chart forms | Prompt lookup key |
|---|---|---|
| Time movement | `annotated_line`, `dual_metric_line`, `small_multiples_line` | `line`, `dual_axis_or_dual_metric`, `small_multiples` |
| Contribution / bridge | `bridge_bar`, `waterfall`, `sorted_horizontal_bar` | `bridge`, `waterfall`, `bar_rank` |
| Rank / comparison | `sorted_horizontal_bar`, `dot_plot`, `lollipop` | `bar_rank`, `dot_plot` |
| Distribution | `histogram`, `box_plot`, `heatmap_matrix` | `distribution`, `heatmap` |
| Relationship | `scatter`, `bubble`, `paired_comparison` | `scatter`, `relationship` |
| Detail evidence | `evidence_table`, `highlight_table`, `matrix_table` | `table`, `matrix` |

## General Chart Principles

- Let the chart answer the same business question as the section, but do not
  require it to mirror every sentence.
- Draw the complete chart grammar for each required metric. The text can state
  only the key finding, but a line chart must still draw the full line over the
  declared domain, a bar chart must draw all required bars, and a scatter chart
  must render all required points. Use highlight layers only as overlays.
- Keep the complete base series perceptible after highlighting. Do not cover a
  base line with a thick highlight in a way that makes the series appear
  partially drawn; use a nearby bracket, band, secondary stroke, endpoint label,
  or restrained segment emphasis.
- Make the conclusion visible before reading the caption: the focus metric,
  key movement, abnormal window, or main contributor should stand out.
- Prefer direct labels over legends when space allows.
- Remove decorative grid lines; keep only the grid or reference line needed to
  compare values.
- Protect text: labels, callouts, units, and source notes must not cover data
  marks or collide with each other.
- Keep enough density: a chart should show comparison context, benchmark,
  decomposition, or relevant counterpoint when a single series is too thin to
  support the section claim.
- Use marks intentionally: value label, shaded window, reference line, boxed
  note, endpoint emphasis, icon, dashed uncertainty line, or segmented color.
- Keep annotations near the data they explain. Use short callouts inside the
  chart; move full explanatory sentences,同比/目标达成 background, caveats, and
  business interpretation into prose or reading notes.
- Do not let long detail text share the plot area with gridlines or bars. For
  bar charts with supplemental details, use a separated label/detail column and
  reserve the plot region for bars, axes, and direct value labels.
- For red/yellow/green semantic marks, use the color-system meaning rules and
  pair color with label/shape/line style.

## Visual Check

The chart Agent must create a private visual-check record before handoff:

```json
{
  "first_pass_status": "pass",
  "checked_items": [
    "text_overlap",
    "label_legibility",
    "conclusion_visibility",
    "information_density",
    "gridline_and_ink",
    "palette_compliance"
  ],
  "revision_count": 0,
  "judge_mode_used": false
}
```

If `first_pass_status` is `fail`, revise no more than two times and run
judge-mode review. Judge mode should explain whether the remaining failure is
analysis data, chart design, or renderer execution.
