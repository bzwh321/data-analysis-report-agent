# Chart Spec Pack Contract

Use this contract after `analysis_material_pack` and before report assembly.
Version `0.3` makes chart design an explicit intermediate artifact. The chart
agent does not render HTML and does not write report prose.

## Required Shape

```json
{
  "chart_spec_pack": {
    "contract_version": "0.3",
    "runtime_policy": {
      "manifest_ref": "agents/chart-spec-agent/manifest.yaml",
      "configured_temperature": 0.0,
      "applied_temperature": 0.0
    },
    "charts": [],
    "chart_opinions": []
  }
}
```

## Chart Spec

Each chart records:

- `chart_id`: stable ID also used by the assembler and renderer.
- `source_chart_candidate_ref`: ID from `analysis_material_pack.chart_candidates`.
- `section_ref`: intended report section.
- `claim_to_prove`: the visible claim, evidence piece, complement, or boundary
  this chart must support.
- `relationship_intent`: `same_claim`, `supporting`, `complementary`, or
  `boundary`.
- `chart_type`: chart form such as `dual_metric_line`, `annotated_line`,
  `sorted_horizontal_bar`, `bridge_bar`, `small_multiples`, or
  `evidence_table`.
- `prompt_resources`: chart-form prompt lookup result. It must include
  `index_ref`, `lookup_key`, `status`, and `resource_ref` or `fallback_reason`.
- `required_series`: non-empty list of series with metric, values, unit, role,
  and evidence refs.
- `series_completeness`: the declared chart domain and completeness rule. It
  must require every `required_series` to render across the full chart domain
  unless a series is explicitly marked as an annotation-only overlay.
- `focus_metric`: the metric that must be visually emphasized.
- `comparison_basis`: period, segment, denominator, or benchmark.
- `required_annotations`: labels or marks that must appear in the rendered
  chart.
- `emphasis_plan`: conclusion-driven emphasis choices such as value labels,
  shaded windows, callouts, icons, reference lines, or boxed text. It must also
  state how complete base-series visibility is
  preserved. This is principle-based, not a fixed template.
- `annotation_plan`: execution-ready in-chart annotation instructions. Each
  item must define `type`, `anchor`, `text`, `placement_channel`,
  `avoid_regions`, `max_chars`, `min_gap_px`, and `icon_id` when an icon is
  used.
- `fail_if_missing`: specific omissions that invalidate the rendered chart.
- `style_constraints`: palette role, semantic signal use, density and label
  rules.
- `visual_check`: first-pass result, checked items, revision count, judge usage,
  collision model, and remaining issues.

The chart may be different from the prose, but it cannot be unrelated. If a
section title says profit rate declined, the chart must show the profit-rate
movement or a validated decomposition that directly proves that decline.

Completeness is separate from emphasis. The visible text may mention only the
key years, categories, or period, but the chart must still satisfy its chart
form. If the chart type is a yearly line, every required yearly value in the
declared domain must be drawn. A local emphasis layer can sit near the full
line; it cannot be the only geometry for that metric. The emphasis also cannot
visually erase the full line. If the overlay covers the base series so the
reader cannot perceive the complete metric path, the chart fails visual check.

Annotation is separate from decoration. In-chart explanatory text is allowed,
but it must be short, anchored to the relevant data mark or region, and placed
with explicit collision avoidance. Do not use decorative decline lines,
diagonal arrows, large red boxes, bracket overlays, or fake legend series for
annotations. Use icons only from
`assets/chart-icons/chart-emphasis-icons.svg`. Red, yellow, and green are
reserved for universal semantic signals; other concepts must use neutral gray.

Allowed `annotation_plan.type` values:

- `point_label`
- `endpoint_label`
- `range_band`
- `reference_line`
- `short_callout`
- `icon_callout`
- `detail_column`
- `in_chart_note`

Allowed `placement_channel` values:

- `near_data_point`
- `near_bar_end`
- `inside_plot_reserved`
- `outside_plot_left`
- `outside_plot_right`
- `above_plot`
- `below_plot`
- `detail_column`

Every annotation must include `avoid_regions`, such as `axis_ticks`,
`axis_labels`, `legend`, `data_marks`, `data_mark_bboxes`, `value_labels`,
`callout_boxes`, `plot_edges`, `x_axis_tick_band`, or `other_annotations`.
The renderer must treat these as protected regions.

Every annotation must include `min_gap_px`. Use `8` as the minimum for normal
labels and `12` or more when the annotation is near axes, tick labels, legends,
plot edges, point markers, bars, bubbles, or callout rectangles.

The collision object is the full rendered annotation geometry: text bounding
box, callout rectangle, icon viewport, leader line, and padding. The protected
data object is also the full mark geometry: bar rectangle, point-marker radius,
bubble radius, band label, and axis/tick text bounding box. Passing a text-only
overlap check is not sufficient.

Renderer collision checks must use explicit geometry roles:

- `data_mark`: bars, points, lines, bubbles, and the full radius/area of marks.
- `axis_or_legend`: axes, ticks, tick labels, unit labels, and legends.
- `annotation_text`: visible annotation text.
- `annotation_container`: the annotation's own background box or icon frame.
- `reference_region`: intentional background bands or benchmark regions.

`annotation_text` may overlap its own `annotation_container` and may sit inside
an intentional `reference_region` when that is the declared placement channel.
It may not overlap `data_mark`, `axis_or_legend`, or another annotation's
container/text, and it must still satisfy `min_gap_px` against protected
regions.

The chart spec must make the broad conclusion visually legible. A reader should
be able to see the core movement, gap, anomaly, or decomposition within five
seconds without relying on prose-only explanation.

The visual check must include collision status for all chart text, callout
boxes, icons, legends, axes, ticks, labels, and data-mark bounding boxes. If
rendered geometry cannot avoid overlap, clipping, or the declared `min_gap_px`,
the chart opinion must be `needs_chart_revision` with route `chart_agent`.

`visual_check.collision_model` is required:

```json
{
  "checked_geometry_roles": [
    "data_mark",
    "axis_or_legend",
    "annotation_text",
    "annotation_container",
    "reference_region"
  ],
  "text_only_check_allowed": false,
  "min_gap_enforced": true
}
```

## Chart Opinion

Every chart has an opinion:

```json
{
  "chart_id": "chart_growth_quality",
  "status": "pass",
  "concerns": [],
  "required_backfill": [],
  "route": null
}
```

Allowed `status` values:

- `pass`
- `needs_analysis_backfill`
- `needs_chart_revision`
- `drop_or_bounded`

Allowed `route` values:

- `analysis`
- `chart_agent`
- `drop_or_bounded`
- `null`

Use `needs_analysis_backfill` when data, grain, denominator, comparison, or
source evidence is missing or inconsistent. Use `needs_chart_revision` only when
the data is sufficient but the chart form, series, annotation, density, or
encoding is wrong.

If prompt resources are unresolved, use `pass` only when the fallback principles
are sufficient and the concern is explicitly recorded. If missing prompt
resources cause weak chart grammar, use `needs_chart_revision`.

## Handoff Rule

The Report Assembler receives `chart_spec_pack` and `report_text_pack` together.
If either side reports a material issue, the assembler decides the route and the
affected unit must be rerun after backfill or revision.
