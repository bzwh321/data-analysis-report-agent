#!/usr/bin/env python3
"""Regression checks for decision-ready material packs and compatibility."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from harness.output_validator import validate_final_output


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    valid = _read(SKILL_DIR / "examples" / "final_report_open_material_pack_sample.json")
    legacy = _read(SKILL_DIR / "examples" / "final_report_sales_decline_sample.json")

    ok, messages = validate_final_output(valid)
    _assert(ok, f"v0.3 valid fixture failed: {messages}", errors)

    v02_compat = copy.deepcopy(valid)
    v02_compat["analysis_material_pack"]["contract_version"] = "0.2"
    v02_compat["analysis_material_pack"].pop("claim_review_log", None)
    for finding in v02_compat["analysis_material_pack"]["validated_findings"]:
        for field in (
            "scope",
            "causal_status",
            "management_implication",
            "recommended_use",
            "next_validation_question",
        ):
            finding.pop(field, None)
    for chart in v02_compat["analysis_material_pack"]["chart_candidates"]:
        for field in (
            "finding_refs",
            "message_to_prove",
            "decision_role",
            "visual_priority",
            "focus_target",
            "why_visual_not_text",
        ):
            chart.pop(field, None)
    compat_ok, compat_messages = validate_final_output(v02_compat)
    _assert(compat_ok, f"v0.2 compatibility fixture failed: {compat_messages}", errors)
    _assert(
        any("v0.2 兼容模式" in item for item in compat_messages),
        "v0.2 compatibility fixture should emit an upgrade warning",
        errors,
    )

    legacy_ok, legacy_messages = validate_final_output(legacy)
    _assert(legacy_ok, f"legacy fixture failed: {legacy_messages}", errors)
    _assert(
        any("旧版 driver-tree" in item for item in legacy_messages),
        "legacy fixture should emit an upgrade warning",
        errors,
    )

    missing_branch = copy.deepcopy(valid)
    missing_branch["analysis_material_pack"]["analysis_decision_log"]["entries"] = [
        entry
        for entry in missing_branch["analysis_material_pack"]["analysis_decision_log"]["entries"]
        if entry["branch_id"] != "candidate_north_region"
    ]
    missing_ok, missing_messages = validate_final_output(missing_branch)
    _assert(
        not missing_ok and any("缺少候选解释分支" in item for item in missing_messages),
        "missing candidate branch decision must fail",
        errors,
    )

    missing_probe = copy.deepcopy(valid)
    missing_probe["analysis_material_pack"]["analysis_decision_log"]["entries"][0][
        "next_probe"
    ] = None
    probe_ok, probe_messages = validate_final_output(missing_probe)
    _assert(
        not probe_ok and any("continue 时不得为空" in item for item in probe_messages),
        "continue without next_probe must fail",
        errors,
    )

    unknown_evidence = copy.deepcopy(valid)
    unknown_evidence["analysis_material_pack"]["chart_candidates"][0][
        "evidence_refs"
    ] = ["unknown_evidence"]
    evidence_ok, evidence_messages = validate_final_output(unknown_evidence)
    _assert(
        not evidence_ok and any("引用未知 id" in item for item in evidence_messages),
        "unknown evidence ref must fail",
        errors,
    )

    missing_review = copy.deepcopy(valid)
    missing_review["analysis_material_pack"]["claim_review_log"]["entries"] = [
        entry
        for entry in missing_review["analysis_material_pack"]["claim_review_log"]["entries"]
        if entry["finding_id"] != "finding_furniture_decline"
    ]
    review_ok, review_messages = validate_final_output(missing_review)
    _assert(
        not review_ok and any("缺少 finding 审查" in item for item in review_messages),
        "every validated finding must have a claim review",
        errors,
    )

    weak_review = copy.deepcopy(valid)
    weak_review["analysis_material_pack"]["claim_review_log"]["entries"][0][
        "checks"
    ]["decision_direction_clear"] = False
    weak_ok, weak_messages = validate_final_output(weak_review)
    _assert(
        not weak_ok and any("decision_direction_clear 必须通过" in item for item in weak_messages),
        "a failed decision-direction review must block handoff",
        errors,
    )

    unbound_chart = copy.deepcopy(valid)
    unbound_chart["analysis_material_pack"]["chart_candidates"][0][
        "finding_refs"
    ] = ["unknown_finding"]
    chart_ok, chart_messages = validate_final_output(unbound_chart)
    _assert(
        not chart_ok and any("finding_refs" in item and "引用未知 id" in item for item in chart_messages),
        "chart candidates must bind known findings",
        errors,
    )

    if errors:
        print("MATERIAL_PACK_TESTS_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "MATERIAL_PACK_TESTS_PASS: v0.3 positive, v0.2/legacy compatibility, "
        "and 6 negative gates"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
