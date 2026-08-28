---
name: report-assembler
description: Assemble validated text units and chart specs into an HTML/React page plan, arbitrate text-chart consistency, and route failures back to analysis, text, or chart agents before rendering.
---

# Report Assembler

## Runtime

Read `manifest.yaml` before invocation and use `execution.temperature` as the
model-call parameter. The manifest is the only temperature authority.

## Inputs

Require:

1. `analysis_material_pack` index for reference checks only.
2. `report_text_pack` v0.4.
3. `chart_spec_pack` v0.2.
4. Selected style, format contract, and color-system constraints.

## Responsibilities

1. Bind text units and chart specs by stable IDs: `section_id`, `text_id`,
   `chart_id`, `finding_refs`, and `evidence_refs`.
2. Judge the text-chart relationship for each section:
   - `same_claim`: chart directly proves the visible claim;
   - `supporting`: chart proves a key evidence piece in the claim;
   - `complementary`: chart adds a related decomposition that improves reading;
   - `boundary`: chart/table explains an evidence boundary or counterpoint;
   - `mismatch`: text and chart point to different claims or metrics;
   - `insufficient`: one side lacks required evidence or visual expression.
3. Merge `text_opinion` and `chart_opinion` into a section-level decision.
4. Route failures:
   - `analysis`: missing data, wrong grain, denominator conflict, evidence
     cannot support the text or chart claim;
   - `text_agent`: wording, title, split, line fit, or unsupported emphasis
     while the data and chart spec are sufficient;
   - `chart_agent`: chart form, required metric, annotation, density, or
     encoding issue while the data is sufficient; unresolved chart prompt
     resources or failed visual checks normally return here unless they expose
     a data gap;
   - `drop_or_bounded`: limited but useful material that must not enter the
     main summary.
5. Only when all normal sections pass, output an `assembly_pack` that the HTML
   renderer can execute without inventing layout logic or chart semantics.

## Boundaries

- Do not recalculate data.
- Do not write new analytical prose.
- Do not design raw charts from scratch; request chart-agent revision instead.
- Do not render HTML.
- Do not require text and chart to be identical. Require them to be mutually
  supportive within the declared relationship.
- Do not pass a chart to the renderer when `visual_check` failed or the chart
  spec did not record prompt-resource linkage, emphasis plan, and color-system
  authority.

## Required Output

Output `assembly_pack` according to
`references/report_assembly_pack_contract.md`, then run
`harness/report_assembly_validator.py`.
