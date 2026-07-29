# Analysis Run Observability Contract v0.1

This contract makes a non-trivial analysis run reviewable for cost, depth, and
marginal value. It records operational facts and explicit decisions only. It
must never contain hidden chain-of-thought.

## Required artifacts

Every dense-report or PPT-bound analysis run writes both files from the start
of the run:

1. `analysis-run-events.jsonl`: append-only intermediate events.
2. `analysis-run-log.json`: final, human-readable run summary.

The final report and `run-manifest.json` should reference both artifacts.

## Event stream

Each JSONL line is one object with:

```json
{
  "event_version": "0.1",
  "event_id": "evt-001",
  "run_id": "run-001",
  "timestamp": "2026-07-16T10:00:00+08:00",
  "event_type": "stage_started"
}
```

Allowed event types are:

- `run_started`
- `stage_started`
- `stage_completed`
- `branch_decision`
- `validation_completed`
- `run_completed`

`stage_started` records `stage_id`, `stage_type`, optional `round`, the
reviewable `question`, and `input_refs`. `stage_completed` records the same
`stage_id`, status, duration, output refs, metrics, and value assessment.

`branch_decision` may record a branch question, `continue` or `stop`, evidence
refs, next probe, and a concise explicit reason. It must not contain private
reasoning traces.

## Final run log

```json
{
  "contract_version": "0.1",
  "run_id": "run-001",
  "recording_mode": "live",
  "execution_mode": "deterministic",
  "status": "completed",
  "started_at": "2026-07-16T10:00:00+08:00",
  "completed_at": "2026-07-16T10:10:00+08:00",
  "duration_seconds": 600,
  "source_ref": "source-profile.json",
  "events_ref": "analysis-run-events.jsonl",
  "usage": {},
  "stages": [],
  "summary": {}
}
```

`recording_mode` is `live` for new runs. `backfilled` is allowed only when a
historical run did not capture stage telemetry. Backfilled logs must identify
every unknown field and must not invent timings or usage.

### Usage

`usage` contains:

- `model_calls`
- `subagent_calls`
- `input_tokens`
- `output_tokens`
- `estimated_cost`
- `unavailable_fields`

Zero calls must be written as `0` only when no model reasoning occurred. A
model-backed host stage must not be reported as zero merely because stage-local
telemetry is unavailable. In that case write `null`, include the field name in
`unavailable_fields`, and add a concise unavailable reason.

### Stage record

Every stage contains:

- `stage_id`, `stage_type`, optional `round`, and `question`
- `status`: `completed`, `failed`, or `partial`
- `measurement_status`: `measured` or `not_recorded`
- `started_at`, `completed_at`, and `duration_seconds`
- `input_refs` and `output_refs`
- `metrics`
- `value_assessment`

`metrics` contains the following counters when applicable:

- `rows_read`, `rows_output`
- `evidence_added`, `findings_added`, `chart_candidates_added`, `gaps_closed`
- `candidate_branches_entered`, `branches_continued`, `branches_stopped`
- `model_calls`, `subagent_calls`, `input_tokens`, `output_tokens`, `estimated_cost`
- `unavailable_fields`

`value_assessment` contains:

- `marginal_value`: `none`, `low`, `medium`, `high`, or `unknown`
- `decision_impact`: `none`, `minor`, `material`, or `unknown`
- `continue_recommendation`: `continue`, `stop`, or `human_review`
- `reason`: a short, reviewable explanation based on output delta and evidence

This is not a fixed-depth gate. Analysis may continue at any depth when the
expected decision value is material and evidence supports the next probe.

### Summary and overthinking signals

`summary` contains:

- `stage_count`
- `validated_findings_added`
- `evidence_files_added`
- `chart_candidates_added`
- `consecutive_zero_yield_stage_count`
- `duplicate_probe_count`
- `overthinking_flags`
- `warnings`

The following are warnings, not automatic stop rules:

- two consecutive completed stages add no evidence, findings, chart
  candidates, or closed gaps;
- a probe repeats the same metric, grain, filters, and question;
- a stage consumes materially more time or model calls without changing the
  supported decision;
- branching grows without a stated expected value or stop condition.

Continuing after a warning requires an explicit reason in the next stage's
value assessment. Depth, branch count, chart count, and page count remain
open-ended and are never global quotas.

## Validation

```powershell
python harness/run_observability_validator.py path\to\analysis-run-log.json path\to\analysis-run-events.jsonl
python harness/test_run_observability_contract.py
```
