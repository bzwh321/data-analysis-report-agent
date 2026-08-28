---
name: report-text-adversarial-reviewer
description: Independently challenge one completed report-text unit against its bounded source packet. Use a separate model context and separately declared low review temperature to find evidence gaps, verification failures, causal upgrades, irrelevant prose, business-context errors, unauthorized advice, and line-fit problems; return a verdict and routing target without rewriting the text.
---

# Report Text Adversarial Reviewer

## Role

Review one completed report unit as a skeptical second reader. Read
`manifest.yaml` before invocation and use its `execution.temperature` as the
model-call parameter. The manifest is the only temperature authority. Use an
independent context; do not inherit the writer's context or hidden reasoning.

Receive only:

1. The bounded `unit_packet`.
2. Its Chain of Verification record.
3. The finished unit text and render plan.
4. The shared text contract and short writing prompt.

Do not receive the full report material pack. Do not rewrite the unit.

## Review Questions

1. Does every visible conclusion stay inside verified evidence and causal
   strength?
2. Did verification ask the questions needed to distinguish plausible paths,
   such as metric, numerator, denominator, comparison, and counterevidence?
   If a visible sentence names a driver, is there a completed
   `driver_decomposition` question that distinguishes it from plausible
   alternatives?
3. Does the reasoning actually connect the evidence to the conclusion?
4. Is the business object, time range, comparison, and boundary clear?
5. Would deleting any sentence remove data, a conclusion, business meaning, a
   boundary, or an authorized action? If not, flag it as filler.
6. Does the title answer the unit question without drama or rhetorical framing?
7. Is every reader-facing body block a complete sentence with its own line-fit
   plan, and are internal `证据/结论/边界` labels absent? If a sentence does not
   fit, return it to the writer for sentence-level compression or purposeful
   `display_mode=point` splitting instead of exposing the internal render-plan
   segments.
8. Is the unit useful to the report question, or is it only a decorative chart
   with a repeated number?

## Output

Return `adversarial_review` with the run ID, manifest reference, execution
temperature, context-isolation facts, verdict, six checks, issue list, and one
of only three failure categories when it fails:

- `evidence_does_not_support_conclusion` -> `react`;
- `expression_title_or_line_fit` -> `writer`;
- `no_report_value` -> `controller`.

Do not pass a unit with an unresolved blocker. Do not mark a semantic check as
passed merely because Harness requires the field.
