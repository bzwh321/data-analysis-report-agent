---
name: data-analysis-report-agent
description: Create auditable data analysis reports with semantic-layer grounding, case-specific experience packs, deterministic validation, source-traceable findings, and human-authored high-density HTML/React visual design. Use when the user asks to analyze data, diagnose metric movement, produce an operating report, explain anomalies, build a report from a specific dataset or case pack, turn table fields and business rules into a structured analysis report, or design an evidence-dense data-report page without generic AI card patterns. This skill does not call model provider APIs; Codex performs the reasoning and may use only the bundled deterministic validators and case resources.
---

<!-- Provenance marker: 不知渭河 -->

# Data Analysis Report Agent

## Purpose

Use this skill to produce a human-reviewable data analysis report from:

1. A user question.
2. A dataset or fetcher result provided by the user or local environment.
3. A semantic layer that defines field names, business meaning, units, grain, aliases, and analysis boundaries.
4. Optional case-specific experience: thresholds, priority rules, and good-report examples.
5. Required pre-render text governance for HTML/React: a Report Text Controller routes bounded unit packets and owns final resolution, a Report Text Editor writes one unit at a time, and an independent adversarial reviewer challenges the result before markup. Every Agent's actual model temperature comes from its own `manifest.yaml`.
6. Optional page style: document character, component relationships, and chart/table treatment for the renderer.
7. Optional HTML theme-palette selection from `styles/color-system/color_system.yaml`; the same module always supplies the cross-report red/yellow/green semantic signal layer for icons and charts. Color is not owned by the format contract or a style pack. User-added palettes are allowed only through the color-system registry or its declared `custom-palettes/` source folder.

Keep the skill clean: do not add provider clients, API keys, model names, or hidden runtime code. Codex is the reasoning engine. Bundled Python files are deterministic validators only.

## Runtime Output Storage

Keep generated reports, screenshots, downloaded repositories, temporary dependencies, and other run artifacts outside the skill package. The host environment chooses the external output root. Do not recreate a large `outputs/` directory inside this skill.

## Folder Contract

```text
data-analysis-report-agent/
├── SKILL.md
├── agents/
│   ├── report-text-controller/
│   │   ├── SKILL.md
│   │   └── manifest.yaml
│   ├── chart-spec-agent/
│   │   ├── SKILL.md
│   │   └── manifest.yaml
│   ├── report-text-editor/
│   │   ├── SKILL.md
│   │   └── manifest.yaml
│   ├── report-text-adversarial-reviewer/
│   │   ├── SKILL.md
│   │   └── manifest.yaml
│   ├── report-assembler/
│   │   ├── SKILL.md
│   │   └── manifest.yaml
│   └── html-report-renderer/
│       ├── SKILL.md
│       └── manifest.yaml
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
│   ├── color-system/
│   ├── editorial-evidence-report/
│   └── internet-reporting/
├── harness/                    # Deterministic validators
│   ├── plan_validator.py
│   ├── data_validator.py
│   ├── agent_runtime_validator.py
│   ├── chart_spec_validator.py
│   ├── report_text_validator.py
│   ├── report_assembly_validator.py
│   └── output_validator.py
├── references/
│   ├── chart_spec_pack_contract.md
│   ├── report_assembly_pack_contract.md
│   ├── report_text_pack_contract.md
│   ├── chart_prompt_resource_index.md
│   └── report_writing_micro_prompt.md
└── docs/
    ├── architecture.md
    └── customization_guide.md
```

`references/analysis_material_pack_contract.md` defines the rich, renderer-neutral analysis material that approved downstream tools may reuse. Presentation authoring and compilation are outside this skill.

## Required Separation

Never put case-specific business meaning into the workflow instructions.

