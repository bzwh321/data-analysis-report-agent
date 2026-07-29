#!/usr/bin/env python3
"""Validate analysis run observability logs without inspecting model reasoning."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "0.1"
RECORDING_MODES = {"live", "backfilled"}
EXECUTION_MODES = {"deterministic", "llm_assisted", "mixed"}
RUN_STATUSES = {"completed", "failed", "partial"}
STAGE_STATUSES = {"completed", "failed", "partial"}
MEASUREMENT_STATUSES = {"measured", "not_recorded"}
MARGINAL_VALUES = {"none", "low", "medium", "high", "unknown"}
DECISION_IMPACTS = {"none", "minor", "material", "unknown"}
CONTINUE_RECOMMENDATIONS = {"continue", "stop", "human_review"}
EVENT_TYPES = {
    "run_started",
    "stage_started",
    "stage_completed",
    "branch_decision",
    "validation_completed",
    "run_completed",
}
USAGE_FIELDS = (
    "model_calls",
    "subagent_calls",
    "input_tokens",
    "output_tokens",
    "estimated_cost",
)
STAGE_METRIC_FIELDS = (
    "rows_read",
    "rows_output",
    "evidence_added",
    "findings_added",
    "chart_candidates_added",
    "gaps_closed",
    "candidate_branches_entered",
    "branches_continued",
    "branches_stopped",
    *USAGE_FIELDS,
)


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _validate_nullable_metrics(
    container: object,
    fields: tuple[str, ...],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(container, dict):
        errors.append(f"{label} must be an object")
        return
    unavailable = container.get("unavailable_fields", [])
    if not isinstance(unavailable, list) or any(not isinstance(item, str) for item in unavailable):
        errors.append(f"{label}.unavailable_fields must be a string list")
        unavailable = []
    unavailable_set = set(unavailable)
    for field in fields:
        if field not in container:
            errors.append(f"{label}.{field} is required")
            continue
        value = container[field]
        if value is None:
            if field not in unavailable_set:
                errors.append(f"{label}.{field} is null but not listed in unavailable_fields")
            continue
        if field in {"estimated_cost"}:
            valid = _is_non_negative_number(value)
        else:
            valid = _is_non_negative_int(value)
        if not valid:
            errors.append(f"{label}.{field} must be a non-negative number or null")


def _validate_value_assessment(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return
    if value.get("marginal_value") not in MARGINAL_VALUES:
        errors.append(f"{label}.marginal_value is invalid")
    if value.get("decision_impact") not in DECISION_IMPACTS:
        errors.append(f"{label}.decision_impact is invalid")
    if value.get("continue_recommendation") not in CONTINUE_RECOMMENDATIONS:
        errors.append(f"{label}.continue_recommendation is invalid")
    if not isinstance(value.get("reason"), str) or not value.get("reason", "").strip():
        errors.append(f"{label}.reason must be non-empty")


def validate_analysis_run_log(
    run_log: object,
    events: list[dict[str, Any]] | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(run_log, dict):
        return False, ["analysis run log must be an object"]

    if run_log.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"contract_version must be {CONTRACT_VERSION}")
    run_id = run_log.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        errors.append("run_id must be non-empty")
    recording_mode = run_log.get("recording_mode")
    if recording_mode not in RECORDING_MODES:
        errors.append("recording_mode must be live or backfilled")
    if run_log.get("execution_mode") not in EXECUTION_MODES:
        errors.append("execution_mode is invalid")
    if run_log.get("status") not in RUN_STATUSES:
        errors.append("status is invalid")
    for field in ("started_at", "completed_at"):
        if not _valid_timestamp(run_log.get(field)):
            errors.append(f"{field} must be an ISO-8601 timestamp")
    if not _is_non_negative_number(run_log.get("duration_seconds")):
        errors.append("duration_seconds must be non-negative")
    if not isinstance(run_log.get("events_ref"), str) or not run_log.get("events_ref", "").strip():
        errors.append("events_ref must be non-empty")

    _validate_nullable_metrics(run_log.get("usage"), USAGE_FIELDS, "usage", errors)

    stages = run_log.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("stages must be a non-empty list")
        stages = []
    stage_ids: set[str] = set()
    for index, stage in enumerate(stages):
        label = f"stages[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{label} must be an object")
            continue
        stage_id = stage.get("stage_id")
        if not isinstance(stage_id, str) or not stage_id.strip():
            errors.append(f"{label}.stage_id must be non-empty")
        elif stage_id in stage_ids:
            errors.append(f"duplicate stage_id: {stage_id}")
        else:
            stage_ids.add(stage_id)
        for field in ("stage_type", "question"):
            if not isinstance(stage.get(field), str) or not stage.get(field, "").strip():
                errors.append(f"{label}.{field} must be non-empty")
        if stage.get("status") not in STAGE_STATUSES:
            errors.append(f"{label}.status is invalid")
        measurement_status = stage.get("measurement_status")
        if measurement_status not in MEASUREMENT_STATUSES:
            errors.append(f"{label}.measurement_status is invalid")
        for field in ("input_refs", "output_refs"):
            if not isinstance(stage.get(field), list):
                errors.append(f"{label}.{field} must be a list")
        if measurement_status == "measured":
            for field in ("started_at", "completed_at"):
                if not _valid_timestamp(stage.get(field)):
                    errors.append(f"{label}.{field} must be an ISO-8601 timestamp for measured stages")
            if not _is_non_negative_number(stage.get("duration_seconds")):
                errors.append(f"{label}.duration_seconds must be non-negative for measured stages")
        else:
            if recording_mode == "live":
                errors.append(f"{label} cannot be not_recorded in a live run")
            if not isinstance(stage.get("measurement_gap_reason"), str) or not stage.get("measurement_gap_reason", "").strip():
                errors.append(f"{label}.measurement_gap_reason is required when telemetry was not recorded")
        _validate_nullable_metrics(stage.get("metrics"), STAGE_METRIC_FIELDS, f"{label}.metrics", errors)
        _validate_value_assessment(stage.get("value_assessment"), f"{label}.value_assessment", errors)

    summary = run_log.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        if summary.get("stage_count") != len(stages):
            errors.append("summary.stage_count must equal len(stages)")
        for field in (
            "validated_findings_added",
            "evidence_files_added",
            "chart_candidates_added",
            "consecutive_zero_yield_stage_count",
            "duplicate_probe_count",
        ):
            if not _is_non_negative_int(summary.get(field)):
                errors.append(f"summary.{field} must be a non-negative integer")
        for field in ("overthinking_flags", "warnings"):
            if not isinstance(summary.get(field), list):
                errors.append(f"summary.{field} must be a list")
        if summary.get("consecutive_zero_yield_stage_count", 0) >= 2:
            warnings.append("WARNING: two or more consecutive zero-yield stages require explicit continuation review")
        if summary.get("duplicate_probe_count", 0) > 0:
            warnings.append("WARNING: duplicate probes were recorded")

    if events is not None:
        _validate_events(events, run_id, recording_mode, stage_ids, errors)

    return not errors, errors + warnings


def _validate_events(
    events: list[dict[str, Any]],
    run_id: object,
    recording_mode: object,
    stage_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty list")
        return
    event_ids: set[str] = set()
    event_types: list[str] = []
    started: set[str] = set()
    completed: set[str] = set()
    for index, event in enumerate(events):
        label = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        if event.get("event_version") != CONTRACT_VERSION:
            errors.append(f"{label}.event_version must be {CONTRACT_VERSION}")
        if event.get("run_id") != run_id:
            errors.append(f"{label}.run_id does not match run log")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            errors.append(f"{label}.event_id must be non-empty")
        elif event_id in event_ids:
            errors.append(f"duplicate event_id: {event_id}")
        else:
            event_ids.add(event_id)
        if not _valid_timestamp(event.get("timestamp")):
            errors.append(f"{label}.timestamp must be an ISO-8601 timestamp")
        event_type = event.get("event_type")
        if event_type not in EVENT_TYPES:
            errors.append(f"{label}.event_type is invalid")
            continue
        event_types.append(event_type)
        if event_type in {"stage_started", "stage_completed"}:
            stage_id = event.get("stage_id")
            if stage_id not in stage_ids:
                errors.append(f"{label}.stage_id is not present in run log stages")
            if event_type == "stage_started":
                started.add(stage_id)
            else:
                completed.add(stage_id)
    if recording_mode == "live":
        if "run_started" not in event_types or "run_completed" not in event_types:
            errors.append("live event stream must include run_started and run_completed")
        if started != stage_ids or completed != stage_ids:
            errors.append("live event stream must pair stage_started and stage_completed for every stage")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number} is not a JSON object")
        events.append(value)
    return events


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python run_observability_validator.py <analysis-run-log.json> [analysis-run-events.jsonl]")
        return 2
    run_log_path = Path(sys.argv[1])
    run_log = json.loads(run_log_path.read_text(encoding="utf-8-sig"))
    events = read_jsonl(Path(sys.argv[2])) if len(sys.argv) == 3 else None
    valid, messages = validate_analysis_run_log(run_log, events)
    print("ANALYSIS_RUN_OBSERVABILITY_PASS" if valid else "ANALYSIS_RUN_OBSERVABILITY_FAILED")
    for message in messages:
        print(f"- {message}")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())

