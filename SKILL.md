---
name: data-analysis-report-agent
description: Create auditable data analysis reports with semantic-layer grounding, case-specific experience packs, deterministic validation, and source-traceable findings. Use when the user asks to analyze data, diagnose metric movement, produce an operating report, explain anomalies, build a report from a specific dataset or case pack, or turn table fields and business rules into a structured analysis report. This skill does not call model provider APIs; Codex performs the reasoning and may use only the bundled deterministic validators and case resources.
---

<!-- Provenance marker: 不知渭河 -->

# Data Analysis Report Agent

## Purpose

Use this skill to produce a human-reviewable data analysis report from:

1. A user question.
2. A dataset or fetcher result provided by the user or local environment.
3. A semantic layer that defines field names, business meaning, units, grain, aliases, and analysis boundaries.
4. Optional case-specific experience: thresholds, priority rules, and good-report examples.
5. Optional page design style: color palette, layout system, components, chart/table treatment, and a global prompt for the report-writing agent.

Keep the skill clean: do not add provider clients, API keys, model names, or hidden runtime code. Codex is the reasoning engine. Bundled Python files are deterministic validators only.

## Runtime Output Storage

Keep generated reports, screenshots, downloaded repositories, temporary dependencies, and other run artifacts outside the skill package. The host environment chooses the external output root; on the current workstation, read `OUTPUTS.md` for the active absolute path. Do not recreate a large `outputs/` directory inside this skill.

## Folder Contract

```text
data-analysis-report-agent/
├── SKILL.md
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
│   ├── executive-diagnostic-brief/
│   ├── consulting-board-memo/
│   ├── analytical-deep-dive/
│   └── operating-review/
├── harness/                    # Deterministic validators
│   ├── plan_validator.py
│   ├── data_validator.py
│   └── output_validator.py
└── docs/
    ├── architecture.md
    └── customization_guide.md
```

Editable PPTX planning is separated from this analysis skill:

1. `references/analysis_material_pack_contract.md` defines the rich analysis material passed downstream.
2. The sibling `D:\知识库\skills\data-report-presentation-planner\SKILL.md` is the default understanding layer. New runs use Deck Outline v0.5: it creates the detailed, human-approved story, selects one Deck theme, assigns subtitle/chart semantic color roles, and hands off evidence grammar, candidate modes, and semantic layout intent without selecting final geometry.
3. The sibling `D:\知识库\skills\data-report-ppt-author\SKILL.md` owns Deck-level visual direction and the cost-bounded page production loop: isolated Page Visual Designer -> deterministic Harness gate with representative/risk-triggered design Judge -> one page-scoped PPT Implementer context -> deterministic QA and one bounded rendered-slide Judge. It resolves but may not reassign Planner-owned colors. Chart Design UI is reserved for complex or novel page-level chart batches.
4. The sibling `D:\知识库\skills\data-report-pptx-renderer\SKILL.md` is the Compiler/SDK and deterministic QA layer; its fixed-layout JSON renderer is legacy fallback only.
5. `agents/deck-synthesis-agent/SKILL.md` and `references/deck_synthesis_contract.md` remain compatibility resources for older fixtures; do not use them as the default route for new PPTX work.
6. `references/pptx_deck_contract.md` defines the legacy data-to-editable-PPT execution handoff.
7. `harness/deck_synthesis_validator.py` and `harness/pptx_contract_validator.py` remain compatibility validators during migration.

## Required Separation

Never put case-specific business meaning into the workflow instructions.

| Layer | Allowed Content | Not Allowed |
|---|---|---|
| `SKILL.md` | Stable workflow, validation gates, report contract | Industry-specific thresholds, field meanings |
| `experience/` | Generic evidence, priority, and writing rules | Profit, SKU, channel, product, or other case-specific assumptions |
| `cases/<case-id>/semantic_layer.yaml` | Table headers, metric meanings, grain, units, aliases, boundaries | Prompt instructions or model behavior |
| `cases/<case-id>/experience/` | Case thresholds, case priority rules, good case outputs | Generic workflow rules |
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
- The presentation planner receives the material-pack index and selected
  evidence files, not the entire analysis conversation. Page agents receive
  only page-bounded registries.