| Layer | Allowed Content | Not Allowed |
|---|---|---|
| `SKILL.md` | Stable workflow, validation gates, report contract | Industry-specific thresholds, field meanings |
| `experience/` | Generic evidence, priority, and writing rules | Profit, SKU, channel, product, or other case-specific assumptions |
| `cases/<case-id>/semantic_layer.yaml` | Table headers, metric meanings, grain, units, aliases, boundaries | Prompt instructions or model behavior |
| `cases/<case-id>/experience/` | Case thresholds, case priority rules, good case outputs | Generic workflow rules |
| `agents/report-text-controller/` | Report-question decomposition, bounded context routing, verification/backfill control, answer-state judgment, and progressive summary synthesis | Data calculation, prose drafting, HTML, unsupported advice |
| `agents/chart-spec-agent/` | Claim-bound chart specification, required series and annotations, chart-side opinion, and analysis backfill request when visual evidence cannot prove the claim | Report prose, data recalculation, HTML/SVG rendering, page assembly |
| `agents/report-text-editor/` | Temperature-0 unit-level wording, evidence-to-conclusion logic, title derivation, concise paragraph planning, and line-fit declarations | Full-report traversal, data queries, recalculation, new findings, unrequested advice, HTML |
| `agents/report-text-adversarial-reviewer/` | Independent challenge of evidence, verification completeness, logic, usefulness, tone, and line fit | Full material pack, writer hidden reasoning, direct rewriting, HTML |
| `agents/report-assembler/` | Text-chart relationship arbitration, section assembly, route-back decision, and renderer handoff | New data analysis, prose drafting, raw chart design, HTML rendering |
| `agents/html-report-renderer/` | Manifest-configured exact HTML/React rendering from assembly handoff, line-fit return, and detachable bounded-module output | New analytical prose, chart semantics, summary changes, rendering omitted units |
| `styles/<style-id>/` | Page design tokens, layout, components, chart/table style, global prompt | Business thresholds, field meanings, case assumptions |
| `harness/` | Deterministic validation scripts | LLM calls, network calls, credentials |

## Cost Discipline

- Keep analysis flexible, but run one primary analysis context per dataset and
  decision question. Analytical rounds are logical stages, not invitations to
  spawn one subagent per branch.
- Profile the source once, persist canonical evidence extracts, and reuse them.
  Do not reread the full workbook or raw tables for every finding.
- Batch related deterministic calculations in SQL/Python or host tools, then
  perform one evidence-and-claim synthesis pass. Overproduction means a rich
  material pack, not repeated model narration of the same evidence.
- Use subagents only for genuinely independent sources or specialist methods
  that can run from a bounded packet. Full parent-conversation inheritance is
  forbidden.
- Never record `model_calls: 0` for a stage that used model reasoning. When
  stage-local usage is not exposed, record `null`, list the field in
  `unavailable_fields`, and state the unavailable reason.

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
   - `references/human_authored_html_design_system.md` for every HTML or React report
   - `styles/color-system/color_system.yaml` for every HTML or React report
   - `styles/manifest.yaml` when a style choice is needed
   - `styles/<style-id>/page_style.yaml`, `global_prompt.md`, and `sample.html` when a style is selected
   - `references/analysis_material_pack_contract.md` for dense HTML/React output or renderer-neutral downstream reuse
   - `references/chart_prompt_resource_index.md`, `references/chart_spec_pack_contract.md`, `references/report_text_pack_contract.md`, `references/report_writing_micro_prompt.md`, all HTML-report Agent `SKILL.md` files, and their `manifest.yaml` files for every HTML or React report
   - `references/analysis_run_observability_contract.md` for dense-report run telemetry

3. Build an analysis plan.
   - State the metric, grain, comparison window, dimensions, filters, expected fields, and stop condition.
   - Validate with `harness/plan_validator.py` before using the plan.
   - Before inspecting data for a dense report, initialize `analysis-run-events.jsonl` and `analysis-run-log.json` using `references/analysis_run_observability_contract.md`.
   - Append `run_started`, paired `stage_started` / `stage_completed`, validation, and `run_completed` events during execution. Do not reconstruct live stage timings after the run.

