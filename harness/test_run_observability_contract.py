#!/usr/bin/env python3
"""Regression checks for the analysis run observability contract."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from harness.run_observability_validator import read_jsonl, validate_analysis_run_log


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    valid = _read(SKILL_DIR / "examples" / "analysis_run_log_sample.json")
    events = read_jsonl(SKILL_DIR / "examples" / "analysis_run_events_sample.jsonl")

    ok, messages = validate_analysis_run_log(valid, events)
    _assert(ok, f"valid fixture failed: {messages}", errors)

    missing_duration = copy.deepcopy(valid)
    missing_duration["stages"][0]["duration_seconds"] = None
    duration_ok, duration_messages = validate_analysis_run_log(missing_duration, events)
    _assert(
        not duration_ok and any("duration_seconds" in item for item in duration_messages),
        "live stage without duration must fail",
        errors,
    )

    missing_unavailable_reason = copy.deepcopy(valid)
    missing_unavailable_reason["usage"]["input_tokens"] = None
    usage_ok, usage_messages = validate_analysis_run_log(missing_unavailable_reason, events)
    _assert(
        not usage_ok and any("input_tokens" in item and "unavailable_fields" in item for item in usage_messages),
        "null usage without unavailable_fields must fail",
        errors,
    )

    duplicate_stage = copy.deepcopy(valid)
    duplicate_stage["stages"].append(copy.deepcopy(duplicate_stage["stages"][0]))
    duplicate_stage["summary"]["stage_count"] = 2
    duplicate_ok, duplicate_messages = validate_analysis_run_log(duplicate_stage)
    _assert(
        not duplicate_ok and any("duplicate stage_id" in item for item in duplicate_messages),
        "duplicate stage id must fail",
        errors,
    )

    backfilled = copy.deepcopy(valid)
    backfilled["recording_mode"] = "backfilled"
    stage = backfilled["stages"][0]
    stage["measurement_status"] = "not_recorded"
    stage["started_at"] = None
    stage["completed_at"] = None
    stage["duration_seconds"] = None
    stage["measurement_gap_reason"] = "Historical run captured only total duration."
    backfill_ok, backfill_messages = validate_analysis_run_log(backfilled)
    _assert(backfill_ok, f"honest historical backfill should pass: {backfill_messages}", errors)

    if errors:
        print("RUN_OBSERVABILITY_TESTS_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RUN_OBSERVABILITY_TESTS_PASS: live, backfill, and 3 negative gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())

