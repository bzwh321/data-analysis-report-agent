---
name: report-text-controller
description: Control the full pre-HTML report text workflow using its Agent manifest runtime. Use after ReAct analysis and visual selection to create bounded per-unit context packets, run Chain of Verification with backfill to the analysis Agent, dispatch unit writing and independent adversarial review, judge whether research questions are solved, and build a progressive report title and summary without expanding each writer context.
---

# Report Text Controller

## Role

Own the report-level question, context routing, verification state, and final
text assembly. Read `manifest.yaml` before invocation and use its
`execution.temperature` as the model-call parameter. The manifest is the only
temperature authority.

Do not write every section in one full-context pass. Keep the complete material
registry in the controller context and send each writer or reviewer only one
bounded `unit_packet`.

## Workflow

1. Read the report question, business context, material-pack index,
   `chart_spec_pack`, chart opinions, and locked visual plan.
2. Assign every selected visual to a report position before prose is written.
   The visual must already have `claim_to_prove`, required series, required
   annotations, and chart-side fail conditions from the Chart Spec Agent.
3. Create one `unit_packet` per bounded chart/table question. Normally it has
   one primary visual; include multiple tightly related visuals only when they
   jointly answer the same question. Include only the selected finding,
   evidence, visual, layout, and minimal previous/next handoff refs.
4. Run Chain of Verification for that unit. Ask concrete checking questions
   about the metric state, numerator, denominator, comparison, driver,
   counterevidence, boundary, or other relevant mechanism.
   If the prospective conclusion names a driver such as seasonality, promotion,
   channel, price, volume, mix, or cost, add at least one
   `role=driver_decomposition` question that distinguishes the relevant
   alternatives. A time pattern by itself does not establish its driver.
5. When a critical answer is missing, internally inconsistent, or conflicts
   with the locked material, send one consolidated backfill request for that
   unit to the ReAct analysis Agent. A hypothesis that is cleanly disproved by
   evidence is a valid answer, not an automatic gap. Update the packet with
   returned evidence and verify again. Continue only while the next probe can
   change the conclusion; otherwise mark a bounded unresolved result.
6. Dispatch the verified packet to `report-text-editor` using that Agent's
   manifest runtime configuration.
7. Dispatch the same packet plus the finished unit text, but no writer hidden
   reasoning, to `report-text-adversarial-reviewer` in an independent context.
8. Route reviewer failures back to the writer, ReAct analysis, or Controller
   according to the failed boundary. Do not let the reviewer silently rewrite.
9. Handle thin-result failures with only three issue codes:
   `evidence_does_not_support_conclusion` routes to ReAct;
   `expression_title_or_line_fit` routes to the Editor; and
   `no_report_value` routes to the Controller and is omitted.
10. After all accepted units return, judge each report research question as
   `answered`, `partially_answered`, or `unanswered`.
11. Build the report title, subtitle, and `summary_chain` from accepted section
    titles, subtitles, verified evidence, and resolution status. Use a
    progressive order such as goal attainment -> core metric -> key question ->
    authorized solution or evidence boundary. Do not require a fixed number of
    sections, charts, or summary paragraphs.
    Keep verification questions, evidence ledgers, logic-chain steps, and
    evidence/conclusion/boundary labels internal. Visible report prose is an
    ordered sequence of complete conclusion sentences.
12. When a unit has limited but still useful evidence, move it to
    `bounded_modules`. Do not reference it from `summary_chain`, report title,
    or report subtitle. Mark it detachable so the renderer produces an
    independent removable module. If it has no report value, record it in
    `omitted_units` and do not render it.
13. Run `harness/report_text_validator.py`. Hand text to HTML only after pass.
14. Hand the validated text pack to `report-assembler`, not directly to HTML.
    If the assembler returns `route=analysis`, wait for the updated material
    pack and rerun the affected chart and text units. If it returns
    `route=chart_agent`, keep the approved text but require a revised chart
    spec. If it returns `route=text_agent`, keep the chart spec but rewrite the
    affected unit.

## Authority

The Controller may select, sequence, merge, drop, request backfill, and decide
whether a report question has been solved. It may not recalculate data, upgrade
causal strength, invent a solution, design final charts, or expose unsupported
certainty in the report title or summary.
