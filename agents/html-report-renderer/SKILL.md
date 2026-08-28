---
name: html-report-renderer
description: Render a validated assembly pack into HTML or React using the frozen format contract, selected style, color system, approved text pack, and approved chart spec pack. Copy approved analytical strings exactly, keep bounded findings as detachable modules outside the full-report summary, and never draft, strengthen, or redesign analytical conclusions.
---

# HTML Report Renderer

## Runtime

Read `manifest.yaml` before invocation and use
`execution.temperature` as the model-call parameter. The manifest is the only
temperature authority.

## Inputs

Require a `report_text_pack` that has passed
`harness/report_text_validator.py`, a `chart_spec_pack` that has passed
`harness/chart_spec_validator.py`, and an `assembly_pack` that has passed
`harness/report_assembly_validator.py`, plus the format contract, selected
style, the selected style's `sample.html`, and color system. Treat the
sample as a fixed visual reference for rhythm and layout, not as a source of
business claims.

## Rendering Rules

1. Copy approved analytical strings exactly. Add only fixed section numbers,
   units, source labels, and accessibility labels.
   Render visible section prose only from `body_blocks`; never render
   verification questions, evidence ledgers, logic-chain steps, or
   `conclusion.render_plan.segments`.
2. Render normal `sections` in the report reading path declared by
   `assembly_pack.renderer_handoff` and allow only their
   accepted title/subtitle text into the full-report summary.
3. Render every `bounded_module` as a separate element with
   `data-module-type="bounded"` and `data-removable="true"`. Place it outside
   the full-report summary and normal analytical-section numbering.
4. Render a bounded module's `statements` as complete sentences in their given
   order. Do not add visible `现有证据`、`结论`、`证据边界` or similar answer
   labels, and do not restyle the module as a recommendation or management
   conclusion.
5. Do not render `controller_resolution.omitted_units`.
6. Respect every declared line plan. If actual browser geometry exceeds it,
   return the unit to `report-text-editor`; do not shorten it in markup.
7. Run desktop and narrow-width visual review before delivery.
8. Render charts only from `chart_spec_pack`. Do not infer chart semantics from
   prose. If a chart spec says the focus metric is profit rate, the rendered
   SVG/canvas/config must show that metric and its required annotations.
9. If the rendered chart cannot satisfy `required_series`,
   `series_completeness`, `required_annotations`, or `fail_if_missing`, stop
   and return to `report-assembler`; do not silently simplify the chart.
   Highlight layers must be rendered as overlays on top of complete base
   series. They may not replace missing points, bars, or lines from the base
   series.
   Render in-chart annotations only from `annotation_plan`. Do not invent
   decorative decline lines, diagonal arrows, large red boxes, bracket overlays,
   fake legend series, or unplanned callouts. When an icon is requested, use
   only `assets/chart-icons/chart-emphasis-icons.svg`; red/yellow/green are
   limited to semantic signal icons, and other icon concepts render in neutral
   gray.
   In-chart explanatory text is allowed, but it must obey the declared
   placement channel and avoid regions. After rendering, check text/icon
   bounding boxes and callout rectangle boxes against axes, ticks, legends,
   labels, plot edges, data-mark bounding boxes, and other annotations. Include
   bar rectangles, point-marker radius, bubble radius, shaded-band labels, icon
   viewports, and callout padding in the collision model. If any annotation
   overlaps, clips, enters the x-axis tick band, covers a data mark, or violates
   declared `min_gap_px`, return the chart to `report-assembler` as
   `needs_chart_revision`; do not hide, shorten, or reposition analytical text
   without a revised chart spec.
   Assign collision roles while rendering SVG/canvas-equivalent layers:
   `data_mark`, `axis_or_legend`, `annotation_text`, `annotation_container`,
   and `reference_region`. Allow annotation text to sit on its own background
   container and inside a declared reference region; reject annotation text that
   overlaps data marks, axis/legend geometry, plot edges, or another
   annotation's text/container. This avoids both false passes and false alarms.
10. For `internet-reporting`, reject short-prose/tall-chart side-by-side layouts
   that leave a large blank area under the prose. Use continuous document flow:
   claim sentences first, embedded evidence next, reading notes immediately
   after the evidence.
11. Prefer one visible statement per line when it fits the planned measure. If
   the approved copy cannot fit cleanly, render the approved point list; do not
   convert it into an awkward multi-line paragraph.
12. Use only colors supplied by the selected color-system palette and the
    universal semantic signal palette. Do not introduce local theme hues in
    HTML, CSS, SVG, canvas, or chart configuration.
