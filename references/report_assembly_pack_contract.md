# Report Assembly Pack Contract

Use this contract after `report_text_pack` and `chart_spec_pack` v0.2 pass their
own validators, and before HTML/React rendering. Version `0.1` makes page
assembly and text-chart arbitration explicit.

## Required Shape

```json
{
  "assembly_pack": {
    "contract_version": "0.1",
    "runtime_policy": {
      "manifest_ref": "agents/report-assembler/manifest.yaml",
      "configured_temperature": 0.0,
      "applied_temperature": 0.0
    },
    "sections": [],
    "bounded_modules": [],
    "assembly_opinions": [],
    "renderer_handoff": {}
  }
}
```

## Section Assembly

Each normal section records:

- `section_id`
- `order`
- `text_refs`: title, subtitle, body blocks, visual captions, and summary refs.
- `chart_refs`: one or more chart IDs from `chart_spec_pack`.
- `layout`: `prose_then_chart`, `chart_then_notes`, `text_chart_columns`,
  `table_first`, or `text_only`.
- `relationship`: `same_claim`, `supporting`, `complementary`, or `boundary`.
- `render_status`: `ready`.

## Assembly Opinion

The assembler must write an opinion for every section:

```json
{
  "section_id": "section_growth_quality",
  "text_status": "pass",
  "chart_status": "pass",
  "text_chart_relation": "supporting",
  "assembly_status": "ready",
  "route": null,
  "reason": "The chart shows sales growth and profit-rate decline required by the title.",
  "backfill_requests": []
}
```

Allowed `text_chart_relation` values:

- `same_claim`
- `supporting`
- `complementary`
- `boundary`
- `mismatch`
- `insufficient`

Allowed `assembly_status` values:

- `ready`
- `return_to_analysis`
- `return_to_text_agent`
- `return_to_chart_agent`
- `drop_or_bounded`

Allowed `route` values:

- `analysis`
- `text_agent`
- `chart_agent`
- `drop_or_bounded`
- `null`

The assembler does not require text and chart to be identical. It requires that
the chart prove, support, complement, or bound the text claim. If the title says
profit rate declined but the chart only shows sales growth, the relation is
`mismatch` and the route is `chart_agent` or `analysis`, depending on whether
the required profit-rate data exists.

## Renderer Handoff

`renderer_handoff` is the only structure the HTML renderer should execute. It
contains ordered blocks and stable references, not new claims. The renderer may
add fixed labels, units, anchors, and source labels, but must not change text,
chart semantics, or assembly order.