4. Inspect or fetch data.
   - Use data already provided by the user when available.
   - If data must be queried, let the host environment or user-provided tooling do it.
   - Validate returned rows with `harness/data_validator.py`.

5. Derive findings.
   - Every finding must reference data fields or row-level evidence.
   - Separate fact, inference, and recommendation.
   - Stop at the semantic layer boundary; do not invent organizational causes.
   - For dense HTML/React work, overproduce an `analysis_material_pack` v0.3 before curating the final findings. Include decision-ready validated findings, candidate explanations, evidence and chart inventories, boundaries, gaps, a claim-review log, and an explicit branch decision log.
   - Run a business-question ReAct loop, not only a data-retrieval loop. Begin with `decision_to_support`; after each probe ask whether the new evidence changes issue materiality, investigation priority, intervention choice, monitoring need, or the next validation question.
   - Let the analysis goal, evidence quality, impact, and marginal explanatory value determine depth. Roughly three levels may be used as a search-budget heuristic, but never require a fixed number of levels, drivers, children, charts, or pages.
   - Record every explored candidate branch as `continue` or `stop` with a reviewable reason. A `continue` branch must name the next probe; a `stop` branch must explain why further analysis is not worth doing or cannot be supported.
   - Write a provisional statement for every proposed validated finding, then review factual support, business meaning, decision direction, causal strength, alternative explanations, and visual evidence. Rewrite the statement when evidence is sufficient but the wording is weak.
   - When a calculation or evidence gap blocks an accurate conclusion, return to analysis with one consolidated next probe. Do not rewrite around a factual error. Material that remains unsupported or has no decision value belongs in candidate explanations, gaps, or stopped branches rather than `validated_findings`.
   - Give every validated finding a scope, causal status, management implication, recommended use, and next validation question where applicable. A ranking fact such as "X is the weakest slice" is incomplete until its management use is explicit.
   - Bind every chart candidate to the finding and message it proves. Declare whether it is dominant, supporting, or optional and identify the focus target. Use `driver` only for a supported decomposition or explanatory relationship within its declared boundary; use `issue_judgement` or `counterevidence` for operating signals that do not establish a cause. When a central quantitative change has a useful comparison, do not leave that change only in prose.
   - At the end of every analysis round, log elapsed time, row and artifact deltas, evidence/finding/chart/gap deltas, branch counts, model/subagent usage, and a concise marginal-value assessment. Write explicit zeroes for calls that did not occur; use `null` only with an unavailable reason.
   - Count a logical analytical stage separately from a model call. Do not spawn
     a new model context merely to preserve stage labels in the observability
     log.
   - Treat two consecutive zero-yield stages, repeated probes, or rising runtime without decision impact as review warnings. They require an explicit continuation reason but never impose a fixed analysis depth.
   - Use `references/analysis_material_pack_contract.md` when the report needs dense React/HTML output or downstream PPT reuse.