- Never record `model_calls: 0` for a stage that used model reasoning. When
  stage-local usage is not exposed, record `null`, list the field in
  `unavailable_fields`, and state the unavailable reason.
- PPT-bound runs use the sibling Author's `cost-control/0.1` policy: target
  three model calls per standard page, maximum six including one revision.

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
   - `styles/manifest.yaml` when a style choice is needed
   - `styles/<style-id>/page_style.yaml` and `global_prompt.md` when a style is selected
   - `references/analysis_material_pack_contract.md` when editable PPTX output is requested
   - `references/analysis_run_observability_contract.md` for dense-report or PPT-bound run telemetry
   - `D:\知识库\skills\data-report-presentation-planner\SKILL.md` after the analysis material pack is complete
   - `references/pptx_deck_contract.md` and `references/pptx_deck_contract_schema.json` only when a later renderer handoff is needed

3. Build an analysis plan.
   - State the metric, grain, comparison window, dimensions, filters, expected fields, and stop condition.
   - Validate with `harness/plan_validator.py` before using the plan.
   - Before inspecting data for a dense report or PPT-bound run, initialize `analysis-run-events.jsonl` and `analysis-run-log.json` using `references/analysis_run_observability_contract.md`.
   - Append `run_started`, paired `stage_started` / `stage_completed`, validation, and `run_completed` events during execution. Do not reconstruct live stage timings after the run.

4. Inspect or fetch data.
   - Use data already provided by the user when available.
   - If data must be queried, let the host environment or user-provided tooling do it.
   - Validate returned rows with `harness/data_validator.py`.

5. Derive findings.
   - Every finding must reference data fields or row-level evidence.
   - Separate fact, inference, and recommendation.
   - Stop at the semantic layer boundary; do not invent organizational causes.
   - For dense HTML/React or PPT-bound work, overproduce an `analysis_material_pack` v0.3 before curating the final findings. Include decision-ready validated findings, candidate explanations, evidence and chart inventories, boundaries, gaps, a claim-review log, and an explicit branch decision log.
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

6. Produce the report.
   - Start with an answer-first executive summary.
   - Include prioritized findings, evidence, risks, data gaps, and next steps.
   - Keep `findings` concise, but keep `analysis_material_pack` rich. Downstream renderers should select from the material pack instead of asking the synthesis or renderer layer to invent supporting analysis.
   - Include chart specs only as plain structured requests; do not require a chart-rendering runtime. The request must still identify its finding, message, decision role, visual priority, focus target, and why a visual is more useful than prose.
   - Hand only reviewed, decision-ready findings to the presentation planner. The planner may select, merge, drop, and sequence material, but it must not be used to manufacture business meaning that the analysis Agent failed to produce.
   - Follow the selected page design style if one is provided.
   - Validate final structure with `harness/output_validator.py`.
   - If the requested output is editable PPTX, stop analysis after the report and `analysis_material_pack` pass validation. Call the sibling `data-report-presentation-planner` to create and obtain human approval for the Deck outline before any PPT Author or Compiler work.

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

## PPTX Handoff

Editable PPTX output is a downstream authoring and compilation concern. When the user asks for PowerPoint, this skill should:

