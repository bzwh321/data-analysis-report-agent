#!/usr/bin/env python3
"""Validate report assembly pack v0.1 before HTML rendering."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


VERSION = "0.1"
RELATIONS = {"same_claim", "supporting", "complementary", "boundary", "mismatch", "insufficient"}
READY_RELATIONS = {"same_claim", "supporting", "complementary", "boundary"}
STATUSES = {"ready", "return_to_analysis", "return_to_text_agent", "return_to_chart_agent", "drop_or_bounded"}
ROUTES = {"analysis", "text_agent", "chart_agent", "drop_or_bounded", None}
LAYOUTS = {"prose_then_chart", "chart_then_notes", "text_chart_columns", "table_first", "text_only"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list(value: Any, *, allow_empty: bool = False) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value))


def validate_report_assembly_pack(payload: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    pack = payload.get("assembly_pack") if "assembly_pack" in payload else payload
    if not isinstance(pack, dict):
        return False, ["assembly_pack must be an object"]
    if pack.get("contract_version") != VERSION:
        errors.append(f"assembly_pack.contract_version must be {VERSION}")
    runtime = pack.get("runtime_policy")
    if not isinstance(runtime, dict):
        errors.append("runtime_policy must be an object")
    else:
        if runtime.get("manifest_ref") != "agents/report-assembler/manifest.yaml":
            errors.append("runtime_policy.manifest_ref must point to report-assembler")
        if runtime.get("configured_temperature") != 0.0 or runtime.get("applied_temperature") != 0.0:
            errors.append("report-assembler temperature must be configured and applied as 0.0")

    sections = pack.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty list")
        sections = []
    section_ids: set[str] = set()
    for index, section in enumerate(sections):
        path = f"sections[{index}]"
        if not isinstance(section, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("section_id", "order", "text_refs", "chart_refs", "layout", "relationship", "render_status"):
            if field not in section:
                errors.append(f"{path}.{field} is required")
        section_id = section.get("section_id")
        if not _text(section_id):
            errors.append(f"{path}.section_id must be non-empty")
        elif section_id in section_ids:
            errors.append(f"{path}.section_id duplicated: {section_id}")
        else:
            section_ids.add(section_id)
        if not isinstance(section.get("order"), int) or section.get("order") < 1:
            errors.append(f"{path}.order must be a positive integer")
        if not isinstance(section.get("text_refs"), dict) or not section.get("text_refs"):
            errors.append(f"{path}.text_refs must be a non-empty object")
        if not _list(section.get("chart_refs"), allow_empty=section.get("layout") == "text_only"):
            errors.append(f"{path}.chart_refs must be non-empty unless layout=text_only")
        if section.get("layout") not in LAYOUTS:
            errors.append(f"{path}.layout is unsupported")
        if section.get("relationship") not in READY_RELATIONS:
            errors.append(f"{path}.relationship must be ready relation, not mismatch or insufficient")
        if section.get("render_status") != "ready":
            errors.append(f"{path}.render_status must be ready")

    opinions = pack.get("assembly_opinions")
    if not isinstance(opinions, list) or len(opinions) != len(sections):
        errors.append("assembly_opinions must exist once per section")
        opinions = []
    opinion_ids: set[str] = set()
    for index, opinion in enumerate(opinions):
        path = f"assembly_opinions[{index}]"
        if not isinstance(opinion, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("section_id", "text_status", "chart_status", "text_chart_relation", "assembly_status", "route", "reason", "backfill_requests"):
            if field not in opinion:
                errors.append(f"{path}.{field} is required")
        section_id = opinion.get("section_id")
        if _text(section_id):
            opinion_ids.add(section_id)
        if opinion.get("text_status") != "pass":
            errors.append(f"{path}.text_status must be pass before rendering")
        if opinion.get("chart_status") != "pass":
            errors.append(f"{path}.chart_status must be pass before rendering")
        relation = opinion.get("text_chart_relation")
        if relation not in RELATIONS:
            errors.append(f"{path}.text_chart_relation is unsupported")
        status = opinion.get("assembly_status")
        if status not in STATUSES:
            errors.append(f"{path}.assembly_status is unsupported")
        if opinion.get("route") not in ROUTES:
            errors.append(f"{path}.route is unsupported")
        if status == "ready":
            if relation not in READY_RELATIONS:
                errors.append(f"{path}.ready cannot use mismatch or insufficient relation")
            if opinion.get("route") is not None:
                errors.append(f"{path}.route must be null when ready")
            if opinion.get("backfill_requests") != []:
                errors.append(f"{path}.backfill_requests must be empty when ready")
        else:
            if opinion.get("route") is None:
                errors.append(f"{path}.route is required when not ready")
        if not _text(opinion.get("reason")):
            errors.append(f"{path}.reason must be non-empty")
        if not isinstance(opinion.get("backfill_requests"), list):
            errors.append(f"{path}.backfill_requests must be a list")
    if opinion_ids != section_ids:
        errors.append("assembly_opinions section_id set must match sections")

    if not isinstance(pack.get("bounded_modules"), list):
        errors.append("bounded_modules must be a list")
    if not isinstance(pack.get("renderer_handoff"), dict) or not pack.get("renderer_handoff"):
        errors.append("renderer_handoff must be a non-empty object")
    return not errors, errors


if __name__ == "__main__":
    target = Path(sys.argv[1])
    data = json.loads(target.read_text(encoding="utf-8"))
    ok, messages = validate_report_assembly_pack(data)
    print("PASS" if ok else "FAIL")
    for message in messages:
        print(f"- {message}")
    sys.exit(0 if ok else 1)