6. Govern all HTML/React text before markup.
   - Complete `analysis_material_pack`, then run `agents/chart-spec-agent/SKILL.md` for every selected chart/table candidate. The chart Agent turns each visual into `chart_spec_pack` units with `claim_to_prove`, required metrics, required annotations, failure conditions, prompt-resource references, conclusion-driven emphasis, visual-check records, and a `chart_opinion`. It selects the chart form from the data conclusion, reads the matching chart-form prompt through `references/chart_prompt_resource_index.md`, applies selected style principles, and takes color only from `styles/color-system/color_system.yaml`. If chart data, grain, denominator, comparison, or evidence is missing or inconsistent, return one consolidated request to the ReAct/data layer before writing or rendering around the gap. If the first visual check fails, allow at most two internal chart revisions and use judge mode; if it passes, do not use judge mode.
   - Lock every selected chart/table's data, structure, intended report position, and `claim_to_prove` before writing titles or prose. Position includes column, grid span, available width, and expected title/conclusion line count. A chart is not a decoration: it must prove, support, complement, or bound the section text.
   - Before every model call, read the target Agent's `manifest.yaml` and pass `execution.temperature` to the runtime. Prompt text is not a temperature source. Validate all six manifests with `harness/agent_runtime_validator.py` and record configured/applied execution receipts.
   - Run `agents/report-text-controller/SKILL.md`. It decomposes the report question into bounded report units and sends the writer only the selected findings, evidence, visual, business context, and layout context for that unit. A unit normally has one primary visual; several tightly related visuals may share a unit only when they jointly answer the same question. Never resend the full report context for each chart.
   - For each unit, run a Chain of Verification before prose. Ask multiple evidence questions with different roles, such as metric movement, revenue, cost, mix/scope, and counterevidence. When a critical answer is missing or contradictory, return one consolidated backfill request to the ReAct/data layer, register the returned evidence, and rerun the affected verification questions. Do not write around a gap.
   - A time sequence alone does not establish seasonality or another driver. If a prospective conclusion names seasonality, promotion, channel, price, volume, mix, cost, or another explanatory path, require a completed `role=driver_decomposition` verification question that distinguishes relevant alternatives; otherwise return to ReAct before writing.
   - Only after verification is `verified`, run `agents/report-text-editor/SKILL.md` with `references/report_writing_micro_prompt.md`. Build the unit internally in reverse: verified evidence -> relationship -> conclusion -> visual takeaway -> title/subtitle. Keep that evidence chain private. Reader-facing `body_blocks` must be complete sentences, one conclusion per sentence in reading order, without visible `证据/结论/边界/判断` answer labels or validation-chain disclaimers such as `以下结论只使用...`. Keep any aggregate split plan `internal_only=true` and give each visible sentence its own line-fit plan. Use `display_mode=line` only for statements planned as one visual line; when the statement cannot fit cleanly and compression would remove evidence, split it into `display_mode=point` blocks.
   - Run `agents/report-text-adversarial-reviewer/SKILL.md` in a separate context. It receives only the unit packet, verification record, final visible strings, and layout plan; it never receives the full material pack or writer hidden reasoning. Limit thin-result routing to exactly three categories: evidence exists but cannot support the conclusion -> ReAct; redundant expression, inaccurate title, or uncontrolled wrapping -> writer; insufficient data with no report value -> controller omission.
   - Let the controller decide whether each report question is `answered`, `partially_answered`, or `unanswered`. Build the full-report conclusion only from approved normal-section titles and subtitles as a progressive logic chain. Do not impose a fixed number of sections, visuals, or summary items.
   - When evidence is limited but still useful, output it in top-level `bounded_modules` with `summary_eligible=false`, `removable=true`, and `render_disposition=detachable_boundary`. Never reference it from the summary, report title, or report subtitle. When it has no report value, record `no_report_value` in `omitted_units` and do not render it.
   - Use a calm, restrained, objective voice. Every claim title must directly answer its declared research question. Do not use dramatic language, responsibility attribution, causal upgrades, or business recommendations without an explicit user request.
   - Produce `report_text_pack` v0.4 according to `references/report_text_pack_contract.md` and validate it with `harness/report_text_validator.py`. Produce `chart_spec_pack` v0.3 according to `references/chart_spec_pack_contract.md` and validate it with `harness/chart_spec_validator.py`. If the host cannot apply an Agent manifest temperature, stop with `temperature_control_unavailable`.
   - Run `agents/report-assembler/SKILL.md` with the latest `analysis_material_pack`, `report_text_pack`, and `chart_spec_pack`. The Assembler merges text opinions and chart opinions, judges each section's text-chart relation (`same_claim`, `supporting`, `complementary`, `boundary`, `mismatch`, or `insufficient`), and routes failures to `analysis`, `text_agent`, `chart_agent`, or `drop_or_bounded`. If a route returns to analysis, update the material pack and rerun the affected chart and text agents before assembly. Do not start HTML or React markup until `harness/report_assembly_validator.py` passes.