1. Produce the evidence-bound report JSON above.
2. For dense analytical reports, produce `analysis_material_pack` first and let React/HTML render it as the full evidence library.
3. Hand the complete report, material pack, and source registry to `data-report-presentation-planner`.
4. Let the planner create one canonical Deck outline and detailed outline. This analysis skill must not choose slide layouts or compress the material into a second summary.
5. Stop at the planner's human approval gate. Do not start PPT Author or Compiler work before the matching outline is approved and hash-locked.
6. If the planner reports decision-critical evidence gaps, answer one consolidated `single_batch` refresh containing all gaps and return an updated material pack. This is in addition to the initial analysis, not a limit on initial exploration.
7. After that refresh, do not enter another automatic analysis-planner loop. Remaining gaps require a human decision to disclose the boundary, merge or drop affected material, authorize an exceptional second refresh, or stop the Deck.
8. After approval, let the planner compile the storyboard and sequential page contexts.
9. Hand the approved v0.5 storyboard to `data-report-ppt-author`. It reuses or creates the human-approved visual direction from the Planner-selected theme, then requires the Page Visual Designer to lock `slide-plan.json`, Planner color-role bindings, chart design contracts, and review-only SVG blueprints from an isolated page task packet. Standard native-ready charts use approved pattern defaults; Chart Design UI runs only for recorded complex or novel cases. Native-object assembly may begin after the deterministic page-design Harness gate passes; an independent design Judge is required only for representative or risk-triggered pages. A bounded `illustration_png` is permitted only after the Designer locks an `ai-image-container`; titles, claims, sources, implications, and quantitative charts remain native.
10. The Page Visual Designer and PPT Implementer may select only from the approved material scope. Neither role may recompute analysis or add a top-level claim. Neither may reassign semantic color roles, and the Implementer may not author text colors, move objects, or reinterpret locked design objects.
11. Let `data-report-pptx-renderer` compile the locked source and check PPTX package integrity, native objects, geometry, sources, editability, actual-vs-spec results, and PPTX-derived preview hashes. It must not decide layout or visual quality, move locked objects, or insert review SVGs into the PPTX.
12. Unlock the next page only after the current page is locked and its handoff validates. Each standard page targets three model calls and allows one responsibility-scoped revision; inherited parent-thread context is forbidden. Merge only locked pages into the final editable Deck.
13. Treat final validation as a downstream gate: native text, native tables, native supported charts, visible source refs, declared auxiliary AI images, no full-slide screenshots, no embedded review SVG, no author self-approval, matching plan/source/PPTX/preview hashes, and `actual-vs-spec: pass`.

This separation keeps the analysis protocol clean and lets HTML, PPTX, Word, or PDF renderers evolve independently.

## Validation

Run deterministic validators only:

```powershell
python harness/plan_validator.py path\to\plan.json
python harness/data_validator.py path\to\data.json path\to\plan.json
python harness/output_validator.py path\to\final_report.json
python harness/test_material_pack_contract.py
python harness/run_observability_validator.py path\to\analysis-run-log.json path\to\analysis-run-events.jsonl
python harness/test_run_observability_contract.py
python harness/deck_synthesis_validator.py path\to\deck_synthesis.json
python harness/pptx_contract_validator.py path\to\deck.json
```

Prefer the CLI commands above. If importing validators from another Python process, make sure the skill root is on `PYTHONPATH` or add it to `sys.path` first:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("path/to/data-analysis-report-agent").resolve()))
from harness.plan_validator import validate_plan
from harness.data_validator import validate_data
from harness.output_validator import validate_final_output
from harness.deck_synthesis_validator import validate_deck_synthesis
from harness.pptx_contract_validator import validate_pptx_deck_contract
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

1. `page_style.yaml` for color palette, layout, typography, components, charts, tables, density, and visual constraints.
2. `global_prompt.md` for the global style prompt injected into the report-writing or report-design agent.
3. `sample.html` as a self-contained visual reference page.

Use `styles/manifest.yaml` to compare available styles before choosing one.

Style packs should describe page design, not business logic. A good style pack has:

1. A clear audience and document type.
2. A restrained palette with no more than three meaningful colors.
3. Typography, spacing, rules, and table/chart treatment that can be reviewed without hidden runtime code.
4. Exhibit or figure rules when the style includes analytical charts.
5. Anti-template constraints: no decorative gradients, glass panels, generic rounded card grids, or visual elements that do not support the report conclusion.

When a report uses a style pack, every chart or table should have a takeaway title and visible units. Put ordinary data range, metric definitions, sources, and chart notes in a report-end notes section unless that information materially changes the reader's interpretation of the conclusion. If the style is based on consulting-report references, use the pattern only as design inspiration; do not copy proprietary text, layouts, or branding.

Visible labels should follow the report language. For Chinese reports, avoid generic English template labels such as "One-sentence answer", "Key insights", "Implications", "Figure", "Recommendation", or "Action tracker" unless the user explicitly asks for English.