7. Produce the report.
   - Start with an answer-first executive summary.
   - Include prioritized findings, evidence, risks, and data gaps. Include next steps or recommendations only when the user explicitly requests them and the text contract authorizes them.
   - Keep `findings` concise, but keep `analysis_material_pack` rich. Downstream renderers should select from the material pack instead of asking the synthesis or renderer layer to invent supporting analysis.
   - Include chart specs as structured, claim-bound execution contracts, not vague chart wishes. Each chart must identify its finding, message, decision role, visual priority, focus target, required metrics, annotations, comparison basis, and failure conditions.
   - For HTML or React, invoke `agents/html-report-renderer` with its manifest and render only the validated `assembly_pack` handoff, approved text strings, and approved chart specs. Copy analytical strings without rewriting or strengthening them; add only fixed structural labels such as section numbers, units, and source labels. Render section prose only from approved `body_blocks`; render charts only from approved `chart_spec_pack`; never expose verification questions, evidence ledgers, logic-chain steps, chart opinions, assembly opinions, or render-plan segments. Render `bounded_modules` as independent removable modules outside the summary and normal section numbering; never render `omitted_units`. Treat `references/human_authored_html_design_system.md` as the frozen format contract and `styles/color-system/color_system.yaml` as the separate color authority. Do not introduce colors outside the active color-system palette and universal semantic signal palette; user-added palettes must be registered in the color-system registry or declared `custom-palettes/` source folder before use. When a style is selected, read its fixed `page_style.yaml`, `global_prompt.md`, and `sample.html`; use the sample as a visual rhythm reference, not as business text. Before markup, write a one-line reading path, map content units to grid spans, and create a private alignment ledger that assigns every structural edge to the shared page grid. Use `editorial-evidence-report` when the user has not selected another HTML style; a selected style may change the document character but may not weaken the text contract, format contract, chart contract, assembly contract, or color authority.
   - Follow the selected page design style if one is provided.
   - Render HTML or React at desktop width and one narrower width. Review the five-second scan, content-to-container fit, chart anatomy, chart-to-prose adjacency, and responsive behavior. Compare rendered structural edges against the alignment ledger: shared anchors must agree within `1px`, and accidental `2-16px` near misses fail delivery.
   - Validate final structure with `harness/output_validator.py`. The earlier `report_text_validator.py` pass remains mandatory and may not be replaced by visual review.

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
  "analysis_material_pack": {
    "contract_version": "0.3",
    "analysis_goal": {
      "question": "...",
      "audience": "...",
      "decision_to_support": "...",
      "time_scope": "..."
    },
    "metric_context": [
      {
        "metric_id": "target_metric",
        "definition": "...",
        "unit": "...",
        "grain": "...",
        "source_refs": ["source_1"]
      }
    ],
    "validated_findings": [
      {
        "finding_id": "finding_1",
        "statement": "...",
        "scope": "...",
        "importance": "high",
        "confidence": "high",
        "causal_status": "descriptive",
        "management_implication": "...",
        "recommended_use": "investigate",
        "next_validation_question": "...",
        "evidence_refs": ["evidence_1"],
        "boundary_refs": []
      }
    ],
    "candidate_explanations": [],
    "evidence_inventory": [
      {
        "evidence_id": "evidence_1",
        "type": "table",
        "subject": "...",
        "grain": "...",
        "data_ref": "...",
        "quality": "validated",
        "source_refs": ["source_1"],
        "availability": "ready"
      }
    ],
    "chart_candidates": [
      {
        "chart_id": "chart_1",
        "question_answered": "...",
        "finding_refs": ["finding_1"],
        "message_to_prove": "...",
        "decision_role": "issue_judgement",
        "visual_priority": "dominant",
        "focus_target": "...",
        "why_visual_not_text": "...",
        "evidence_refs": ["evidence_1"],
        "recommended_form": "line",
        "editability_need": "native_chart_preferred"
      }
    ],
    "boundaries": [],
    "gaps": [],
    "claim_review_log": {
      "entries": [
        {
          "finding_id": "finding_1",
          "candidate_statement": "...",
          "final_statement": "...",
          "review_status": "rewritten",
          "review_reason": "...",
          "checks": {
            "factually_supported": true,
            "business_meaning_clear": true,
            "decision_direction_clear": true,
            "causal_strength_appropriate": true,
            "alternative_explanations_considered": true,
            "visual_evidence_sufficient": true
          }
        }
      ]
    },
    "analysis_decision_log": {
      "entries": [
        {
          "branch_id": "branch_1",
          "parent_id": null,
          "question": "...",
          "decision": "stop",
          "reason": "...",
          "evidence_refs": ["evidence_1"],
          "impact_estimate": "high",
          "confidence": "high",
          "marginal_explanatory_value": "low",
          "next_probe": null,
          "depth": 1
        }
      ]
    }
  },
  "report_text_pack": {
    "contract_version": "0.4",
    "contract_ref": "references/report_text_pack_contract.md",
    "required_before": ["html", "react"]
  },
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
python harness/test_material_pack_contract.py
python harness/run_observability_validator.py path\to\analysis-run-log.json path\to\analysis-run-events.jsonl
python harness/test_run_observability_contract.py
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

1. `page_style.yaml` for document character, layout patterns, components, charts, tables, density, and visual constraints. It references but does not redefine the format contract or color system.
2. `global_prompt.md` for the global style prompt injected into the report renderer. It may arrange approved text but may not author analytical prose.
3. `sample.html` as the fixed visual reference file for that style. The renderer should consult it for layout rhythm and component relationships, but must not copy its business claims unless the report text pack supplies them.

Use `styles/manifest.yaml` to compare available styles before choosing one.

For HTML or React reports, first read `references/human_authored_html_design_system.md`. It is the frozen cross-style format contract. Then read `styles/color-system/color_system.yaml`, the only source for palette and color usage. Style packs may specialize audience, document character, and content rhythm, but they must preserve the format contract and must not define local colors. User-added palettes may live in the color-system registry or the declared `styles/color-system/custom-palettes/` folder; unregistered colors are not allowed in report HTML, CSS, SVG, canvas, or chart configuration. When the user does not choose a style, use `editorial-evidence-report` as the default HTML reference.

The renderer must also receive a validated `report_text_pack`. Style prompts may control hierarchy, placement, typography, chart treatment, and emphasis, but they may not create, shorten, combine, strengthen, or recommend through visible text.

Style packs should describe page design, not business logic. A good style pack has:

1. A clear audience and document type.
2. A direct reference to the shared color system, with no local palette or color semantics.
3. Typography, spacing, rules, explicit grid spans, one page-grid token set, an alignment ledger, and table/chart treatment that can be reviewed without hidden runtime code.
4. Exhibit or figure rules when the style includes analytical charts.
5. Content-fit constraints that explain when a container is justified and how its span follows content length, importance, and comparison needs.
6. Anti-template constraints: no decorative gradients, glass panels, generic rounded card grids, or visual elements that do not support the report conclusion.

When a report uses a style pack, every chart or table should have a takeaway title and visible units. Put ordinary data range, metric definitions, sources, and chart notes in a report-end notes section unless that information materially changes the reader's interpretation of the conclusion. If the style is based on consulting-report references, use the pattern only as design inspiration; do not copy proprietary text, layouts, or branding.

Visible labels should follow the report language. For Chinese reports, avoid generic English template labels such as "One-sentence answer", "Key insights", "Implications", "Figure", "Recommendation", or "Action tracker" unless the user explicitly asks for English.
